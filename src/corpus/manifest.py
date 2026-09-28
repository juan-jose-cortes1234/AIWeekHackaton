"""Manifiesto y tablas de la bitácora: `python -m src.corpus.manifest`.

Lee `build/corpus/_resumen.json` (lo escribe `src.corpus.build`) y:
- escribe `corpus_manifest.json` en la raíz (formato del ejemplo oficial);
- regenera los bloques `<!-- AUTO:... -->` de `CORPUS.md` (inventario, totales y
  cobertura por área, esta última estimada con `data/seed_targets.json`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from src.config import RAIZ, config
from src.oficial import AREA_SLUG, AREAS

# Ítems del banco completo por área (enunciado §4.2).
ITEMS_POR_AREA = {
    "Derecho constitucional": 134, "Derecho administrativo": 124, "Derecho penal": 123,
    "Derecho procesal": 111, "Derecho comercial y sociedades": 104, "Derecho civil": 102,
    "Derecho de familia": 93, "Derecho tributario": 92, "Derecho laboral": 87,
    AREAS[-1]: 72,
}
LICENCIA = "CC-BY-4.0"


def _metodo(doc: dict) -> str:
    formatos = set(doc.get("formatos") or [])
    partes = []
    if formatos & {"html", "htm"}:
        partes.append("parser HTML")
    if "pdf" in formatos:
        partes.append("extraccion de PDF (OCR si no hay capa de texto)")
    if "docx" in formatos:
        partes.append("extraccion DOCX")
    if "txt" in formatos:
        partes.append("texto plano")
    seg = "segmentacion por seccion" if doc["tipo"] in ("sentencia", "concepto") \
        else "segmentacion por articulo"
    return " + ".join(partes + [seg])


def construir_manifiesto(resumen: dict, hoy: str | None = None) -> dict:
    docs = []
    for d in resumen["documentos"]:
        docs.append({
            "doc_id": d["doc_id"], "titulo": d["titulo"], "fuente": d["fuente"], "url": d["url"],
            "fecha_consulta": d["fecha_consulta"], "areas": d["areas"],
            "tipo": d["tipo"], "vigencia": d.get("vigencia"),
            "n_articulos": d["n_articulos"], "n_fragmentos": d["n_fragmentos"],
            "metodo_ingesta": _metodo(d), "sha256": d["sha256"],
        })
    return {
        "equipo": config.team_name or "<nombre del equipo>",
        "licencia": LICENCIA,
        "fecha_generacion": hoy or date.today().isoformat(),
        "enlace_nube": config.corpus_zip_url or "<URL del comprimido con el corpus y el indice>",
        "documentos": docs,
    }


def _area_corta(area: str) -> str:
    return AREA_SLUG.get(area, area).capitalize()


def _celda(s) -> str:
    return str(s if s not in (None, "") else "—").replace("|", "\\|")


def tabla_inventario(docs: list[dict]) -> str:
    filas = ["| doc_id | Título | Fuente | URL | Fecha de consulta | Artículos | Fragmentos | Áreas |",
             "|---|---|---|---|---|---:|---:|---|"]
    for d in docs:
        filas.append("| `{}` | {} | {} | {} | {} | {} | {} | {} |".format(
            d["doc_id"], _celda(d["titulo"]), _celda(d["fuente"]), _celda(d["url"]),
            _celda(d["fecha_consulta"]), _celda(d["n_articulos"]), d["n_fragmentos"],
            ", ".join(_area_corta(a) for a in d["areas"])))
    return "\n".join(filas)


def tabla_totales(resumen: dict) -> str:
    docs = resumen["documentos"]
    arts = sum(d["n_articulos"] or 0 for d in docs)
    chars = sum(d.get("n_caracteres", 0) for d in docs)
    return "\n".join([
        "| Métrica | Valor |", "|---|---:|",
        f"| Documentos incorporados | {len(docs)} |",
        f"| Artículos indexados | {arts} |",
        f"| Fragmentos en el índice | {resumen['n_fragmentos']} |",
        f"| Tamaño del corpus procesado | {chars / 1e6:.1f} MB |",
    ])


def cobertura_seed(resumen: dict, seed_path: Path) -> dict[str, tuple[int, int]]:
    """Por área: (ítems del seed cuyas normas están en el corpus, ítems del seed)."""
    presentes = {tuple(c) for d in resumen["documentos"] for c in d.get("cuerpos", [])}
    seed = json.loads(seed_path.read_text(encoding="utf-8"))["documentos"]
    res = {a: [0, 0] for a in AREAS}
    for s in seed:
        cuerpo = tuple(s["canonico"])
        for a in s["areas"]:
            if a in res:
                res[a][1] += s["items_del_banco"]
                if cuerpo in presentes:
                    res[a][0] += s["items_del_banco"]
    return {a: (v[0], v[1]) for a, v in res.items()}


def tabla_cobertura(resumen: dict, seed_path: Path) -> str:
    cob = cobertura_seed(resumen, seed_path)
    filas = ["| Área | Ítems en el banco | Documentos incorporados | Fragmentos | "
             "Cobertura del seed (ítems) |", "|---|---:|---:|---:|---|"]
    for a in AREAS:
        docs = [d for d in resumen["documentos"] if a in d["areas"]]
        frag = sum(d["n_fragmentos"] for d in docs)
        c, t = cob[a]
        pct = f"{c}/{t} ({c / t:.0%})" if t else "—"
        filas.append(f"| {_area_corta(a) if a == AREAS[-1] else a} | {ITEMS_POR_AREA[a]} | "
                     f"{len(docs)} | {frag} | {pct} |")
    filas.append("")
    filas.append("_Cobertura del seed_: ítems del banco (según `items_del_banco` de "
                 "`data/seed_targets.json`) cuyas normas ya están en el corpus. Es una cota "
                 "inferior: el seed no es exhaustivo.")
    return "\n".join(filas)


def reemplazar_bloque(texto: str, nombre: str, contenido: str) -> str:
    patron = re.compile(rf"(<!-- AUTO:{nombre} -->\n).*?(\n<!-- /AUTO:{nombre} -->)", re.DOTALL)
    if not patron.search(texto):
        raise ValueError(f"CORPUS.md no tiene el bloque AUTO:{nombre}")
    return patron.sub(lambda m: m.group(1) + contenido + m.group(2), texto)


def actualizar_corpus_md(ruta: Path, resumen: dict, seed_path: Path) -> None:
    texto = ruta.read_text(encoding="utf-8")
    texto = reemplazar_bloque(texto, "inventario", tabla_inventario(resumen["documentos"]))
    texto = reemplazar_bloque(texto, "totales", tabla_totales(resumen))
    texto = reemplazar_bloque(texto, "cobertura", tabla_cobertura(resumen, seed_path))
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--resumen", type=Path, default=config.corpus_out_dir / "_resumen.json")
    ap.add_argument("--manifest", type=Path, default=RAIZ / "corpus_manifest.json")
    ap.add_argument("--corpus-md", type=Path, default=RAIZ / "CORPUS.md")
    ap.add_argument("--seed", type=Path, default=RAIZ / "data" / "seed_targets.json")
    args = ap.parse_args(argv)
    if not args.resumen.is_file():
        print(f"No existe {args.resumen}; corra primero `python -m src.corpus.build`.")
        return 0
    resumen = json.loads(args.resumen.read_text(encoding="utf-8"))
    manifiesto = construir_manifiesto(resumen)
    args.manifest.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    actualizar_corpus_md(args.corpus_md, resumen, args.seed)
    print(f"{args.manifest.name}: {len(manifiesto['documentos'])} documentos; "
          f"{args.corpus_md.name} actualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
