"""Chequeo final de la entrega: `python -m src.eval.validar_entrega [submissions.jsonl] [--split test]`.

Sin la clave de respuestas (la tiene el jurado) verifica lo que sí se puede:
cada línea contra `schema/submission.schema.json`, ids completos y sin
duplicados respecto a las preguntas, formato coherente, pasajes presentes salvo
abstención y como máximo 10 pasajes con texto literal no vacío.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from src.config import RAIZ


def validar(entrega: Path, preguntas: Path) -> dict:
    import jsonschema

    esquema = json.loads((RAIZ / "schema" / "submission.schema.json").read_text(encoding="utf-8"))
    val = jsonschema.Draft202012Validator(esquema)
    lineas = [json.loads(l) for l in entrega.read_text(encoding="utf-8").splitlines() if l.strip()]
    items = {q["id"]: q for q in (json.loads(l) for l in preguntas.read_text(encoding="utf-8")
                                  .splitlines() if l.strip())}
    errores: list[str] = []
    ids = Counter(l.get("id") for l in lineas)
    errores += [f"id {i} duplicado ({n} veces)" for i, n in ids.items() if n > 1]
    faltan = sorted(set(items) - set(ids))
    sobran = sorted(set(ids) - set(items))
    if faltan:
        errores.append(f"{len(faltan)} preguntas sin respuesta: {faltan[:15]}")
    if sobran:
        errores.append(f"{len(sobran)} ids que no están en las preguntas: {sobran[:15]}")
    for l in lineas:
        i = l.get("id")
        errores += [f"id {i}: {e.message}" for e in val.iter_errors(l)]
        if i in items and l.get("formato") != items[i].get("formato"):
            errores.append(f"id {i}: formato {l.get('formato')} ≠ {items[i].get('formato')}")
        pas = l.get("pasajes_recuperados") or []
        if not l.get("abstencion") and not pas:
            errores.append(f"id {i}: sin pasajes y sin abstención")
        if len(pas) > 10:
            errores.append(f"id {i}: {len(pas)} pasajes (el evaluador solo mira 10)")
    abst = Counter(l.get("formato") for l in lineas if l.get("abstencion"))
    return {"lineas": len(lineas), "preguntas": len(items), "errores": errores,
            "abstenciones": dict(abst), "ok": not errores}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("entrega", nargs="?", type=Path, default=RAIZ / "submissions.jsonl")
    ap.add_argument("--split", choices=("sample", "test"), default="test")
    ap.add_argument("--preguntas", type=Path, default=None)
    args = ap.parse_args(argv)
    from src.pipeline.main import ENTRADAS

    preguntas = args.preguntas or ENTRADAS[args.split]
    for ruta in (args.entrega, preguntas):
        if not ruta.is_file():
            print(f"No existe {ruta}.")
            return 1
    r = validar(args.entrega, preguntas)
    for e in r["errores"][:50]:
        print(f"ERROR  {e}")
    veredicto = "VÁLIDA" if r["ok"] else f"{len(r['errores'])} ERRORES"
    print(f"\n{r['lineas']} líneas para {r['preguntas']} preguntas · "
          f"abstenciones {r['abstenciones']} · {veredicto}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
