"""Paquetes para trabajar en Google Colab.

    python -m src.index.paquete_colab                # modo "indice": para construir el índice
    python -m src.index.paquete_colab --modo muestra # modo "muestra": para responder y evaluar

- **indice** → `dist/paquete_colab.zip`: código (`src/`, `scripts/`), `requirements.txt` y
  los fragmentos (`build/indice/chunks.jsonl`, `build/corpus/_fuga.json`). Se usa con
  `notebooks/indice_en_colab.ipynb`.
- **muestra** → `dist/paquete_colab_muestra.zip`: lo anterior más el índice ya construido
  (`index.faiss`, BM25, manifiesto), `data/` y `schema/`. Se usa con
  `notebooks/muestra_en_colab.ipynb`.

Nunca incluye `.env` (la llave del juez) ni los documentos originales.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from src.config import RAIZ, config

ARCHIVOS_INDICE = ("index.faiss", "index_manifest.json", "chunks.jsonl")


def _codigo(z: zipfile.ZipFile, carpetas: tuple[str, ...]) -> None:
    for carpeta in carpetas:
        for p in sorted((RAIZ / carpeta).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".env":
                z.write(p, p.relative_to(RAIZ).as_posix())
    for p in (RAIZ / "requirements.txt", RAIZ / ".env.example"):
        z.write(p, p.name)


def crear(modo: str = "indice", destino: Path | None = None) -> Path:
    chunks = config.index_dir / "chunks.jsonl"
    fuga = config.corpus_out_dir / "_fuga.json"
    if not chunks.is_file():
        raise SystemExit("No hay build/indice/chunks.jsonl: corra primero python -m src.corpus.build")
    if modo == "muestra":
        faltan = [f for f in ARCHIVOS_INDICE if not (config.index_dir / f).is_file()]
        if faltan or not (config.index_dir / "bm25").is_dir():
            raise SystemExit(f"Falta el índice ({faltan or 'bm25'}): constrúyalo primero "
                             "(python -m src.index.build o el cuaderno de Colab).")
    nombre = "paquete_colab.zip" if modo == "indice" else "paquete_colab_muestra.zip"
    destino = destino or RAIZ / "dist" / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        if modo == "indice":
            _codigo(z, ("src", "scripts"))
            z.write(chunks, "build/indice/chunks.jsonl")
        else:
            _codigo(z, ("src", "scripts", "data", "schema"))
            for f in ARCHIVOS_INDICE:
                z.write(config.index_dir / f, f"build/indice/{f}")
            for p in sorted((config.index_dir / "bm25").iterdir()):
                z.write(p, f"build/indice/bm25/{p.name}")
        if fuga.is_file():
            z.write(fuga, "build/corpus/_fuga.json")
    return destino


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=("indice", "muestra"), default="indice")
    args = ap.parse_args(argv)
    ruta = crear(args.modo)
    cuaderno = "indice_en_colab" if args.modo == "indice" else "muestra_en_colab"
    print(f"{ruta} ({ruta.stat().st_size / 1e6:.1f} MB). Úselo con notebooks/{cuaderno}.ipynb.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
