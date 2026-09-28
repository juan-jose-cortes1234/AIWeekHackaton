"""Mecanismo de abstención (paso 4 del enunciado; ARQUITECTURA §7).

Con los pesos oficiales, abstenerse casi nunca conviene:
- **MC: nunca.** Responder aporta p·(20/289 + 10/N) y abstenerse 0,5·10/N; con
  cuatro opciones p ≥ 0,25 y responder siempre gana.
- **Texto libre:** abstenerse pierde RAGAS y el recall de citas; solo se hace si
  la recuperación no trajo nada pertinente (ningún pasaje por el router y la
  pertinencia máxima bajo el umbral), o si el modelo no produjo una respuesta
  utilizable.

Al abstenerse los campos de contenido quedan en "" y se conservan los pasajes
recuperados, como en el ejemplo oficial (ítem 218).
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import Config, config

CAMPOS = {
    "multiple_choice": ("respuesta_correcta", "justificacion", "descarte_opciones"),
    "semi_open": ("respuesta", "palabras_clave", "referencia_legal"),
    "open_ended": ("marco_normativo", "analisis", "jurisprudencia", "conclusion"),
}


@dataclass
class Decision:
    abstener: bool
    motivo: str
    pertinencia_max: float | None = None


def pertinencia_maxima(pasajes) -> tuple[float | None, str]:
    """Mayor pertinencia de la evidencia: reranker si existe; si no, similitud densa."""
    rr = [p.score_rerank for p in pasajes if p.score_rerank is not None]
    if rr:
        return max(rr), "rerank"
    dn = [p.score_denso for p in pasajes if p.score_denso is not None]
    return (max(dn), "denso") if dn else (None, "ninguna")


def decidir(item: dict, pasajes, campos: dict | None, cfg: Config = config) -> Decision:
    formato = item["formato"]
    maximo, fuente = pertinencia_maxima(pasajes)
    if formato == "multiple_choice":
        return Decision(False, "MC: nunca se abstiene", maximo)
    if not pasajes:
        return Decision(True, "sin pasajes recuperados", maximo)
    if not campos or not any(str(campos.get(c) or "").strip() for c in CAMPOS[formato]):
        return Decision(True, "el modelo no produjo una respuesta utilizable", maximo)
    if any("router" in (p.origen or []) for p in pasajes):
        return Decision(False, "la pregunta cita una norma presente en el corpus", maximo)
    umbral = cfg.umbral_abstencion if fuente == "rerank" else cfg.umbral_abstencion_denso
    if maximo is not None and maximo < umbral:
        return Decision(True, f"pertinencia máxima {maximo:.3f} < {umbral} ({fuente})", maximo)
    return Decision(False, "evidencia suficiente", maximo)


def registro_abstencion(item: dict, pasajes) -> dict:
    """Línea de entrega con abstención: campos vacíos y pasajes conservados."""
    vacios = {c: "" for c in CAMPOS[item["formato"]]}
    if item["formato"] == "semi_open":
        vacios["palabras_clave"] = []
    return {"id": item["id"], "formato": item["formato"], "abstencion": True, **vacios,
            "pasajes_recuperados": [p.a_entrega() for p in pasajes]}
