"""Valida el corpus crudo: `python -m src.corpus.validar [--dir RUTA]`.

Sale con código 0 si todo está bien o si todavía no hay corpus (con instrucciones),
y con código 1 si `fuentes.csv` tiene errores.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import config
from src.corpus.fuentes import validar


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=config.corpus_raw_dir,
                    help="carpeta del corpus crudo (por defecto CORPUS_RAW_DIR)")
    args = ap.parse_args(argv)
    raiz: Path = args.dir

    if not raiz.is_dir() or not (raiz / "fuentes.csv").is_file():
        print(f"Aún no hay corpus en {raiz}.\n"
              "Cree la carpeta con fuentes.csv y los documentos según GUIA_CORPUS.md §3,\n"
              "y apunte CORPUS_RAW_DIR en .env a esa carpeta.")
        return 0

    res = validar(raiz)
    for a in res.avisos:
        print(f"AVISO  {a}")
    for e in res.errores:
        print(f"ERROR  {e}")
    print(f"\n{len(res.fuentes)} documentos válidos, {len(res.errores)} errores, "
          f"{len(res.avisos)} avisos.")
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
