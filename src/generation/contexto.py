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
MAX_TOKENS = {"multiple_choice": 450, "semi_open": 400, "open_ended": 900}
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


def evidencia(pasajes, cfg: Config = config) -> str:
    return "\n\n".join(f"[P{n}] {recortar(p.texto, cfg.palabras_por_pasaje)}"
                       for n, p in enumerate(pasajes[:cfg.pasajes_prompt], start=1))


def letras_de(item: dict) -> list[str]:
    return [l for l in LETRAS if l in (item.get("opciones") or {})]


def esquema(item: dict) -> dict:
    """JSON schema de la salida del decoder para el formato del ítem."""
    usados = {"type": "array", "items": {"type": "integer", "minimum": 1, "maximum": 20},
              "maxItems": 10}
    f = item["formato"]
    if f == "multiple_choice":
        letras = letras_de(item) or list(LETRAS)
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


def mensajes(item: dict, pasajes, cfg: Config = config) -> list[dict]:
    """Mensajes system + user para un ítem del banco y sus pasajes recuperados."""
    f = item["formato"]
    campos = {
        "area": item.get("area") or "no indicada",
        "sub_tarea": item.get("sub_tarea") or "no indicada",
        "evidencia": evidencia(pasajes, cfg) or "(no se recuperó evidencia)",
        "pregunta": (item.get("pregunta") or "").strip(),
    }
    if f == "multiple_choice":
        letras = letras_de(item)
        campos["opciones"] = "\n".join(f"{l}) {str(item['opciones'][l]).strip()}" for l in letras)
        campos["letras_descarte"] = ", ".join(letras)
    usuario = plantilla(f).format(**campos)
    return [{"role": "system", "content": plantilla("sistema")},
            {"role": "user", "content": usuario}]
