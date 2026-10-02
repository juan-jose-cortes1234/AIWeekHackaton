"""Paquetes para trabajar en Google Colab.

    python -m src.index.paquete_colab                # modo "indice": para construir el índice
    python -m src.index.paquete_colab --modo muestra # modo "muestra": para responder y evaluar

- **indice** → `dist/paquete_colab.zip`: código (`src/`, `scripts/`), `requirements.txt`,
  los fragmentos (`build/indice/chunks.jsonl`, `build/corpus/_fuga.json`) y la caché de
  embeddings (`build/cache/emb/`), para que Colab calcule **solo los fragmentos nuevos o
  modificados** (extensión incremental). `--sin-cache` fuerza el cálculo completo. Se usa con
  `notebooks/indice_en_colab.ipynb`.
- **muestra** → `dist/paquete_colab_muestra.zip`: lo anterior más `data/` y `schema/`. El
  cuaderno `notebooks/muestra_en_colab.ipynb` primero actualiza el índice en la GPU (con la
  caché, solo recalcula los fragmentos que cambiaron) y luego responde y evalúa la muestra: un
  solo viaje a Colab devuelve índice + resultados. No hace falta tener el índice local al día.
  Con `--con-indice` lleva además el índice ya construido (FAISS, BM25 y manifiesto), siempre
  que corresponda a estos fragmentos: el cuaderno lo reutiliza en segundos en lugar de rehacer
  BM25 en CPU, y el zip sirve para compartir el índice con el equipo (Drive).

Nunca incluye `.env` (la llave del juez) ni los documentos originales.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from src.config import RAIZ, config
from src.index.build import sha256_archivo

def _codigo(z: zipfile.ZipFile, carpetas: tuple[str, ...]) -> None:
    for carpeta in carpetas:
        for p in sorted((RAIZ / carpeta).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".env":
                z.write(p, p.relative_to(RAIZ).as_posix())
    for p in (RAIZ / "requirements.txt", RAIZ / ".env.example"):
        z.write(p, p.name)


def _indice_al_dia(chunks: Path) -> bool:
    """¿El índice local (FAISS, BM25, manifiesto) corresponde a estos fragmentos?"""
    import json

    d = config.index_dir
    manifiesto = d / "index_manifest.json"
    if not (manifiesto.is_file() and (d / "index.faiss").is_file() and (d / "bm25").is_dir()):
        return False
    m = json.loads(manifiesto.read_text(encoding="utf-8"))
    return (m.get("sha256_chunks") == sha256_archivo(chunks)
            and m.get("sha256_faiss") == sha256_archivo(d / "index.faiss"))


def _huella() -> str:
    """Fecha de generación y huella del código: el cuaderno la imprime para confirmar que
    Colab/Kaggle usa el paquete recién subido (Kaggle ancla la versión del dataset)."""
    import hashlib
    from datetime import datetime

    h = hashlib.sha256()
    for carpeta in ("src", "config", "scripts"):
        for f in sorted((RAIZ / carpeta).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                h.update(f.relative_to(RAIZ).as_posix().encode("utf-8"))
                h.update(f.read_bytes())
    return (f"Paquete generado: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"Huella del código: {h.hexdigest()[:12]}\n")


def crear(modo: str = "indice", destino: Path | None = None, con_cache: bool = True,
          con_indice: bool = False) -> Path:
    chunks = config.index_dir / "chunks.jsonl"
    fuga = config.corpus_out_dir / "_fuga.json"
    if not chunks.is_file():
        raise SystemExit("No hay build/indice/chunks.jsonl: corra primero python -m src.corpus.build")
    if con_indice and not _indice_al_dia(chunks):
        raise SystemExit("--con-indice: el índice local no corresponde a build/indice/chunks.jsonl "
                         "(o falta). Constrúyalo (python -m src.index.build o el cuaderno) o "
                         "genere el paquete sin --con-indice.")
    nombre = "paquete_colab.zip" if modo == "indice" else "paquete_colab_muestra.zip"
    destino = destino or RAIZ / "dist" / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        _codigo(z, ("src", "scripts", "config") if modo == "indice"
                else ("src", "scripts", "config", "data", "schema"))
        z.write(chunks, "build/indice/chunks.jsonl")
        # Caché de embeddings: con ella Colab solo calcula los fragmentos nuevos o
        # modificados (extensión incremental del índice) en lugar de todo el corpus.
        cache = RAIZ / "build" / "cache" / "emb"
        if con_cache and cache.is_dir():
            for p in sorted(cache.glob("*.npz")):
                z.write(p, f"build/cache/emb/{p.name}")
        if fuga.is_file():
            z.write(fuga, "build/corpus/_fuga.json")
        z.writestr("PAQUETE.txt", _huella())
        if con_indice:
            d = config.index_dir
            z.write(d / "index.faiss", "build/indice/index.faiss")
            z.write(d / "index_manifest.json", "build/indice/index_manifest.json")
            for p in sorted((d / "bm25").iterdir()):
                z.write(p, f"build/indice/bm25/{p.name}")
    return destino


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=("indice", "muestra"), default="indice")
    ap.add_argument("--sin-cache", action="store_true",
                    help="no incluir la caché (recalcula todos los embeddings)")
    ap.add_argument("--con-indice", action="store_true",
                    help="incluir el índice ya construido (debe corresponder a los fragmentos)")
    args = ap.parse_args(argv)
    ruta = crear(args.modo, con_cache=not args.sin_cache, con_indice=args.con_indice)
    cuaderno = "indice_en_colab" if args.modo == "indice" else "muestra_en_colab"
    print(f"{ruta} ({ruta.stat().st_size / 1e6:.1f} MB). Úselo con notebooks/{cuaderno}.ipynb.")
    with zipfile.ZipFile(ruta) as z:
        print(z.read("PAQUETE.txt").decode("utf-8").strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
