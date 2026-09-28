"""Prueba de humo de la interfaz (FastAPI) con los modelos reales sobre el mini-corpus."""
import dataclasses

import pytest
from fastapi.testclient import TestClient

from interfaz.app import crear_app
from src.config import config


@pytest.fixture(scope="module")
def cliente(indice_prueba, tmp_path_factory):
    from src.generation.llm import LLM

    _, rec = indice_prueba
    llm = LLM(dataclasses.replace(config, decoder_num_ctx=4096))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.generation.llm.DIR_CACHE", tmp_path_factory.mktemp("gen"))
        yield TestClient(crear_app(rec=rec, llm=llm))


def test_pagina_y_estado(cliente):
    r = cliente.get("/")
    assert r.status_code == 200 and "Software Colombia" in r.text
    assert cliente.get("/static/styles.css").status_code == 200
    e = cliente.get("/api/estado").json()
    assert e["recuperador_cargado"] and len(e["areas"]) == 10


def test_recuperar(cliente):
    r = cliente.post("/api/recuperar", json={"pregunta": "¿Qué dispone el artículo 1820 del Código Civil?"})
    assert r.status_code == 200
    p = r.json()["pasajes"]
    assert p[0]["encabezado"].startswith("Código Civil, artículo 1820")


def test_mc_sin_opciones_es_422(cliente):
    r = cliente.post("/api/consulta", json={"pregunta": "¿Cuál aplica?", "formato": "multiple_choice",
                                            "opciones": {"A": "solo una"}})
    assert r.status_code == 422


def test_consulta_completa(cliente):
    r = cliente.post("/api/consulta", json={
        "pregunta": "¿Qué dispone el artículo 11 de la Ley 1150 de 2007 sobre el plazo?",
        "formato": "semi_open", "area": "administrativo"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["respuesta"]["formato"] == "semi_open" and not d["respuesta"]["abstencion"]
    assert d["pasajes"] and d["citas"]
    assert all(c["respaldada"] for c in d["citas"])          # el post-filtro no deja citas sin respaldo
    assert d["traza"]["s_total"] > 0
