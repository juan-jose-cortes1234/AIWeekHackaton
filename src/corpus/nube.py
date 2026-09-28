"""Corpus e índice desde la nube: `python -m src.corpus.nube [--forzar]` (ARQUITECTURA §1.1).

Descarga el zip publicado en `CORPUS_ZIP_URL` (Google Drive, OneDrive/SharePoint,
Dropbox, Zenodo o URL directa), verifica `CORPUS_ZIP_SHA256`, valida la
estructura oficial y lo descomprime en `CORPUS_OUT_DIR` e `INDEX_DIR`. Con esto
el sistema consume **solo** el corpus publicado: conectarlo es llenar esas dos
variables en `.env`.

Estructura esperada del zip (entregables/sabado/README.md), con o sin una
carpeta raíz:
    LICENSE · corpus_manifest.json · corpus/*.txt ·
    indice/{index.faiss, chunks.jsonl, index_manifest.json, bm25/}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from src.config import RAIZ, Config, config

DIR_DESCARGAS = RAIZ / "build" / "descargas"
OBLIGATORIOS = ("LICENSE", "corpus_manifest.json", "indice/index.faiss", "indice/chunks.jsonl",
                "indice/index_manifest.json")
MARCA = ".origen_nube.json"


class ErrorNube(Exception):
    pass


# --------------------------------------------------------------------------- enlaces

def id_google_drive(url: str) -> str | None:
    m = re.search(r"drive\.google\.com/file/d/([\w-]+)", url) or \
        re.search(r"drive\.google\.com/(?:open|uc)\?(?:.*&)?id=([\w-]+)", url)
    return m.group(1) if m else None


def enlace_directo(url: str) -> str:
    """Convierte enlaces de compartir en enlaces de descarga directa."""
    p = urlparse(url)
    q = parse_qs(p.query)
    host = p.netloc.lower()
    if "dropbox.com" in host:
        q["dl"] = ["1"]
    elif "sharepoint.com" in host or "onedrive.live.com" in host or host == "1drv.ms":
        q["download"] = ["1"]
    elif "zenodo.org" in host and "/files/" in p.path:
        q["download"] = ["1"]
    else:
        return url
    return urlunparse(p._replace(query=urlencode({k: v[0] for k, v in q.items()})))


# --------------------------------------------------------------------------- descarga

def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def descargar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    gid = id_google_drive(url)
    if gid:
        import gdown

        if gdown.download(id=gid, output=str(destino), quiet=False, resume=True) is None:
            raise ErrorNube("Google Drive no entregó el archivo (¿enlace público?).")
        return destino

    import httpx
    from tqdm import tqdm

    parcial = destino.with_suffix(destino.suffix + ".part")
    inicio = parcial.stat().st_size if parcial.exists() else 0
    cabeceras = {"Range": f"bytes={inicio}-"} if inicio else {}
    with httpx.stream("GET", enlace_directo(url), headers=cabeceras, follow_redirects=True,
                      timeout=httpx.Timeout(60.0, read=300.0)) as r:
        if r.status_code == 416:                       # ya estaba completo
            parcial.rename(destino)
            return destino
        if r.status_code >= 400:
            raise ErrorNube(f"Descarga fallida: HTTP {r.status_code} ({url})")
        tipo = r.headers.get("content-type", "")
        if "text/html" in tipo:
            raise ErrorNube("El enlace devolvió una página web, no el zip: verifique que la "
                            "descarga sea pública y sin inicio de sesión.")
        modo = "ab" if (inicio and r.status_code == 206) else "wb"
        total = int(r.headers.get("content-length", 0)) + (inicio if modo == "ab" else 0)
        with parcial.open(modo) as fh, tqdm(total=total or None, initial=inicio if modo == "ab" else 0,
                                            unit="B", unit_scale=True, desc="corpus") as barra:
            for bloque in r.iter_bytes(1 << 20):
                fh.write(bloque)
                barra.update(len(bloque))
    parcial.replace(destino)
    return destino


# --------------------------------------------------------------------------- validación

def _prefijo(nombres: list[str]) -> str:
    """Carpeta raíz común del zip (p. ej. 'corpus_equipo/'), o ''."""
    if any(n.rstrip("/") == "LICENSE" or n == "corpus_manifest.json" for n in nombres):
        return ""
    raices = {n.split("/", 1)[0] for n in nombres if "/" in n}
    return f"{raices.pop()}/" if len(raices) == 1 else ""


def validar_zip(ruta: Path, cfg: Config = config) -> str:
    """Comprueba la estructura y el encoder del índice; devuelve el prefijo interno."""
    with zipfile.ZipFile(ruta) as z:
        nombres = z.namelist()
        pre = _prefijo(nombres)
        faltan = [o for o in OBLIGATORIOS if pre + o not in nombres]
        if not any(n.startswith(pre + "corpus/") and n.endswith(".txt") for n in nombres):
            faltan.append("corpus/*.txt")
        if not any(n.startswith(pre + "indice/bm25/") for n in nombres):
            faltan.append("indice/bm25/")
        if faltan:
            raise ErrorNube(f"Al zip le faltan: {faltan}")
        man = json.loads(z.read(pre + "indice/index_manifest.json"))
    if man.get("modelo") != cfg.encoder_model:
        raise ErrorNube(f"El índice del zip se construyó con {man.get('modelo')} y ENCODER_MODEL "
                        f"es {cfg.encoder_model}.")
    return pre


def extraer(ruta: Path, pre: str, cfg: Config = config) -> None:
    for d in (cfg.corpus_out_dir, cfg.index_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    with zipfile.ZipFile(ruta) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.startswith(pre):
                continue
            rel = info.filename[len(pre):]
            if rel.startswith("corpus/"):
                dest = cfg.corpus_out_dir / rel[len("corpus/"):]
            elif rel.startswith("indice/"):
                dest = cfg.index_dir / rel[len("indice/"):]
            elif rel == "corpus_manifest.json":
                dest = cfg.index_dir / "corpus_manifest.json"
            else:
                continue
            if ".." in Path(rel).parts:
                raise ErrorNube(f"Ruta insegura en el zip: {info.filename}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, dest.open("wb") as dst:
                shutil.copyfileobj(src, dst)


# --------------------------------------------------------------------------- flujo

def obtener(cfg: Config = config, forzar: bool = False, dir_descargas: Path | None = None) -> dict:
    if not cfg.corpus_zip_url:
        raise ErrorNube("CORPUS_ZIP_URL está vacío en .env. Pegue el enlace público del zip "
                        "(y CORPUS_ZIP_SHA256, que imprime `python -m src.corpus.empaquetar`).")
    marca = cfg.index_dir / MARCA
    if not forzar and marca.is_file():
        previo = json.loads(marca.read_text(encoding="utf-8"))
        if previo.get("url") == cfg.corpus_zip_url and \
                (not cfg.corpus_zip_sha256 or previo.get("sha256") == cfg.corpus_zip_sha256):
            return previo | {"reutilizado": True}

    zip_path = (dir_descargas or DIR_DESCARGAS) / "corpus.zip"
    if forzar or not zip_path.is_file() or (cfg.corpus_zip_sha256 and
                                            sha256(zip_path) != cfg.corpus_zip_sha256):
        if zip_path.exists():
            zip_path.unlink()
        descargar(cfg.corpus_zip_url, zip_path)
    digest = sha256(zip_path)
    if cfg.corpus_zip_sha256 and digest != cfg.corpus_zip_sha256:
        raise ErrorNube(f"sha256 no coincide: esperado {cfg.corpus_zip_sha256}, obtenido {digest}. "
                        "El índice del sábado está congelado: no se usa un zip distinto.")
    pre = validar_zip(zip_path, cfg)
    extraer(zip_path, pre, cfg)
    info = {"url": cfg.corpus_zip_url, "sha256": digest, "verificado": bool(cfg.corpus_zip_sha256)}
    marca.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info | {"reutilizado": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--forzar", action="store_true", help="descarga y extrae de nuevo")
    args = ap.parse_args(argv)
    try:
        info = obtener(forzar=args.forzar)
    except ErrorNube as e:
        print(f"ERROR: {e}")
        return 1
    estado = "ya estaba descargado" if info["reutilizado"] else "descargado y extraído"
    aviso = "" if info["verificado"] else " (AVISO: sin CORPUS_ZIP_SHA256, no se verificó el hash)"
    print(f"Corpus e índice {estado}: sha256 {info['sha256']}{aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
