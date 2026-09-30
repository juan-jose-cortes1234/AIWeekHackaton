"""Paquete para construir el índice en Google Colab: `python -m src.index.paquete_colab`.

Crea `dist/paquete_colab.zip` con lo mínimo para calcular los embeddings en una
GPU: el código (`src/`, `scripts/`), `requirements.txt` y los fragmentos ya
construidos (`build/indice/chunks.jsonl` + `build/corpus/_fuga.json`). No lleva
los documentos originales ni la llave del juez.

En Colab se usa con `notebooks/indice_en_colab.ipynb`; el resultado
(`indice_colab.zip`) se descomprime en la raíz del proyecto.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from src.config import RAIZ, config


def crear(destino: Path | None = None) -> Path:
    chunks = config.index_dir / "chunks.jsonl"
    fuga = config.corpus_out_dir / "_fuga.json"
    if not chunks.is_file():
        raise SystemExit("No hay build/indice/chunks.jsonl: corra primero python -m src.corpus.build")
    destino = destino or RAIZ / "dist" / "paquete_colab.zip"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for carpeta in ("src", "scripts"):
            for p in sorted((RAIZ / carpeta).rglob("*")):
                if p.is_file() and "__pycache__" not in p.parts and p.name != ".env":
                    z.write(p, p.relative_to(RAIZ).as_posix())
        for p in (RAIZ / "requirements.txt", RAIZ / ".env.example"):
            z.write(p, p.name)
        z.write(chunks, "build/indice/chunks.jsonl")
        if fuga.is_file():
            z.write(fuga, "build/corpus/_fuga.json")
    return destino


def main() -> int:
    ruta = crear()
    print(f"{ruta} ({ruta.stat().st_size / 1e6:.1f} MB). Súbalo a Colab con notebooks/indice_en_colab.ipynb.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
