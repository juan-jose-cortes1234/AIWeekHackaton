"""Pruebas del corpus desde la nube con un servidor HTTP local y el índice real del mini-corpus."""
import dataclasses
import functools
import hashlib
import http.server
import threading
import zipfile

import pytest

from src.config import config
from src.corpus.nube import ErrorNube, enlace_directo, id_google_drive, obtener
from src.retrieval.hibrido import Recuperador


def test_enlaces_de_compartir():
    assert id_google_drive("https://drive.google.com/file/d/1AbC-xyz_9/view?usp=sharing") == "1AbC-xyz_9"
    assert id_google_drive("https://drive.google.com/open?id=QWE123") == "QWE123"
    assert enlace_directo("https://www.dropbox.com/s/abc/corpus.zip?dl=0").endswith("dl=1")
    assert "download=1" in enlace_directo(
        "https://uniandes-my.sharepoint.com/:u:/g/personal/x/EAbc?e=123")
    assert enlace_directo("https://zenodo.org/records/1/files/c.zip").endswith("download=1")
    assert enlace_directo("https://ejemplo.org/c.zip") == "https://ejemplo.org/c.zip"


def _zip(build, destino, raiz="corpus_equipo/", omitir=()):
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(raiz + "LICENSE", "CC-BY-4.0")
        z.writestr(raiz + "corpus_manifest.json", "{}")
        for sub in ("corpus", "indice"):
            for p in (build / sub).rglob("*"):
                rel = f"{sub}/{p.relative_to(build / sub).as_posix()}"
                if p.is_file() and rel not in omitir:
                    z.write(p, raiz + rel)
    return hashlib.sha256(destino.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("web")
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(raiz))
    manejador.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield raiz, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _cfg(tmp_path, url, sha=""):
    return dataclasses.replace(config, corpus_zip_url=url, corpus_zip_sha256=sha,
                               corpus_out_dir=tmp_path / "b" / "corpus",
                               index_dir=tmp_path / "b" / "indice")


def test_ida_y_vuelta(indice_prueba, servidor, tmp_path, encoder_real, reranker_real):
    build, rec = indice_prueba
    web, base = servidor
    digest = _zip(build, web / "corpus.zip")
    cfg = _cfg(tmp_path, f"{base}/corpus.zip", digest)

    info = obtener(cfg, dir_descargas=tmp_path / "dl")
    assert info["sha256"] == digest and info["verificado"] and not info["reutilizado"]
    assert (cfg.index_dir / "index.faiss").is_file() and list(cfg.corpus_out_dir.glob("*.txt"))
    assert obtener(cfg, dir_descargas=tmp_path / "dl")["reutilizado"]

    rec2 = Recuperador.cargar(cfg.index_dir, encoder=encoder_real, reranker=reranker_real)
    q = "¿Qué dispone el artículo 11 de la Ley 1150 de 2007?"
    assert [(p.chunk_id, p.score) for p in rec2.buscar(q)] == \
           [(p.chunk_id, p.score) for p in rec.buscar(q)]


def test_hash_distinto_se_rechaza(indice_prueba, servidor, tmp_path):
    build, _ = indice_prueba
    web, base = servidor
    _zip(build, web / "otro.zip")
    with pytest.raises(ErrorNube, match="sha256"):
        obtener(_cfg(tmp_path, f"{base}/otro.zip", "0" * 64), dir_descargas=tmp_path / "dl")


def test_estructura_incompleta_se_rechaza(indice_prueba, servidor, tmp_path):
    build, _ = indice_prueba
    web, base = servidor
    _zip(build, web / "incompleto.zip", raiz="", omitir=("indice/index.faiss",))
    with pytest.raises(ErrorNube, match="index.faiss"):
        obtener(_cfg(tmp_path, f"{base}/incompleto.zip"), dir_descargas=tmp_path / "dl")


def test_sin_enlace(tmp_path):
    with pytest.raises(ErrorNube, match="CORPUS_ZIP_URL"):
        obtener(_cfg(tmp_path, ""))


def test_enlace_que_devuelve_html(servidor, tmp_path):
    web, base = servidor
    (web / "login.html").write_text("<html>inicie sesión</html>", encoding="utf-8")
    with pytest.raises(ErrorNube, match="página web"):
        obtener(_cfg(tmp_path, f"{base}/login.html"), dir_descargas=tmp_path / "dl")
