"""Auditorías independientes con citas comprobadas, seguidas de una selección.

La comprobación literal garantiza presencia en el contexto, no implicación lógica.
No modifica el recuperador, el corpus ni la salida oficial del evaluador.
"""
from __future__ import annotations

from dataclasses import replace
import json
import time
import unicodedata

from jsonschema import Draft202012Validator

from src.generation.contexto import evidencia, esquema, letras_de, plantilla, recortar
from src.generation.revision_mc import agregar_usos

ESTADOS = ("respaldada", "contradicha", "evidencia_insuficiente")
TOKENS_AUDITORIA = 280
TOKENS_SELECCION = 500
RESERVA_INFORMES = 4 * TOKENS_AUDITORIA + 160


def normalizar(texto):
    """Solo equivalencias Unicode y espacio; conserva negaciones y puntuación."""
    return " ".join(unicodedata.normalize("NFC", texto).split())


def esquema_auditoria(indices):
    return {"type": "object", "additionalProperties": False,
            "properties": {
                "citas": {"type": "array", "maxItems": 2, "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"pasaje": {"type": "integer", "enum": indices or [1]},
                                   "texto": {"type": "string"}},
                    "required": ["pasaje", "texto"]}},
                "explicacion": {"type": "string"},
                "estado": {"type": "string", "enum": list(ESTADOS)}},
            "required": ["citas", "explicacion", "estado"]}


def comprobar_auditoria(datos, pasajes, indices, cfg):
    """Descarta citas no visibles o alteradas y degrada las conclusiones inseguras."""
    valido = Draft202012Validator(esquema_auditoria(indices)).is_valid(datos)
    citas, rechazadas = [], []
    if not valido:
        return {"estado": "evidencia_insuficiente", "citas": [],
                "citas_rechazadas": [], "json_valido": False, "degradada": True}
    for cita in datos["citas"]:
        n, texto = cita["pasaje"], normalizar(cita["texto"])
        motivo = None
        if type(n) is not int or n not in indices or not 1 <= n <= len(pasajes):
            motivo = "pasaje_no_visible"
        elif not texto:
            motivo = "cita_vacia"
        elif texto not in normalizar(pasajes[n - 1].texto):
            motivo = "cita_no_literal"
        elif texto not in normalizar(recortar(pasajes[n - 1].texto, cfg.palabras_por_pasaje)):
            motivo = "texto_no_visible"
        if motivo:
            rechazadas.append({"cita": cita, "motivo": motivo})
        else:
            p = pasajes[n - 1]
            citas.append({"pasaje": n, "texto": cita["texto"],
                          "chunk_id": p.chunk_id, "doc_id": p.doc_id})
    degradada = bool(rechazadas) or (datos["estado"] != "evidencia_insuficiente" and not citas)
    return {"estado": "evidencia_insuficiente" if degradada else datos["estado"],
            "citas": citas, "citas_rechazadas": rechazadas,
            "json_valido": True, "degradada": degradada}


def informes_validados(auditorias, compacto=False):
    """El selector no recibe explicaciones ni citas que no superaron la comprobación."""
    return {letra: {"estado": a["estado"], "citas": [
        {"pasaje": c["pasaje"], **({} if compacto else {"texto": c["texto"]})}
        for c in a["citas"]]} for letra, a in auditorias.items()}


def mensajes_etapa(item, pasajes, indices, cfg, opcion=None, informes=None):
    opciones = "\n".join(f"{l}: {item['opciones'][l]}" for l in letras_de(item))
    texto = (f"Área: {item.get('area', '')}\nSubtarea: {item.get('sub_tarea', '')}\n"
             f"Pregunta:\n{item['pregunta']}\n\nAlternativas:\n{opciones}\n\n"
             f"Pasajes:\n{evidencia([pasajes[n - 1] for n in indices], cfg, marcas=False, numeros_pasajes=indices)}")
    if opcion is not None:
        nombre = "multiple_choice_verificar"
        texto += f"\n\nAlternativa que debes evaluar: {opcion}"
    else:
        nombre = "multiple_choice_decidir_verificacion"
        texto += "\n\nInformes comprobados:\n" + json.dumps(informes or {}, ensure_ascii=False)
    return [{"role": "system", "content": plantilla(nombre)}, {"role": "user", "content": texto}]


def contexto_comun(item, pasajes, llm, cfg):
    """Todas las etapas ven los mismos pasajes; reserva espacio para los informes."""
    indices = list(range(1, min(len(pasajes), cfg.pasajes_prompt, 10) + 1))
    while True:
        auditorias = [mensajes_etapa(item, pasajes, indices, cfg, opcion=l) for l in letras_de(item)]
        selector = mensajes_etapa(item, pasajes, indices, cfg, informes={})
        if (all(llm.contar_tokens(m) + TOKENS_AUDITORIA + 32 <= llm.n_ctx for m in auditorias)
                and llm.contar_tokens(selector) + RESERVA_INFORMES + TOKENS_SELECCION + 32 <= llm.n_ctx):
            return indices
        if not indices:
            raise ValueError("Pregunta e informes de verificación exceden la ventana del decoder.")
        indices.pop()


def verificar(item, pasajes, llm, cfg, usar_cache=True):
    indices = contexto_comun(item, pasajes, llm, cfg)
    auditorias, generaciones = {}, []
    for letra in letras_de(item):
        inicio = time.perf_counter()
        try:
            g = llm.generar(mensajes_etapa(item, pasajes, indices, cfg, opcion=letra),
                            esquema=esquema_auditoria(indices), max_tokens=TOKENS_AUDITORIA,
                            usar_cache=usar_cache)
            generaciones.append(g)
            a = comprobar_auditoria(g.datos, pasajes, indices, cfg)
            a.update(datos_originales=g.datos, truncada=g.truncada,
                     tokens_prompt=g.tokens_prompt, tokens_salida=g.tokens_salida,
                     segundos=g.segundos, desde_cache=g.desde_cache)
            a["error_etapa"] = bool(g.truncada or not a["json_valido"])
            if a["error_etapa"]:
                a.update(estado="evidencia_insuficiente", citas=[])
        except Exception as exc:
            a = {"estado": "evidencia_insuficiente", "citas": [], "citas_rechazadas": [],
                 "error_etapa": True, "excepcion": f"{type(exc).__name__}: {exc}",
                 "segundos": time.perf_counter() - inicio}
        auditorias[letra] = a
    msgs = mensajes_etapa(item, pasajes, indices, cfg, informes=informes_validados(auditorias))
    compacto = llm.contar_tokens(msgs) + TOKENS_SELECCION + 32 > llm.n_ctx
    if compacto:
        msgs = mensajes_etapa(item, pasajes, indices, cfg, informes=informes_validados(auditorias, True))
    if llm.contar_tokens(msgs) + TOKENS_SELECCION + 32 > llm.n_ctx:
        raise ValueError("Los informes de verificación exceden el contexto común.")
    e = esquema(item, cfg, numeros_pasajes=indices)
    final = llm.generar(msgs, esquema=e, max_tokens=TOKENS_SELECCION, usar_cache=usar_cache)
    generaciones.append(final)
    if final.truncada or not Draft202012Validator(e).is_valid(final.datos):
        final = replace(final, datos=None)
    extra = {"mc_modo": "verificacion", "indices_pasajes_leidos": indices,
             "chunk_ids_leidos": [pasajes[n - 1].chunk_id for n in indices],
             "verificacion_auditorias": auditorias,
             "verificacion_incompleta": any(a["error_etapa"] for a in auditorias.values()),
             "verificacion_informes": "referencias" if compacto else "completo"}
    return agregar_usos(final, generaciones), len(indices), extra
