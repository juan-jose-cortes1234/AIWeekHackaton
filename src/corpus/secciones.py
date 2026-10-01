"""Chequeo automático del corte por secciones de las sentencias.

    python -m src.corpus.secciones                      # las tres sentencias de control
    python -m src.corpus.secciones sentencia_t-760_2008 # otras
    python -m src.corpus.secciones --todas              # resumen de todas las sentencias

Cuenta los fragmentos de cada sección en `build/indice/chunks.jsonl` y marca lo sospechoso:
una sentencia sin RESUELVE o sin parte motiva (consideraciones, competencia, problema
jurídico o caso concreto), o un RESUELVE que ocupa más del 25 % de la
sentencia (síntoma de que un falso título arrastró el cuerpo del fallo, como pasaba con la
T-760 de 2008 antes del detector estricto). Sale con código 1 si algo se ve raro.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict

from src.config import config

CONTROL = ("sentencia_c-355_2006", "sentencia_t-760_2008", "sentencia_su-455_2020")
MAX_RESUELVE = 0.25
# Títulos de la parte motiva: "1. Competencia" o "Caso concreto" son subtítulos de las
# consideraciones y, al detectarse, toman su lugar como etiqueta.
MOTIVA = ("CONSIDERACIONES", "COMPETENCIA", "PROBLEMA JURÍDICO", "CASO CONCRETO")


def distribuciones() -> dict[str, Counter]:
    por_doc: dict[str, Counter] = defaultdict(Counter)
    with open(config.index_dir / "chunks.jsonl", encoding="utf-8") as f:
        for linea in f:
            c = json.loads(linea)
            if c.get("tipo_norma") == "sentencia":
                por_doc[c["doc_id"]][c.get("seccion") or "(sin sección)"] += 1
    return por_doc


def alertas(cuenta: Counter) -> list[str]:
    total = sum(cuenta.values())
    avisos = []
    if not cuenta.get("RESUELVE"):
        avisos.append("sin RESUELVE")
    elif cuenta["RESUELVE"] / total > MAX_RESUELVE:
        avisos.append(f"RESUELVE = {cuenta['RESUELVE']}/{total} fragmentos")
    if not any(cuenta.get(s) for s in MOTIVA):
        avisos.append("sin parte motiva")
    return avisos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="*", help="doc_id de las sentencias (por defecto, las de control)")
    ap.add_argument("--todas", action="store_true", help="resumen de todas las sentencias")
    args = ap.parse_args(argv)
    por_doc = distribuciones()
    raras = 0
    for doc in args.docs or CONTROL:
        cuenta = por_doc.get(doc)
        if not cuenta:
            print(f"{doc}: NO ESTÁ en el corpus procesado")
            raras += 1
            continue
        avisos = alertas(cuenta)
        raras += bool(avisos)
        print(f"{doc} ({sum(cuenta.values())} fragmentos)"
              + (f"  ⚠ {'; '.join(avisos)}" if avisos else "  OK"))
        for seccion, n in cuenta.most_common():
            print(f"    {n:5d}  {seccion}")
    if args.todas:
        con_aviso = {d: alertas(c) for d, c in sorted(por_doc.items()) if alertas(c)}
        print(f"\nTodas: {len(por_doc)} sentencias, {len(con_aviso)} con avisos")
        for d, a in con_aviso.items():
            print(f"    {d}: {'; '.join(a)}")
    return 1 if raras else 0


if __name__ == "__main__":
    sys.exit(main())
