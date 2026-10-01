"""Responde un ítem del banco: recuperar → construir prompt → generar.

El post-filtro de citas (T17) y la abstención (T18) se aplican sobre el
resultado de `responder`.
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass

from src.oficial import citations
from src.config import Config, config
from src.generation.contexto import MAX_TOKENS, esquema, esquema_mc_abierta, mensajes
from src.generation.llm import LLM, Generacion
from src.retrieval.hibrido import Pasaje, Recuperador


@dataclass
class Resultado:
    item: dict
    pasajes: list[Pasaje]
    generacion: Generacion
    datos: dict | None
    extra: dict = dataclasses.field(default_factory=dict)


# Palabras que plantean la pregunta pero no dicen de qué trata (se suman a las vacías de BM25).
_VACIAS_PREGUNTA = frozenset("""
caso casos siguiente siguientes correcta correcto correctas opcion opciones afirmacion
respecto acuerdo puede pueden debe deben deberia corresponde senale indique cierto cierta
falso falsa verdadero verdadera mismo misma dicho dicha cada sido esta estan seria
pregunta preguntas responda responder lea leer lectura atencion habiendo enunciado anterior
anteriores juridica
""".split())


def palabras_clave(pregunta: str, n: int, frecuencia=None) -> list[str]:
    """Hasta `n` palabras con contenido de la pregunta, sin repetir y en su orden original.

    Se descartan las palabras vacías (las de BM25 y las que solo plantean la pregunta) y las
    de menos de 3 letras; los números (artículos, años) se conservan. Con `frecuencia`
    (palabra → n.º de fragmentos que la contienen, ver `IndiceBM25.frecuencia`) se eligen
    las más raras del corpus, que son las que distinguen el tema: en una pregunta larga, el
    preámbulo ("Habiendo hecho la lectura previa…") no desplaza a "consulta previa" o
    "relleno sanitario". Las palabras ausentes del corpus van al final (BM25 no las usa).
    Sin `frecuencia`, las primeras `n`.
    """
    from src.index.lexico import STOPWORDS

    vistas: set[str] = set()
    candidatas: list[str] = []
    for palabra in re.findall(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+(?:-\d+)?", pregunta):
        normal = citations.norm(palabra)
        if normal in vistas or normal in STOPWORDS or normal in _VACIAS_PREGUNTA:
            continue
        if not palabra.isdigit() and len(normal) < 3:
            continue
        vistas.add(normal)
        candidatas.append(palabra)
    if frecuencia is None or len(candidatas) <= n:
        return candidatas[:n]
    df = {i: frecuencia(w) for i, w in enumerate(candidatas)}
    utiles = [i for i in df if df[i] is not None]
    orden = sorted(utiles, key=lambda i: (df[i] == 0, df[i], i))[:n]
    return [candidatas[i] for i in sorted(orden)]


def consulta_opcion(pregunta: str, opcion: str, cfg: Config = config, frecuencia=None) -> str:
    """Consulta con la que se busca la evidencia de una opción de selección múltiple.

    "pregunta" (C-03): la pregunta completa más la opción; en preguntas largas la pregunta
    domina y la opción casi no pesa (caso 748: «falsa motivación» no trajo el art. 137 del
    CPACA). "clave" (C-07): primero el texto de la opción y luego pocas palabras clave de la
    pregunta, para que BM25 y el encoder busquen lo que distingue a esa opción sin perder el
    tema ("2 meses" solo no dice nada).
    """
    pregunta, opcion = pregunta.strip(), str(opcion).strip()
    if cfg.mc_consulta_opcion == "pregunta":
        return f"{pregunta} {opcion}"
    return " ".join([opcion, *palabras_clave(pregunta, cfg.mc_palabras_clave, frecuencia)])


def consultas_extra(item: dict, cfg: Config = config, frecuencia=None) -> list[str]:
    """En MC, las consultas de cada opción (ver `consulta_opcion`)."""
    if item.get("formato") != "multiple_choice":
        return []
    pregunta = item.get("pregunta") or ""
    return [consulta_opcion(pregunta, v, cfg, frecuencia)
            for _, v in sorted((item.get("opciones") or {}).items()) if str(v).strip()]


def recuperar(item: dict, rec: Recuperador, cfg: Config = config) -> list[Pasaje]:
    if item.get("formato") == "multiple_choice" and item.get("opciones"):
        return recuperar_mc(item, rec, cfg)
    return rec.buscar(item["pregunta"], area=item.get("area"), k=cfg.top_k_pasajes)


def recuperar_mc(item: dict, rec: Recuperador, cfg: Config = config) -> list[Pasaje]:
    """Evidencia representativa por opción (selección múltiple).

    `PUESTOS_PREGUNTA` puestos para lo mejor de la pregunta y el resto repartido por turnos
    entre las opciones: en cada ronda entra el mejor pasaje aún no incluido de cada opción
    (buscando con `consulta_opcion`). Así cada alternativa tiene evidencia propia que la
    respalde o la contradiga, en lugar de competir todas por los mismos 10 puestos. Cada
    pasaje de opción queda marcado con su letra (`meta["opcion"]`) para el prompt.
    Respeta el tope por documento (C-02), salvo documentos mencionados en la pregunta.
    """
    k = cfg.top_k_pasajes
    pregunta = (item.get("pregunta") or "").strip()
    base = rec.buscar(pregunta, area=item.get("area"), k=k)
    por_opcion = {
        letra: rec.buscar(consulta_opcion(pregunta, texto, cfg, rec.bm25.frecuencia),
                          area=item.get("area"),
                          k=cfg.pasajes_por_opcion + 2, n_rerank=cfg.rerank_candidatos_opcion)
        for letra, texto in sorted(item["opciones"].items()) if str(texto).strip()}
    _, mencionados = rec.router(pregunta)

    elegidos: list[Pasaje] = []
    vistos: set[str] = set()
    por_doc: dict[str, int] = {}
    n_complementarios = [0]

    def admitir(p: Pasaje) -> bool:
        if p.chunk_id in vistos:
            return False
        mencionado = "router" in (p.origen or []) or bool(mencionados & rec.cuerpo_doc[p.id])
        if cfg.max_por_documento and not mencionado and por_doc.get(p.doc_id, 0) >= cfg.max_por_documento:
            return False
        complementario = p.doc_id in rec.complementarios and not mencionado
        if complementario and cfg.max_complementarios and n_complementarios[0] >= cfg.max_complementarios:
            return False
        n_complementarios[0] += complementario
        vistos.add(p.chunk_id)
        por_doc[p.doc_id] = por_doc.get(p.doc_id, 0) + 1
        elegidos.append(p)
        return True

    for p in base:
        if len(elegidos) >= min(cfg.puestos_pregunta, k):
            break
        admitir(p)
    for ronda in range(cfg.pasajes_por_opcion + 2):
        for letra, candidatos in por_opcion.items():
            if len(elegidos) >= k:
                break
            for p in candidatos:
                if p.chunk_id not in vistos and admitir(p):
                    p.meta = {**(p.meta or {}), "opcion": letra}
                    break
    for p in base:                     # si sobran puestos, se completan con la pregunta
        if len(elegidos) >= k:
            break
        admitir(p)
    return elegidos


def mensajes_que_caben(item: dict, pasajes, llm: LLM, cfg: Config = config,
                       etapa: str | None = None, max_tokens: int | None = None,
                       respuesta_abierta: str = "") -> tuple[list[dict], int]:
    """Mensajes con tantos pasajes como quepan en la ventana de contexto.

    Quita pasajes del final (los menos pertinentes) hasta que prompt + salida
    quepan. Determinista. Devuelve también cuántos pasajes leyó el modelo.
    """
    maximo = llm.n_ctx - (max_tokens or MAX_TOKENS[item["formato"]]) - 32
    n = min(cfg.pasajes_prompt, len(pasajes))
    while True:
        msgs = mensajes(item, pasajes, dataclasses.replace(cfg, pasajes_prompt=n), etapa=etapa,
                        respuesta_abierta=respuesta_abierta)
        if n == 0 or llm.contar_tokens(msgs) <= maximo:
            return msgs, n
        n -= 1


def opcion_por_similitud(item: dict, respuesta: str, encoder) -> str | None:
    """Letra cuya opción se parece más (coseno con el encoder) a la respuesta abierta.

    Solo diagnóstico (C-08): se guarda en la traza para comparar "elegir por similitud"
    con la elección del modelo sin otra corrida. Falla en opciones como "(a) y (b)" o
    "Ninguna de las anteriores", por eso no decide.
    """
    letras = [l for l in sorted(item.get("opciones") or {}) if str(item["opciones"][l]).strip()]
    if not respuesta.strip() or not letras or encoder is None:
        return None
    import numpy as np

    v = np.asarray(encoder.codificar([respuesta] + [str(item["opciones"][l]) for l in letras],
                                     es_consulta=False), dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    sims = v[1:] @ v[0]
    return letras[int(np.argmax(sims))]


def generar_respuesta(item: dict, pasajes, llm: LLM, cfg: Config = config,
                      usar_cache: bool = True, encoder=None) -> tuple[Generacion, int, dict]:
    """Genera la salida del decoder para el ítem. Devuelve (generación, pasajes leídos, extra).

    En selección múltiple con `MC_MODO=abierta` (C-08) son dos llamadas: (1) el modelo
    responde la pregunta sin ver las opciones (evidencia sin marcas de opción); (2) con su
    respuesta preliminar, la evidencia y las opciones, elige la letra (esquema de "elegir
    primero"). La generación devuelta es la del paso 2, con tiempos y tokens sumados; `extra`
    lleva la respuesta abierta y la opción más parecida según el encoder (diagnóstico).
    """
    mc_abierta = item["formato"] == "multiple_choice" and cfg.mc_modo == "abierta"
    if not mc_abierta:
        # Selección múltiple con razonamiento (C-09): Qwen3 piensa antes de escribir el JSON;
        # se reserva su tope de tokens al decidir cuántos pasajes caben.
        pensar = cfg.mc_razonamiento_tokens if item["formato"] == "multiple_choice" else 0
        msgs, n = mensajes_que_caben(item, pasajes, llm, cfg,
                                     max_tokens=MAX_TOKENS[item["formato"]] + pensar)
        g = llm.generar(msgs, esquema=esquema(item, cfg), max_tokens=MAX_TOKENS[item["formato"]],
                        usar_cache=usar_cache, razonamiento_tokens=pensar)
        return g, n, ({"razonamiento": g.razonamiento} if pensar else {})

    msgs1, _ = mensajes_que_caben(item, pasajes, llm, cfg, etapa="abierta",
                                  max_tokens=MAX_TOKENS["mc_abierta"])
    g1 = llm.generar(msgs1, esquema=esquema_mc_abierta(), max_tokens=MAX_TOKENS["mc_abierta"],
                     usar_cache=usar_cache)
    abierta = str((g1.datos or {}).get("respuesta") or "").strip()
    msgs2, n = mensajes_que_caben(item, pasajes, llm, cfg, etapa="desde_abierta",
                                  respuesta_abierta=abierta)
    g2 = llm.generar(msgs2, esquema=esquema(item, cfg), max_tokens=MAX_TOKENS[item["formato"]],
                     usar_cache=usar_cache)
    suma = lambda a, b: (a or 0) + (b or 0) if a is not None or b is not None else None
    g = dataclasses.replace(g2, segundos=g1.segundos + g2.segundos,
                            tokens_prompt=suma(g1.tokens_prompt, g2.tokens_prompt),
                            tokens_salida=suma(g1.tokens_salida, g2.tokens_salida),
                            desde_cache=g1.desde_cache and g2.desde_cache,
                            truncada=g1.truncada or g2.truncada)
    extra = {"mc_modo": "abierta", "respuesta_abierta": abierta,
             "abierta_json_valido": g1.datos is not None,
             "opcion_por_similitud": opcion_por_similitud(item, abierta, encoder)}
    return g, n, extra


def responder(item: dict, rec: Recuperador, llm: LLM, cfg: Config = config,
              usar_cache: bool = True) -> Resultado:
    pasajes = recuperar(item, rec, cfg)
    g, _, extra = generar_respuesta(item, pasajes, llm, cfg, usar_cache,
                                    encoder=getattr(rec, "encoder", None))
    return Resultado(item=item, pasajes=pasajes, generacion=g, datos=g.datos, extra=extra)
