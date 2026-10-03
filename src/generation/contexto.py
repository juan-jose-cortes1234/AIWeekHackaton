"""Construcción de los mensajes para el decoder y del JSON schema de cada formato.

- La evidencia se numera `[P1]…[Pn]` en el orden del recuperador; cada pasaje
  conserva su encabezado canónico. Por defecto va completa; `PALABRAS_POR_PASAJE`
  > 0 recorta el cuerpo solo para acelerar pruebas en CPU.
- Los esquemas fuerzan exactamente las claves del evaluador más `pasajes_usados`,
  que se usa internamente para renderizar las citas y no va en la entrega.
- Sin `maxLength`: llama.cpp lo convierte en una gramática con un nivel anidado
  por carácter y falla. La longitud se controla con `MAX_TOKENS` y el post-proceso.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from src.config import Config, config

DIR_PROMPTS = Path(__file__).resolve().parent / "prompts"
MAX_TOKENS = {"multiple_choice": 500, "semi_open": 400, "open_ended": 1400,
              "mc_abierta": 350}   # paso 1 de MC en modo "abierta" (C-08)
LETRAS = ("A", "B", "C", "D")


@lru_cache(maxsize=None)
def plantilla(nombre: str) -> str:
    return (DIR_PROMPTS / f"{nombre}.txt").read_text(encoding="utf-8").strip()


def recortar(texto: str, max_palabras: int) -> str:
    """Conserva el encabezado (primera línea) y recorta el cuerpo a `max_palabras`.

    `max_palabras <= 0` deja el pasaje completo (flujo final, decisión del equipo:
    en GPU no hace falta sacrificar contexto). El recorte es solo una perilla de
    velocidad para pruebas en CPU (medido: 158 s completos vs. 102 s a 180 palabras).
    """
    if max_palabras <= 0:
        return texto
    cabeza, _, cuerpo = texto.partition("\n")
    palabras = cuerpo.split()
    if len(palabras) <= max_palabras:
        return texto
    return f"{cabeza}\n{' '.join(palabras[:max_palabras])} […]"


def evidencia(pasajes, cfg: Config = config, marcas: bool = True,
              numeros_pasajes: list[int] | None = None) -> str:
    partes = []
    numeros = numeros_pasajes if numeros_pasajes is not None else list(range(1, len(pasajes) + 1))
    if len(numeros) != len(pasajes) or len(set(numeros)) != len(numeros):
        raise ValueError("La numeración debe corresponder a cada pasaje sin duplicados.")
    for n, p in list(zip(numeros, pasajes))[:cfg.pasajes_prompt]:
        meta = getattr(p, "meta", None) or {}
        opciones = meta.get("opciones") or ([meta["opcion"]] if meta.get("opcion") else [])
        opcion = ", ".join(opciones) if marcas else None
        marca = f"(recuperado para la opción {opcion}) " if opcion else ""
        partes.append(f"[P{n}] {marca}{recortar(p.texto, cfg.palabras_por_pasaje)}")
    return "\n\n".join(partes)


def letras_de(item: dict) -> list[str]:
    return [l for l in LETRAS if l in (item.get("opciones") or {})]


def plantilla_de(item: dict, cfg: Config = config) -> str:
    """Nombre de la plantilla del prompt para el formato del ítem."""
    if item["formato"] == "multiple_choice" and not cfg.mc_analisis_previo:
        return "multiple_choice_precisa" if cfg.mc_prompt_preciso else "multiple_choice_elegir"
    return item["formato"]


def esquema(item: dict, cfg: Config = config, numeros_pasajes: list[int] | None = None) -> dict:
    """JSON schema de la salida del decoder para el formato del ítem."""
    usados = {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 20},
              "maxItems": 10}
    if numeros_pasajes is not None:
        usados = {"type": "array", "maxItems": min(10, len(numeros_pasajes)),
                  "items": {"type": "integer", "enum": numeros_pasajes or [1]}}
    f = item["formato"]
    if f == "multiple_choice" and (not cfg.mc_analisis_previo or cfg.mc_modo == "abierta"):
        letras = letras_de(item) or list(LETRAS)
        # Elegir primero (C-06): la letra, la justificación y luego un descarte por cada otra
        # opción; las marcas de procedencia son opcionales (C-21).
        return {
            "type": "object",
            "properties": {
                "respuesta_correcta": {"type": "string", "enum": letras},
                "justificacion": {"type": "string"},
                "descarte_opciones": {
                    "type": "object",
                    "properties": {l: {"type": "string"} for l in letras},
                },
                "pasajes_usados": usados,
            },
            "required": ["respuesta_correcta", "justificacion", "descarte_opciones",
                         "pasajes_usados"],
        }
    if f == "multiple_choice":
        letras = letras_de(item) or list(LETRAS)
        return {
            "type": "object",
            # Orden deliberado: primero el análisis de cada opción y después la letra (la
            # gramática sigue este orden, así el modelo "razona" antes de elegir). Los
            # descartes de la entrega se derivan de este análisis (citas.postprocesar).
            "properties": {
                "analisis_opciones": {
                    "type": "object",
                    "properties": {l: {"type": "string"} for l in letras},
                    "required": letras,
                },
                "respuesta_correcta": {"type": "string", "enum": letras},
                "justificacion": {"type": "string"},
                "pasajes_usados": usados,
            },
            "required": ["analisis_opciones", "respuesta_correcta", "justificacion",
                         "pasajes_usados"],
        }
    if f == "semi_open":
        return {
            "type": "object",
            "properties": {
                "respuesta": {"type": "string"},
                "palabras_clave": {"type": "array", "items": {"type": "string"},
                                   "minItems": 3, "maxItems": 6},
                "referencia_legal": {"type": "string"},
                "pasajes_usados": usados,
            },
            "required": ["respuesta", "palabras_clave", "referencia_legal", "pasajes_usados"],
        }
    return {
        "type": "object",
        "properties": {
            "marco_normativo": {"type": "string"},
            "analisis": {"type": "string"},
            "jurisprudencia": {"type": "string"},
            "conclusion": {"type": "string"},
            "pasajes_usados": usados,
        },
        "required": ["marco_normativo", "analisis", "jurisprudencia", "conclusion",
                     "pasajes_usados"],
    }


def esquema_mc_abierta(numeros_pasajes: list[int] | None = None) -> dict:
    """Paso 1 de MC en modo "abierta" (C-08): respuesta libre, sin opciones."""
    resultado = {
        "type": "object",
        "properties": {
            "respuesta": {"type": "string"},
            "pasajes_usados": {"type": "array", "items": {"type": "integer", "minimum": 1,
                                                          "maximum": 20}, "maxItems": 10},
        },
        "required": ["respuesta", "pasajes_usados"],
    }
    if numeros_pasajes is not None:
        resultado["properties"]["pasajes_usados"] = {
            "type": "array", "maxItems": min(10, len(numeros_pasajes)),
            "items": {"type": "integer", "enum": numeros_pasajes or [1]}}
    return resultado


def mensajes(item: dict, pasajes, cfg: Config = config, etapa: str | None = None,
             respuesta_abierta: str = "", numeros_pasajes: list[int] | None = None) -> list[dict]:
    """Mensajes system + user para un ítem del banco y sus pasajes recuperados.

    `etapa` solo aplica a MC en modo "abierta" (C-08): "abierta" = paso 1 (la pregunta sin
    opciones y la evidencia sin marcas de opción); "desde_abierta" = paso 2 (opciones y la
    respuesta preliminar del paso 1).
    """
    f = item["formato"]
    campos = {
        "area": item.get("area") or "no indicada",
        "sub_tarea": item.get("sub_tarea") or "no indicada",
        "evidencia": evidencia(pasajes, cfg, marcas=etapa != "abierta"
                               and (f != "multiple_choice" or cfg.mc_marcas_evidencia),
                               numeros_pasajes=numeros_pasajes)
                     or "(no se recuperó evidencia)",
        "pregunta": (item.get("pregunta") or "").strip(),
    }
    if f == "multiple_choice":
        letras = letras_de(item)
        campos["opciones"] = "\n".join(f"{l}) {str(item['opciones'][l]).strip()}" for l in letras)
        campos["letras_descarte"] = ", ".join(letras)
        campos["respuesta_abierta"] = respuesta_abierta.strip() or "(sin respuesta preliminar)"
    nombre = {"abierta": "multiple_choice_abierta",
              "desde_abierta": "multiple_choice_desde_abierta",
              "contraste": "multiple_choice_contraste",
              "revision": "multiple_choice_revision"}.get(etapa) or plantilla_de(item, cfg)
    usuario = plantilla(nombre).format(**campos)
    return [{"role": "system", "content": plantilla("sistema")},
            {"role": "user", "content": usuario}]
