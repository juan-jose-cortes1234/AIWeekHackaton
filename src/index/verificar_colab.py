"""Verifica el índice empaquetado sin descargar ni cargar modelos.

python -m src.index.verificar_colab --estructuras
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import RAIZ, config
from src.pipeline.identidad import sha256_archivo

ARCHIVOS_BM25 = ("params.index.json", "vocab.index.json", "data.csc.index.npy",
                 "indices.csc.index.npy", "indptr.csc.index.npy")


def verificar(raiz: Path = RAIZ, estructuras: bool = False) -> dict:
    d = raiz / "build" / "indice"
    requeridos = [d / n for n in ("chunks.jsonl", "index.faiss", "index_manifest.json")]
    requeridos += [d / "bm25" / n for n in ARCHIVOS_BM25]
    faltan = [str(p.relative_to(raiz)) for p in requeridos if not p.is_file()]
    if faltan:
        raise ValueError("Paquete incompleto; faltan: " + ", ".join(faltan))
    m = json.loads((d / "index_manifest.json").read_text(encoding="utf-8"))
    if m.get("modelo") != config.encoder_model:
        raise ValueError(f"El índice usa {m.get('modelo')}; ENCODER_MODEL={config.encoder_model}.")
    for nombre, clave in (("chunks.jsonl", "sha256_chunks"), ("index.faiss", "sha256_faiss")):
        if sha256_archivo(d / nombre) != m.get(clave):
            raise ValueError(f"Hash incompatible: {nombre}. Suba un paquete con índice consistente.")
    with (d / "chunks.jsonl").open(encoding="utf-8") as fh:
        n = sum(bool(linea.strip()) for linea in fh)
    params = json.loads((d / "bm25" / "params.index.json").read_text(encoding="utf-8"))
    if not n or n != m.get("n_fragmentos") or n != params.get("num_docs"):
        raise ValueError("El número de fragmentos difiere entre chunks, manifiesto y BM25.")
    fuga = raiz / "build" / "corpus" / "_fuga.json"
    if fuga.is_file() and json.loads(fuga.read_text(encoding="utf-8")).get("graves"):
        raise ValueError("La guardia anti-fuga registra problemas graves en este corpus.")
    if estructuras:
        import faiss
        from src.index.lexico import IndiceBM25

        indice = faiss.read_index(str(d / "index.faiss"))
        if indice.ntotal != n or indice.d != m.get("dimension"):
            raise ValueError("La estructura FAISS no coincide con el manifiesto.")
        bm25 = IndiceBM25.cargar(d / "bm25")
        if bm25.retriever.scores["num_docs"] != n:
            raise ValueError("La estructura BM25 no corresponde a estos fragmentos.")
    return {"modelo": m["modelo"], "n_fragmentos": n, "dimension": m["dimension"],
            "sha256_chunks": m["sha256_chunks"], "sha256_faiss": m["sha256_faiss"],
            "estructuras_verificadas": estructuras}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    ap.add_argument("--estructuras", action="store_true",
                    help="carga FAISS y BM25, sin encoder, reranker ni decoder")
    args = ap.parse_args(argv)
    try:
        rep = verificar(args.raiz, args.estructuras)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
