"""Construye el índice vectorial: `python -m src.index.build [--forzar]`.

Entrada: `INDEX_DIR/chunks.jsonl` (de `src.corpus.build`). Salidas en `INDEX_DIR`:
- `index.faiss`: `IndexFlatIP` exacto; el id de cada vector es su línea en chunks.jsonl.
- `bm25/`: índice léxico BM25 (ver `src.index.lexico`).
- `index_manifest.json`: modelo, dimensión, n.º de fragmentos, sha256 de
  chunks.jsonl y de index.faiss, fecha. Sirve para congelar el índice.

Es idempotente: si chunks.jsonl y el modelo no cambiaron, no recalcula nada.
Se niega a indexar si la guardia anti-fuga reportó problemas graves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.config import config
from src.index.encoder import CacheEmbeddings, Codificador, EncoderST
from src.index.lexico import construir_bm25


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_chunks(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def verificar_fuga(dir_corpus: Path) -> None:
    informe = dir_corpus / "_fuga.json"
    if informe.is_file():
        graves = json.loads(informe.read_text(encoding="utf-8")).get("graves") or []
        if graves:
            raise SystemExit("La guardia anti-fuga reportó problemas graves; no se indexa.\n"
                             + "\n".join(graves[:10]))


def construir_indice(dir_indice: Path, enc: Codificador | None = None, forzar: bool = False,
                     dir_corpus: Path | None = None, nombre_modelo: str | None = None) -> dict:
    import faiss

    chunks_path = dir_indice / "chunks.jsonl"
    if not chunks_path.is_file():
        raise SystemExit(f"No existe {chunks_path}; corra `python -m src.corpus.build`.")
    verificar_fuga(dir_corpus or config.corpus_out_dir)

    nombre = enc.nombre if enc is not None else (nombre_modelo or config.encoder_model)
    sha_chunks = sha256_archivo(chunks_path)
    man_path = dir_indice / "index_manifest.json"
    faiss_path = dir_indice / "index.faiss"
    if not forzar and man_path.is_file() and faiss_path.is_file():
        previo = json.loads(man_path.read_text(encoding="utf-8"))
        if (previo.get("sha256_chunks") == sha_chunks and previo.get("modelo") == nombre
                and previo.get("sha256_faiss") == sha256_archivo(faiss_path)):
            previo["reutilizado"] = True
            return previo

    enc = enc or EncoderST(nombre)
    chunks = leer_chunks(chunks_path)
    cache = CacheEmbeddings(nombre)
    t0 = time.perf_counter()
    matriz, calculados = cache.codificar_pasajes(enc, [c["texto"] for c in chunks])
    segundos = time.perf_counter() - t0
    cache.guardar()

    indice = faiss.IndexFlatIP(enc.dimension)
    if len(chunks):
        indice.add(matriz)
    faiss.write_index(indice, str(faiss_path))

    manifiesto = {
        "modelo": nombre, "dimension": enc.dimension, "tipo_indice": "IndexFlatIP",
        "normalizado": True, "max_length": getattr(enc, "max_length", None),
        "n_fragmentos": len(chunks), "sha256_chunks": sha_chunks,
        "sha256_faiss": sha256_archivo(faiss_path),
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embeddings_calculados": calculados, "segundos_embedding": round(segundos, 2),
    }
    man_path.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    manifiesto["reutilizado"] = False
    return manifiesto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=config.index_dir)
    ap.add_argument("--forzar", action="store_true", help="recalcula aunque nada haya cambiado")
    args = ap.parse_args(argv)
    if not (args.dir / "chunks.jsonl").is_file():
        print(f"No hay {args.dir / 'chunks.jsonl'}; corra primero `python -m src.corpus.build`.")
        return 0
    m = construir_indice(args.dir, forzar=args.forzar)
    construir_bm25(args.dir)   # barato: siempre se reconstruye
    estado = "reutilizado (sin cambios)" if m["reutilizado"] else (
        f"{m['embeddings_calculados']} embeddings nuevos en {m['segundos_embedding']} s")
    print(f"Índice {m['tipo_indice']} · {m['modelo']} · dim {m['dimension']} · "
          f"{m['n_fragmentos']} fragmentos · {estado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
