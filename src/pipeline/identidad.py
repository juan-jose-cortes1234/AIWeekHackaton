"""Identidad de corrida para impedir reanudar respuestas con otro experimento."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

from src.config import RAIZ, SECRETOS, Config


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def identidad(cfg: Config, modelo: str | None = None) -> dict:
    # No leer ni serializar claves ni URLs de acceso al corpus.
    excluidos = SECRETOS | {"corpus_zip_url", "team_name"}
    parametros = {f.name: str(getattr(cfg, f.name)) if isinstance(getattr(cfg, f.name), Path)
                  else getattr(cfg, f.name) for f in dataclasses.fields(cfg)
                  if f.name not in excluidos}
    codigo = {p.relative_to(RAIZ).as_posix(): sha256_archivo(p)
              for p in sorted((RAIZ / "src").rglob("*"))
              if p.is_file() and p.suffix in {".py", ".txt"}}
    man = cfg.index_dir / "index_manifest.json"
    contenido = {"version": 1, "parametros": parametros, "decoder": modelo,
                 "codigo": codigo, "indice_manifest": sha256_archivo(man) if man.is_file() else None}
    contenido["sha256"] = hashlib.sha256(json.dumps(contenido, sort_keys=True,
                                                      ensure_ascii=False).encode("utf-8")).hexdigest()
    return contenido


def verificar_identidad(salida: Path, actual: dict, reanudar: bool) -> None:
    ruta = salida.with_suffix(".experimento.json")
    hay_respuestas = salida.is_file() and salida.stat().st_size > 0
    if reanudar and hay_respuestas:
        if not ruta.is_file():
            raise ValueError("La corrida tiene respuestas sin identidad verificable. "
                             "Use un TAG/salida nuevo para conservar las respuestas anteriores.")
        anterior = json.loads(ruta.read_text(encoding="utf-8"))
        if anterior != actual:
            raise ValueError("La configuración, código o índice cambió. Use un TAG/salida nuevo; "
                             "--no-cache no regenera IDs ya escritos.")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")
