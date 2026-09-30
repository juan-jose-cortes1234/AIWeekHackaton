"""Guardia anti-fuga: `python -m src.corpus.fuga`.

Indexar el banco de preguntas o material con respuestas esperadas descalifica
(enunciado §3.2 y §8). Esta guardia revisa el corpus procesado contra
`data/sample_50.jsonl` (y cualquier otro JSONL de preguntas que se le pase):

Lo prohibido es indexar el **banco** (preguntas con sus respuestas), no las
normas: una norma oficial contiene, por diseño, lo que responde la pregunta, y
muchas preguntas citan textualmente artículos o sentencias (p. ej. "reproducción
literal"). Por eso:

- **Grave** (bloquea la construcción del índice):
  * un archivo del corpus crudo que parece banco de preguntas (JSON/JSONL con
    `respuesta_esperada`, `legal_basis` o `respuesta_correcta`), o
    `CORPUS_RAW_DIR` dentro de `data/`;
  * un fragmento que contiene **a la vez** la pregunta (≥ 3 8-gramas) y ≥ 50 % de
    la respuesta esperada **del mismo ítem** (firma de material de preguntas y respuestas);
  * un fragmento que contiene enunciados de **varias preguntas distintas**
    (≥ 3 ítems con ≥ 3 8-gramas cada uno): parece una lista de preguntas.
- **Revisión humana** (solo se lista): coincidencias solo con la pregunta o solo
  con la respuesta, típicamente citas literales de normas. No se borra nada.

Decisión tomada al construir el corpus real (2026-09-29): con la regla anterior,
la Constitución, el Código Civil y sentencias del propio seed oficial quedaban
bloqueados por ser citados literalmente en la muestra.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from src.config import RAIZ, config
from src.oficial import citations

N = 8
MIN_NGRAMAS_PREGUNTA = 3
FRACCION_RESPUESTA = 0.5
_MARCAS_BANCO = ('"respuesta_esperada"', '"legal_basis"', '"respuesta_correcta"',
                 '"texto_respuesta_correcta"')


@dataclass
class Informe:
    graves: list[str] = field(default_factory=list)
    revision: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.graves


def ngramas(texto: str, n: int = N) -> set[tuple[str, ...]]:
    toks = re.findall(r"\w+", citations.norm(texto))
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def cargar_preguntas(rutas: list[Path]) -> list[dict]:
    filas = []
    for r in rutas:
        with r.open(encoding="utf-8") as fh:
            filas.extend(json.loads(l) for l in fh if l.strip())
    return filas


def revisar_crudo(raiz: Path) -> list[str]:
    """Problemas graves a nivel de archivos del corpus crudo."""
    graves = []
    try:
        raiz.resolve().relative_to((RAIZ / "data").resolve())
        graves.append(f"CORPUS_RAW_DIR ({raiz}) está dentro de data/: ahí viven las preguntas.")
    except ValueError:
        pass
    if raiz.is_dir():
        for p in raiz.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".json", ".jsonl", ".csv", ".txt"):
                if p.name == "fuentes.csv":
                    continue
                cabeza = p.read_text(encoding="utf-8", errors="ignore")[:20000]
                if any(m in cabeza for m in _MARCAS_BANCO):
                    graves.append(f"{p}: parece un banco de preguntas/respuestas.")
    return graves


def revisar_fragmentos(fragmentos: list[dict], preguntas: list[dict]) -> Informe:
    inf = Informe()
    # Índice invertido 8-grama → fragmentos que lo contienen.
    indice: dict[tuple, set[str]] = {}
    for fr in fragmentos:
        for g in ngramas(fr["texto"]):
            indice.setdefault(g, set()).add(fr["chunk_id"])

    def conteos(texto: str) -> tuple[dict[str, int], int]:
        gs = ngramas(texto or "")
        c: dict[str, int] = {}
        for g in gs:
            for cid in indice.get(g, ()):
                c[cid] = c.get(cid, 0) + 1
        return c, len(gs)

    preguntas_por_chunk: dict[str, set] = {}
    for q in preguntas:
        qid = q.get("id")
        c_preg, _ = conteos(q.get("pregunta"))
        c_resp, n_resp = conteos(q.get("respuesta_esperada"))
        for cid in sorted(set(c_preg) | set(c_resp)):
            np_, nr = c_preg.get(cid, 0), c_resp.get(cid, 0)
            con_preg = np_ >= MIN_NGRAMAS_PREGUNTA
            con_resp = n_resp > 0 and nr / n_resp >= FRACCION_RESPUESTA
            if con_preg:
                preguntas_por_chunk.setdefault(cid, set()).add(qid)
            partes = []
            if np_:
                partes.append(f"{np_} 8-gramas del enunciado")
            if nr:
                partes.append(f"{nr}/{n_resp} 8-gramas de la respuesta esperada ({nr / n_resp:.0%})")
            msg = f"pregunta {qid}: {' y '.join(partes)} en {cid}"
            if con_preg and con_resp:
                inf.graves.append(msg + " — contiene pregunta y respuesta del mismo ítem")
            else:
                inf.revision.append(msg)
    for cid, qids in sorted(preguntas_por_chunk.items()):
        if len(qids) >= MIN_NGRAMAS_PREGUNTA:
            inf.graves.append(f"{cid}: contiene enunciados de {len(qids)} preguntas distintas "
                              f"{sorted(qids)} — parece una lista de preguntas")
    return inf


def revisar(chunks_path: Path, raiz_crudo: Path | None, rutas_preguntas: list[Path]) -> Informe:
    fragmentos = []
    if chunks_path.is_file():
        with chunks_path.open(encoding="utf-8") as fh:
            fragmentos = [json.loads(l) for l in fh if l.strip()]
    inf = revisar_fragmentos(fragmentos, cargar_preguntas(rutas_preguntas))
    if raiz_crudo is not None:
        inf.graves = revisar_crudo(raiz_crudo) + inf.graves
    return inf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chunks", type=Path, default=config.index_dir / "chunks.jsonl")
    ap.add_argument("--dir", type=Path, default=config.corpus_raw_dir)
    ap.add_argument("--preguntas", type=Path, nargs="*",
                    default=[RAIZ / "data" / "sample_50.jsonl"])
    args = ap.parse_args(argv)
    inf = revisar(args.chunks, args.dir, [p for p in args.preguntas if p.is_file()])
    for m in inf.revision:
        print(f"REVISAR  {m}")
    for m in inf.graves:
        print(f"GRAVE    {m}")
    print(f"\n{len(inf.graves)} problemas graves, {len(inf.revision)} coincidencias para revisar.")
    return 0 if inf.ok else 1


if __name__ == "__main__":
    sys.exit(main())
