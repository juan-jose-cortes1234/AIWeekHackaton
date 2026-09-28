"""Empaqueta corpus e índice para publicarlos: `python -m src.corpus.empaquetar`.

Produce `dist/corpus_<equipo>.zip` con la estructura oficial
(entregables/sabado/README.md):

    LICENSE                  CC-BY-4.0 (texto legal completo, docs/LICENSE-CORPUS-CC-BY-4.0.txt)
    corpus_manifest.json     copia del manifiesto del repositorio
    corpus/<doc_id>.txt      documentos procesados
    indice/                  index.faiss, chunks.jsonl, index_manifest.json, bm25/

El zip es **determinista** (entradas ordenadas y fechas fijas): mismo corpus e
índice ⇒ mismo sha256, lo que sirve para congelar el índice. Imprime las dos
líneas para `.env`. Subirlo a la nube lo hace el equipo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from src.config import RAIZ, Config, config
from src.index.build import sha256_archivo

LICENCIA = RAIZ / "docs" / "LICENSE-CORPUS-CC-BY-4.0.txt"
FECHA_FIJA = (1980, 1, 1, 0, 0, 0)
EXCLUIR_INDICE = {".origen_nube.json", "corpus_manifest.json"}


class ErrorEmpaquetado(Exception):
    pass


def _verificar(cfg: Config, manifiesto: Path) -> dict:
    idx = cfg.index_dir
    for req in ("index.faiss", "chunks.jsonl", "index_manifest.json"):
        if not (idx / req).is_file():
            raise ErrorEmpaquetado(f"Falta {idx / req}: construya el índice (python -m src.index.build).")
    if not (idx / "bm25").is_dir():
        raise ErrorEmpaquetado("Falta el índice BM25 (python -m src.index.build).")
    if not list(cfg.corpus_out_dir.glob("*.txt")):
        raise ErrorEmpaquetado(f"No hay documentos en {cfg.corpus_out_dir} (python -m src.corpus.build).")
    if not manifiesto.is_file():
        raise ErrorEmpaquetado(f"Falta {manifiesto.name} (python -m src.corpus.manifest).")
    fuga = cfg.corpus_out_dir / "_fuga.json"
    if fuga.is_file() and json.loads(fuga.read_text(encoding="utf-8")).get("graves"):
        raise ErrorEmpaquetado("La guardia anti-fuga reportó problemas graves: no se publica.")
    man = json.loads((idx / "index_manifest.json").read_text(encoding="utf-8"))
    if man.get("sha256_chunks") != sha256_archivo(idx / "chunks.jsonl"):
        raise ErrorEmpaquetado("El índice está desactualizado respecto a chunks.jsonl: "
                               "reconstruya con python -m src.index.build.")
    if man.get("sha256_faiss") != sha256_archivo(idx / "index.faiss"):
        raise ErrorEmpaquetado("index.faiss no coincide con index_manifest.json.")
    return man


def _escribir(z: zipfile.ZipFile, nombre: str, datos: bytes) -> None:
    info = zipfile.ZipInfo(nombre, date_time=FECHA_FIJA)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, datos)


def empaquetar(cfg: Config = config, destino: Path | None = None,
               manifiesto: Path | None = None) -> dict:
    manifiesto = manifiesto or RAIZ / "corpus_manifest.json"
    man = _verificar(cfg, manifiesto)
    equipo = re.sub(r"[^a-z0-9]+", "_", (cfg.team_name or "equipo").lower()).strip("_") or "equipo"
    destino = destino or RAIZ / "dist" / f"corpus_{equipo}.zip"
    destino.parent.mkdir(parents=True, exist_ok=True)

    entradas: list[tuple[str, Path]] = [("LICENSE", LICENCIA), ("corpus_manifest.json", manifiesto)]
    entradas += [(f"corpus/{p.name}", p) for p in cfg.corpus_out_dir.glob("*.txt")]
    entradas += [(f"indice/{p.relative_to(cfg.index_dir).as_posix()}", p)
                 for p in cfg.index_dir.rglob("*")
                 if p.is_file() and p.name not in EXCLUIR_INDICE]
    entradas.sort(key=lambda e: e[0])

    tmp = destino.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w") as z:
        for nombre, ruta in entradas:
            _escribir(z, nombre, ruta.read_bytes())
    tmp.replace(destino)
    digest = hashlib.sha256(destino.read_bytes()).hexdigest()
    return {"zip": destino, "sha256": digest, "bytes": destino.stat().st_size,
            "archivos": len(entradas), "n_fragmentos": man.get("n_fragmentos"),
            "modelo": man.get("modelo")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    try:
        r = empaquetar(destino=args.out)
    except ErrorEmpaquetado as e:
        print(f"ERROR: {e}")
        return 1
    print(f"{r['zip']}  ({r['bytes'] / 1e6:.1f} MB, {r['archivos']} archivos, "
          f"{r['n_fragmentos']} fragmentos, encoder {r['modelo']})")
    print(f"sha256: {r['sha256']}\n")
    print("1. Suba el zip a la nube con acceso público de lectura (sin inicio de sesión).")
    print("2. Pegue en .env (y en el README, sección 'Corpus e índice'):")
    print("   CORPUS_ZIP_URL=<enlace público del zip>")
    print(f"   CORPUS_ZIP_SHA256={r['sha256']}")
    print("3. Verifique desde una sesión privada del navegador y con: python -m src.corpus.nube --forzar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
