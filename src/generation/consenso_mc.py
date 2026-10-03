"""Fusión de rangos entre consultas; nunca suma scores de pertinencia distintos."""
from dataclasses import replace
import math


def reordenar(por_opcion, pool, puntos):
    if len(pool) != len(puntos) or len({p.chunk_id for p in pool}) != len(pool):
        raise ValueError("El pool y sus puntuaciones deben corresponder sin duplicados.")
    scores = {p.chunk_id: float(s) for p, s in zip(pool, puntos)}
    if not all(math.isfinite(s) for s in scores.values()):
        raise ValueError("Puntuaciones de reranking no finitas.")
    orden = sorted(scores, key=lambda cid: (-round(scores[cid], 5), cid))
    rangos = {cid: i for i, cid in enumerate(orden, 1)}
    salida = {}
    for letra, candidatos in sorted(por_opcion.items()):
        locales = {p.chunk_id: i for i, p in enumerate(candidatos, 1)}
        if not set(locales) <= set(rangos):
            raise ValueError("Candidato ausente del pool de reranking.")
        fusion = {cid: 1 / (60 + local) + 1 / (60 + rangos[cid])
                  for cid, local in locales.items()}
        salida[letra] = [replace(p, meta={**p.meta,
                                        "rango_consenso": rangos[p.chunk_id],
                                        "score_consenso": scores[p.chunk_id],
                                        "rrf_consenso": fusion[p.chunk_id]})
                         for p in sorted(candidatos,
                                         key=lambda p: (-fusion[p.chunk_id], p.chunk_id))]
    return salida
