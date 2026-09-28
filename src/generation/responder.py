"""Responde un ítem del banco: recuperar → construir prompt → generar.

El post-filtro de citas (T17) y la abstención (T18) se aplican sobre el
resultado de `responder`.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from src.config import Config, config
from src.generation.contexto import MAX_TOKENS, esquema, mensajes
from src.generation.llm import LLM, Generacion
from src.retrieval.hibrido import Pasaje, Recuperador


@dataclass
class Resultado:
    item: dict
    pasajes: list[Pasaje]
    generacion: Generacion
    datos: dict | None


def consultas_extra(item: dict) -> list[str]:
    """En MC, la pregunta más cada opción sirven como consultas adicionales."""
    if item.get("formato") != "multiple_choice":
        return []
    pregunta = (item.get("pregunta") or "").strip()
    return [f"{pregunta} {str(v).strip()}" for _, v in sorted((item.get("opciones") or {}).items())]


def recuperar(item: dict, rec: Recuperador, cfg: Config = config) -> list[Pasaje]:
    return rec.buscar(item["pregunta"], area=item.get("area"),
                      consultas_extra=consultas_extra(item), k=cfg.top_k_pasajes)


def mensajes_que_caben(item: dict, pasajes, llm: LLM, cfg: Config = config) -> tuple[list[dict], int]:
    """Mensajes con tantos pasajes como quepan en la ventana de contexto.

    Quita pasajes del final (los menos pertinentes) hasta que prompt + salida
    quepan. Determinista. Devuelve también cuántos pasajes leyó el modelo.
    """
    maximo = llm.n_ctx - MAX_TOKENS[item["formato"]] - 32
    n = min(cfg.pasajes_prompt, len(pasajes))
    while True:
        msgs = mensajes(item, pasajes, dataclasses.replace(cfg, pasajes_prompt=n))
        if n == 0 or llm.contar_tokens(msgs) <= maximo:
            return msgs, n
        n -= 1


def responder(item: dict, rec: Recuperador, llm: LLM, cfg: Config = config,
              usar_cache: bool = True) -> Resultado:
    pasajes = recuperar(item, rec, cfg)
    msgs, _ = mensajes_que_caben(item, pasajes, llm, cfg)
    g = llm.generar(msgs, esquema=esquema(item), max_tokens=MAX_TOKENS[item["formato"]],
                    usar_cache=usar_cache)
    return Resultado(item=item, pasajes=pasajes, generacion=g, datos=g.datos)
