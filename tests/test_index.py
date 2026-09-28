"""Pruebas del índice con el encoder real configurado (bge-m3)."""
import json

import numpy as np
import pytest

from src.corpus.build import construir
from src.index.build import construir_indice
from src.index.encoder import CacheEmbeddings


@pytest.fixture
def indice(corpus_crudo, tmp_path, monkeypatch):
    monkeypatch.setattr("src.index.encoder.DIR_CACHE", tmp_path / "cache")
    salida = tmp_path / "build"
    construir(corpus_crudo, salida)
    return salida


def test_construye_y_recupera(indice, encoder_real):
    import faiss

    m = construir_indice(indice / "indice", enc=encoder_real, dir_corpus=indice / "corpus")
    chunks = [json.loads(l) for l in (indice / "indice" / "chunks.jsonl").read_text(
        encoding="utf-8").splitlines()]
    assert m["n_fragmentos"] == len(chunks) and m["dimension"] == encoder_real.dimension
    assert m["modelo"] == encoder_real.nombre
    assert m["tipo_indice"] == "IndexFlatIP" and len(m["sha256_faiss"]) == 64

    idx = faiss.read_index(str(indice / "indice" / "index.faiss"))
    assert idx.ntotal == len(chunks)
    objetivo = next(i for i, c in enumerate(chunks) if c["articulo"] == "1820")
    q = encoder_real.codificar([chunks[objetivo]["texto"]], es_consulta=True)
    _, ids = idx.search(q, 1)
    assert ids[0][0] == objetivo


def test_idempotente_y_cache(indice, encoder_real):
    m1 = construir_indice(indice / "indice", enc=encoder_real, dir_corpus=indice / "corpus")
    assert m1["embeddings_calculados"] == m1["n_fragmentos"]
    m2 = construir_indice(indice / "indice", enc=encoder_real, dir_corpus=indice / "corpus")
    assert m2["reutilizado"]                                   # nada cambió → no recalcula
    m3 = construir_indice(indice / "indice", enc=encoder_real, forzar=True,
                          dir_corpus=indice / "corpus")
    assert not m3["reutilizado"] and m3["embeddings_calculados"] == 0   # todo desde la caché


def test_cache_persistente(tmp_path, encoder_real):
    c = CacheEmbeddings(encoder_real.nombre, tmp_path)
    v1, n1 = c.codificar_pasajes(encoder_real, ["texto uno", "texto dos", "texto uno"])
    assert n1 == 2 and v1.shape == (3, encoder_real.dimension) and np.allclose(v1[0], v1[2])
    c.guardar()
    c2 = CacheEmbeddings(encoder_real.nombre, tmp_path)
    v2, n2 = c2.codificar_pasajes(encoder_real, ["texto dos", "texto tres"])
    assert n2 == 1 and np.allclose(v2[0], v1[1])


def test_se_niega_con_fuga(indice, encoder_real):
    (indice / "corpus" / "_fuga.json").write_text(json.dumps({"graves": ["x"]}), encoding="utf-8")
    with pytest.raises(SystemExit):
        construir_indice(indice / "indice", enc=encoder_real, dir_corpus=indice / "corpus")


def test_prefijos_e5():
    from src.index.encoder import EncoderST

    e = EncoderST.__new__(EncoderST)
    e.nombre = "intfloat/multilingual-e5-large"
    assert e._prefijar(["x"], True) == ["query: x"]
    assert e._prefijar(["x"], False) == ["passage: x"]
    e.nombre = "BAAI/bge-m3"
    assert e._prefijar(["x"], True) == ["x"]
