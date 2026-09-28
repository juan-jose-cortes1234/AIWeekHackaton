"""Consulta manual del recuperador: `python -m src.retrieval.buscar "pregunta" [--area ÁREA] [-k 10]`."""
from __future__ import annotations

import argparse
import sys

from src.config import config
from src.corpus.fuentes import normalizar_area
from src.retrieval.hibrido import Recuperador


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pregunta")
    ap.add_argument("--area", default=None, help="nombre oficial o slug (p. ej. laboral)")
    ap.add_argument("-k", type=int, default=config.top_k_pasajes)
    args = ap.parse_args(argv)
    if not (config.index_dir / "index_manifest.json").is_file():
        print("No hay índice; corra `python -m src.corpus.build` y `python -m src.index.build`.")
        return 1
    area = normalizar_area(args.area) if args.area else None
    rec = Recuperador.cargar()
    for n, p in enumerate(rec.buscar(args.pregunta, area=area, k=args.k), start=1):
        primera = p.texto.split("\n", 1)[0]
        print(f"{n:>2}. [{p.score:.4f}] {'+'.join(p.origen):14} {primera}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
