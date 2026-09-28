"""Reporte de brechas del corpus: `python -m src.eval.brechas` → `docs/BRECHAS.md`.

Lista las normas que el banco necesita y que **todavía no están** en el corpus:
- del `data/seed_targets.json`, ordenadas por `items_del_banco` (peso real en las 1.042 preguntas);
- de los `legal_basis` de la muestra (solo nombres de normas; nada de esto se indexa).

Funciona aunque aún no exista corpus: en ese caso todo figura como faltante,
lo que sirve de lista de trabajo para el equipo.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from src.config import RAIZ, config
from src.oficial import AREA_SLUG, citations


def cuerpos_en_corpus(resumen_path: Path) -> set[tuple]:
    if not resumen_path.is_file():
        return set()
    resumen = json.loads(resumen_path.read_text(encoding="utf-8"))
    return {tuple(c) for d in resumen["documentos"] for c in d.get("cuerpos", [])}


def nombre(cuerpo: tuple) -> str:
    tipo, num, anio = cuerpo
    if tipo == "jurisprudencia":
        return f"Sentencia {num} de {anio}"
    if num:
        return f"{tipo.replace('_', ' ').capitalize()} {num} de {anio}"
    return tipo.replace("_", " ").capitalize()


def calcular(presentes: set[tuple], seed_path: Path, preguntas: list[dict]) -> dict:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))["documentos"]
    faltan_seed = []
    total_items = cubiertos = 0
    for s in seed:
        c = tuple(s["canonico"])
        total_items += s["items_del_banco"]
        if c in presentes:
            cubiertos += s["items_del_banco"]
        else:
            faltan_seed.append({"cuerpo": list(c), "norma": s["norma"],
                                "items": s["items_del_banco"], "areas": s["areas"],
                                "donde_buscar": s["donde_buscar"]})
    faltan_seed.sort(key=lambda x: (-x["items"], x["norma"]))

    muestra: dict[tuple, dict] = defaultdict(lambda: {"ids": [], "areas": set()})
    for it in preguntas:
        for c in citations.bodies(citations.extract(it.get("legal_basis") or "")):
            if c not in presentes:
                muestra[c]["ids"].append(it["id"])
                muestra[c]["areas"].add(it.get("area") or "")
    faltan_muestra = sorted(
        ({"cuerpo": list(c), "nombre": nombre(c), "ids": v["ids"], "areas": sorted(v["areas"])}
         for c, v in muestra.items()), key=lambda x: (-len(x["ids"]), x["nombre"]))
    return {"items_seed_cubiertos": cubiertos, "items_seed_total": total_items,
            "faltan_seed": faltan_seed, "faltan_muestra": faltan_muestra,
            "normas_en_corpus": len(presentes)}


def _areas(areas) -> str:
    return ", ".join(AREA_SLUG.get(a, a) for a in areas if a)


def markdown(r: dict) -> str:
    pct = r["items_seed_cubiertos"] / r["items_seed_total"] if r["items_seed_total"] else 0
    lineas = [
        "# Brechas del corpus",
        "",
        f"Generado por `python -m src.eval.brechas` el {date.today().isoformat()}. "
        "No editar a mano.",
        "",
        f"- Normas distintas ya presentes en el corpus: **{r['normas_en_corpus']}**",
        f"- Ítems del banco cubiertos según el seed: **{r['items_seed_cubiertos']} de "
        f"{r['items_seed_total']} ({pct:.0%})**",
        "",
        "## 1. Normas del seed que faltan (por peso en el banco)",
        "",
        "Recordatorio: para sentencias SL/SP/SC/STC el seed apunta a la Corte "
        "Constitucional, pero son de la Corte Suprema de Justicia.",
        "",
        "| Ítems del banco | Norma | Áreas | Dónde buscar |",
        "|---:|---|---|---|",
    ]
    for f in r["faltan_seed"]:
        lineas.append(f"| {f['items']} | {f['norma']} | {_areas(f['areas'])} | {f['donde_buscar']} |")
    lineas += [
        "",
        "## 2. Normas citadas en la muestra que faltan",
        "",
        "El seed no es exhaustivo: estas normas aparecen en los fundamentos de la muestra "
        "y no están en el corpus. Son indicio de brechas mayores en el banco completo.",
        "",
        "| Norma | Ítems de la muestra | Áreas |",
        "|---|---|---|",
    ]
    for f in r["faltan_muestra"]:
        lineas.append(f"| {f['nombre']} | {len(f['ids'])} | {_areas(f['areas'])} |")
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--resumen", type=Path, default=config.corpus_out_dir / "_resumen.json")
    ap.add_argument("--seed", type=Path, default=RAIZ / "data" / "seed_targets.json")
    ap.add_argument("--preguntas", type=Path, default=RAIZ / "data" / "sample_50.jsonl")
    ap.add_argument("--out", type=Path, default=RAIZ / "docs" / "BRECHAS.md")
    args = ap.parse_args(argv)
    preguntas = [json.loads(l) for l in args.preguntas.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    r = calcular(cuerpos_en_corpus(args.resumen), args.seed, preguntas)
    args.out.write_text(markdown(r), encoding="utf-8", newline="\n")
    print(f"Seed cubierto: {r['items_seed_cubiertos']}/{r['items_seed_total']} ítems · "
          f"faltan {len(r['faltan_seed'])} normas del seed y {len(r['faltan_muestra'])} de la "
          f"muestra → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
