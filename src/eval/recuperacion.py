"""Calidad de la recuperación: `python -m src.eval.recuperacion [--preguntas data/sample_50.jsonl]`.

Por ítem con `legal_basis` citable: ¿alguno de los 10 pasajes recuperados
contiene un cuerpo normativo del fundamento de referencia (según el extractor
del evaluador)? Es la condición para poder citar bien, y la métrica que guía
la construcción del corpus. Las preguntas se usan solo para medir: nada de
ellas entra al índice.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from src.config import RAIZ, config
from src.generation.responder import recuperar
from src.oficial import AREA_SLUG, citations


def evaluar(recuperador, preguntas: list[dict], k: int | None = None) -> dict:
    k = k or config.top_k_pasajes
    detalle = []
    por_area: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # hits, n, cuerpos_ok, cuerpos
    for it in preguntas:
        ref = citations.bodies(citations.extract(it.get("legal_basis") or ""))
        if not ref:
            continue
        pasajes = recuperar(it, recuperador)[:k]
        encontrados = set()
        for p in pasajes:
            encontrados |= citations.bodies(citations.extract(p.texto))
        cubiertos = ref & encontrados
        a = por_area[it.get("area") or "sin área"]
        a[0] += bool(cubiertos)
        a[1] += 1
        a[2] += len(cubiertos)
        a[3] += len(ref)
        detalle.append({
            "id": it["id"], "formato": it.get("formato"), "area": it.get("area"),
            "acierto": bool(cubiertos),
            "ref": sorted(map(list, ref)), "cubiertos": sorted(map(list, cubiertos)),
            "faltantes": sorted(map(list, ref - encontrados)),
            "top": [p.texto.split("\n", 1)[0] for p in pasajes[:3]],
            "max_mismo_documento": max(Counter(p.doc_id for p in pasajes).values(), default=0),
        })
    n = sum(v[1] for v in por_area.values())
    hits = sum(v[0] for v in por_area.values())
    cu = sum(v[2] for v in por_area.values())
    tot = sum(v[3] for v in por_area.values())
    return {
        "k": k, "items_evaluados": n,
        "max_mismo_documento": dict(sorted(Counter(d["max_mismo_documento"] for d in detalle).items())),
        "acierto_at_k": round(hits / n, 4) if n else 0.0,
        "recall_cuerpos_at_k": round(cu / tot, 4) if tot else 0.0,
        "por_area": {a: {"items": v[1], "acierto_at_k": round(v[0] / v[1], 4),
                         "recall_cuerpos": round(v[2] / v[3], 4) if v[3] else 0.0}
                     for a, v in sorted(por_area.items())},
        "detalle": detalle,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preguntas", type=Path, default=RAIZ / "data" / "sample_50.jsonl")
    ap.add_argument("-k", type=int, default=config.top_k_pasajes)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    if not (config.index_dir / "index_manifest.json").is_file():
        print("No hay índice; corra `python -m src.corpus.build` y `python -m src.index.build`.")
        return 0
    from src.retrieval.hibrido import Recuperador

    preguntas = [json.loads(l) for l in args.preguntas.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    rep = evaluar(Recuperador.cargar(), preguntas, args.k)
    out = args.out or RAIZ / "runs" / f"{datetime.now():%Y%m%d_%H%M}_recuperacion" / "reporte.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"acierto@{rep['k']}: {rep['acierto_at_k']:.1%} · recall de cuerpos@{rep['k']}: "
          f"{rep['recall_cuerpos_at_k']:.1%} · {rep['items_evaluados']} ítems")
    for a, v in rep["por_area"].items():
        print(f"  {AREA_SLUG.get(a, a):15} {v['acierto_at_k']:6.1%}  ({v['items']} ítems)")
    print(f"máximo de pasajes del mismo documento → n.º de preguntas: {rep['max_mismo_documento']}")
    print(f"Detalle: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
