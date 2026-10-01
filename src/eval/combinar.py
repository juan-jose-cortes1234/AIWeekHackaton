"""Combina una corrida parcial con una completa para evaluar un experimento.

    python -m src.eval.combinar --base runs/muestra_t22 --parcial runs/mc_elegir_primero \
        --out runs/mc_elegir_primero_50

Toma todas las respuestas de `--base` y reemplaza las que también estén en `--parcial` (por id).
Sirve para experimentos que solo cambian un formato (p. ej. selección múltiple): se responden en
Colab solo esas preguntas y el resto se reutiliza tal cual, sin gastar la llave del juez, porque
las respuestas de texto libre no cambian. Escribe `<out>/submissions.jsonl` en el orden de la base.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def leer(carpeta: Path) -> list[dict]:
    with open(carpeta / "submissions.jsonl", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def combinar(base: Path, parcial: Path, out: Path) -> tuple[int, int]:
    nuevas = {s["id"]: s for s in leer(parcial)}
    filas = leer(base)
    faltan = set(nuevas) - {s["id"] for s in filas}
    if faltan:
        raise SystemExit(f"Ids de la corrida parcial que no están en la base: {sorted(faltan)}")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "submissions.jsonl", "w", encoding="utf-8") as f:
        for s in filas:
            f.write(json.dumps(nuevas.get(s["id"], s), ensure_ascii=False) + "\n")
    return len(filas), len(nuevas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, required=True, help="corrida completa (carpeta)")
    ap.add_argument("--parcial", type=Path, required=True, help="corrida del experimento (carpeta)")
    ap.add_argument("--out", type=Path, required=True, help="carpeta de salida")
    args = ap.parse_args(argv)
    total, reemplazadas = combinar(args.base, args.parcial, args.out)
    print(f"{args.out / 'submissions.jsonl'}: {total} respuestas ({reemplazadas} del experimento).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
