"""Índice léxico BM25 con un tokenizador para texto jurídico en español.

Los embeddings confunden “artículo 42” con “artículo 24” (enunciado B.3); BM25
no. Por eso el tokenizador:
- normaliza como el evaluador (minúsculas, sin tildes);
- **conserva los números** y los identificadores de sentencia (`c-355`, `su-214`,
  `sl3385` → `sl-3385`) y los de artículos con guion o decimales (`240-1`, `2.2.1.1`);
- quita stopwords y aplica stemming Snowball en español a las palabras.

Se guarda en `INDEX_DIR/bm25/` junto al índice denso.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

from src.config import config
from src.oficial import citations

STOPWORDS = frozenset("""
a al algo algunas algunos ante antes como con contra cual cuales cuando de del desde donde
durante e el ella ellas ellos en entre era es esa esas ese eso esos esta estas este esto estos
fue fueron ha han hasta la las le les lo los mas me mi muy no nos o otra otras otro otros para
pero por que quien quienes se sea segun ser si sin sino sobre su sus tal tambien te tiene
tienen toda todas todo todos tu un una uno unos y ya cuál qué cuáles
""".split())

_SENT = re.compile(r"\b(c|t|su|sl|sc|sp|stc|stl|ac|au)\s*-?\s*(\d{1,5})\b")
_TOKEN = re.compile(r"[a-z]{1,4}-\d{1,5}|\d+(?:[.\-]\d+)*[a-z]?|[a-zñ]+")


@lru_cache(maxsize=1)
def _stemmer():
    import Stemmer

    return Stemmer.Stemmer("spanish")


def tokenizar(texto: str) -> list[str]:
    t = citations.norm(texto)
    t = _SENT.sub(lambda m: f"{m.group(1)}-{int(m.group(2))}", t)
    t = re.sub(r"\b(\d+)\s*(?:o|º|°)\b", r"\1", t)          # 1o. / 12º → 1 / 12
    crudos = _TOKEN.findall(t)
    palabras = [w for w in crudos if w not in STOPWORDS]
    alfab = [w for w in palabras if w.isalpha()]
    raices = dict(zip(alfab, _stemmer().stemWords(alfab))) if alfab else {}
    return [raices.get(w, w) for w in palabras]


class IndiceBM25:
    def __init__(self, retriever):
        self.retriever = retriever

    @classmethod
    def construir(cls, textos: list[str]) -> "IndiceBM25":
        import bm25s

        r = bm25s.BM25()
        r.index([tokenizar(t) or ["_vacio_"] for t in textos], show_progress=False)
        return cls(r)

    def guardar(self, directorio: Path) -> None:
        directorio.mkdir(parents=True, exist_ok=True)
        self.retriever.save(str(directorio), show_progress=False)

    @classmethod
    def cargar(cls, directorio: Path) -> "IndiceBM25":
        import bm25s

        return cls(bm25s.BM25.load(str(directorio), show_progress=False))

    def puntajes(self, consulta: str) -> np.ndarray:
        """Puntaje BM25 de la consulta contra todos los fragmentos (en orden de chunks.jsonl)."""
        toks = tokenizar(consulta)
        if not toks:
            return np.zeros(self.retriever.scores["num_docs"], dtype=np.float32)
        return np.asarray(self.retriever.get_scores(toks), dtype=np.float32)

    def buscar(self, consulta: str, k: int = 50) -> list[tuple[int, float]]:
        """Top-k (id, puntaje) con desempate estable por id."""
        s = self.puntajes(consulta)
        orden = np.lexsort((np.arange(len(s)), -s))[:k]
        return [(int(i), float(s[i])) for i in orden if s[i] > 0]


def construir_bm25(dir_indice: Path) -> IndiceBM25:
    with (dir_indice / "chunks.jsonl").open(encoding="utf-8") as fh:
        textos = [json.loads(l)["texto"] for l in fh if l.strip()]
    idx = IndiceBM25.construir(textos)
    idx.guardar(dir_indice / "bm25")
    return idx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Construye el índice BM25 en INDEX_DIR/bm25/.")
    ap.add_argument("--dir", type=Path, default=config.index_dir)
    args = ap.parse_args(argv)
    if not (args.dir / "chunks.jsonl").is_file():
        print(f"No hay {args.dir / 'chunks.jsonl'}; corra primero `python -m src.corpus.build`.")
        return 0
    construir_bm25(args.dir)
    print(f"BM25 guardado en {args.dir / 'bm25'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
