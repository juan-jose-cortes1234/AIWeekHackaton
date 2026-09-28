"""Construye el corpus procesado: `python -m src.corpus.build [--dir RAW] [--out BUILD]`.

Salidas:
- `<out>/corpus/<doc_id>.txt`: fragmentos en orden, cada uno con su encabezado,
  separados por una línea en blanco.
- `<out>/indice/chunks.jsonl`: un fragmento por línea con `doc_id`, `inicio`,
  `fin` (offsets en el .txt; `texto == txt[inicio:fin]`) y metadatos.
- `<out>/corpus/_resumen.json`: estadísticas por documento para el manifiesto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from src.config import RAIZ, config
from src.corpus import fuga
from src.corpus.extraer import extraer
from src.corpus.fragmentar import cuerpos, cuerpos_documento, fragmentar, nombre_canonico
from src.corpus.fuentes import Fuente, validar
from src.corpus.segmentar import segmentar

SEPARADOR = "\n\n"


def construir_documento(f: Fuente, dir_corpus: Path) -> tuple[list[dict], dict]:
    """Procesa una fuente; devuelve sus filas de chunks.jsonl y su resumen."""
    ext = extraer(f.archivo)
    segs = segmentar(ext.texto, f.tipo)
    frags = fragmentar(f, segs)
    esperados = cuerpos_documento(f)
    avisos = list(ext.avisos)
    if not esperados:
        avisos.append(f"el nombre '{nombre_canonico(f)}' no produce una cita que el evaluador "
                      "reconozca: sus pasajes no servirán de respaldo")

    partes, filas, pos = [], [], 0
    sin_cuerpo = 0
    for n, fr in enumerate(frags):
        inicio = pos
        fin = inicio + len(fr.texto)
        partes.append(fr.texto)
        pos = fin + len(SEPARADOR)
        c = cuerpos(fr.texto)
        if esperados and not (esperados & c):
            sin_cuerpo += 1
        filas.append({
            "chunk_id": f"{f.doc_id}#{n:05d}", "doc_id": f.doc_id, "inicio": inicio, "fin": fin,
            "texto": fr.texto, "tipo_fragmento": fr.tipo_fragmento, "articulo": fr.articulo,
            "seccion": fr.seccion, "parte": fr.parte, "partes": fr.partes,
            "tipo_norma": f.tipo, "numero": f.numero or None, "anio": f.anio or None,
            "titulo": f.titulo, "nombre_canonico": nombre_canonico(f), "organo": f.organo_emisor,
            "vigencia": f.vigencia or None, "areas": f.areas, "url": f.url,
            "cuerpos": sorted(list(x) for x in c),
        })
    if sin_cuerpo:
        avisos.append(f"{sin_cuerpo} fragmentos sin el cuerpo normativo del documento")

    contenido = SEPARADOR.join(partes) + ("\n" if partes else "")
    ruta = dir_corpus / f"{f.doc_id}.txt"
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    resumen = {
        "doc_id": f.doc_id, "titulo": f.titulo, "nombre_canonico": nombre_canonico(f),
        "tipo": f.tipo, "fuente": f.fuente, "url": f.url, "fecha_consulta": f.fecha_consulta,
        "areas": f.areas, "vigencia": f.vigencia or None,
        "n_articulos": len({s.articulo for s in segs if s.tipo == "articulo"}) or None,
        "n_fragmentos": len(frags), "n_caracteres": len(contenido),
        "sha256": hashlib.sha256(contenido.encode("utf-8")).hexdigest(),
        "formatos": sorted({a.suffix.lower().lstrip(".") for a in ext.archivos}),
        "n_archivos": len(ext.archivos),
        "cuerpos": sorted(list(x) for x in esperados), "avisos": avisos,
    }
    return filas, resumen


def construir(raiz: Path, salida: Path) -> dict:
    res = validar(raiz)
    if not res.ok:
        raise SystemExit("fuentes.csv tiene errores; corra `python -m src.corpus.validar`.\n"
                         + "\n".join(res.errores[:20]))
    dir_corpus, dir_indice = salida / "corpus", salida / "indice"
    dir_corpus.mkdir(parents=True, exist_ok=True)
    dir_indice.mkdir(parents=True, exist_ok=True)
    for viejo in dir_corpus.glob("*.txt"):
        viejo.unlink()   # artefacto generado: se reconstruye completo

    todas, resumenes = [], []
    for f in res.fuentes:
        filas, resumen = construir_documento(f, dir_corpus)
        todas.extend(filas)
        resumenes.append(resumen)

    with (dir_indice / "chunks.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for fila in todas:
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
    total = {"documentos": resumenes, "n_documentos": len(resumenes),
             "n_fragmentos": len(todas), "avisos_fuentes": res.avisos}
    (dir_corpus / "_resumen.json").write_text(
        json.dumps(total, ensure_ascii=False, indent=2), encoding="utf-8")
    return total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=config.corpus_raw_dir)
    ap.add_argument("--out", type=Path, default=RAIZ / "build")
    args = ap.parse_args(argv)
    if not (args.dir / "fuentes.csv").is_file():
        print(f"No hay fuentes.csv en {args.dir}. Ver GUIA_CORPUS.md §3.")
        return 0
    total = construir(args.dir, args.out)
    print(f"{'doc_id':40} {'artículos':>9} {'fragmentos':>10}  avisos")
    for d in total["documentos"]:
        print(f"{d['doc_id']:40} {str(d['n_articulos'] or '-'):>9} {d['n_fragmentos']:>10}  "
              + "; ".join(d["avisos"]))
    print(f"\n{total['n_documentos']} documentos, {total['n_fragmentos']} fragmentos → {args.out}")

    inf = fuga.revisar(args.out / "indice" / "chunks.jsonl", args.dir,
                       [RAIZ / "data" / "sample_50.jsonl"])
    (args.out / "corpus" / "_fuga.json").write_text(
        json.dumps({"graves": inf.graves, "revision": inf.revision}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    if inf.revision:
        print(f"Guardia anti-fuga: {len(inf.revision)} coincidencias menores para revisar "
              f"(build/corpus/_fuga.json).")
    if not inf.ok:
        print("GUARDIA ANTI-FUGA: el corpus contiene material de preguntas/respuestas. "
              "No se debe indexar:")
        for m in inf.graves:
            print(f"  {m}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
