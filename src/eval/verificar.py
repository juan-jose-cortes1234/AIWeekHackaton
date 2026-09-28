"""Simulacro de la verificación en vivo: `python -m src.eval.verificar --ids 51,290 [--split test]`.

El jurado elige 2–3 preguntas entregadas y pide regenerarlas; deben coincidir
**las normas citadas y los pasajes recuperados** (enunciado §7). Este comando
regenera esos ítems **sin caché** con el sistema actual y los compara con
`submissions.jsonl`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.config import RAIZ, config
from src.oficial import citations

CAMPOS_CITA = {
    "multiple_choice": ("justificacion",),
    "semi_open": ("respuesta", "referencia_legal"),
    "open_ended": ("marco_normativo", "analisis", "jurisprudencia", "conclusion"),
}


def normas_citadas(linea: dict) -> set[tuple]:
    texto = " ".join(str(linea.get(k) or "") for k in CAMPOS_CITA[linea["formato"]])
    return citations.bodies(citations.extract(texto))


def pasajes(linea: dict) -> list[tuple]:
    return [(p["doc_id"], p.get("inicio"), p.get("fin")) for p in linea.get("pasajes_recuperados") or []]


def comparar(entregada: dict, nueva: dict) -> dict:
    """Diferencias relevantes para la verificación en vivo."""
    r = {"id": entregada["id"],
         "pasajes_iguales": pasajes(entregada) == pasajes(nueva),
         "normas_iguales": normas_citadas(entregada) == normas_citadas(nueva),
         "abstencion_igual": bool(entregada.get("abstencion")) == bool(nueva.get("abstencion"))}
    if entregada["formato"] == "multiple_choice":
        r["letra_igual"] = entregada.get("respuesta_correcta") == nueva.get("respuesta_correcta")
    r["ok"] = all(v for k, v in r.items() if k.endswith("igual") or k.endswith("iguales"))
    if not r["normas_iguales"]:
        r["normas_entregadas"] = sorted(map(list, normas_citadas(entregada)))
        r["normas_regeneradas"] = sorted(map(list, normas_citadas(nueva)))
    return r


def verificar(ids: list[int], entrega: Path, preguntas: Path, rec, llm) -> list[dict]:
    from src.pipeline.main import leer_jsonl, responder_item

    entregadas = {l["id"]: l for l in leer_jsonl(entrega)}
    items = {q["id"]: q for q in leer_jsonl(preguntas)}
    res = []
    for i in ids:
        if i not in entregadas or i not in items:
            res.append({"id": i, "ok": False, "error": "id ausente de la entrega o de las preguntas"})
            continue
        nueva, _ = responder_item(items[i], rec, llm, usar_cache=False)
        res.append(comparar(entregadas[i], nueva))
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", required=True, help="ids separados por coma")
    ap.add_argument("--split", choices=("sample", "test"), default="test")
    ap.add_argument("--entrega", type=Path, default=RAIZ / "submissions.jsonl")
    ap.add_argument("--preguntas", type=Path, default=None)
    args = ap.parse_args(argv)
    from src.pipeline.main import ENTRADAS

    preguntas = args.preguntas or ENTRADAS[args.split]
    for ruta in (args.entrega, preguntas):
        if not ruta.is_file():
            print(f"No existe {ruta}.")
            return 1
    config.validar_final()
    from src.generation.llm import LLM
    from src.retrieval.hibrido import Recuperador

    ids = [int(x) for x in args.ids.split(",") if x.strip()]
    res = verificar(ids, args.entrega, preguntas, Recuperador.cargar(), LLM())
    for r in res:
        estado = "COINCIDE" if r["ok"] else "DIFIERE"
        print(f"id {r['id']}: {estado}  {json.dumps({k: v for k, v in r.items() if k not in ('id', 'ok')}, ensure_ascii=False)}")
    return 0 if all(r["ok"] for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
