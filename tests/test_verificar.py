"""Pruebas del simulacro de verificación en vivo y del chequeo final de la entrega."""
import copy
import dataclasses
import json

import pytest

from src.config import config
from src.eval.validar_entrega import validar
from src.eval.verificar import comparar, verificar
from src.pipeline.main import ejecutar

PREG = [{"id": 920001, "formato": "semi_open", "area": "Derecho administrativo",
         "sub_tarea": "Requisitos legales",
         "pregunta": "¿Qué dispone el artículo 11 de la Ley 1150 de 2007 sobre el plazo?"}]


def _linea():
    return {"id": 1, "formato": "semi_open", "abstencion": False,
            "respuesta": "Aplica el artículo 11 de la Ley 1150 de 2007.", "palabras_clave": ["plazo"],
            "referencia_legal": "Ley 1150 de 2007, artículo 11",
            "pasajes_recuperados": [{"doc_id": "d", "inicio": 0, "fin": 10, "texto": "Ley 1150 de 2007.",
                                     "score": 0.9}]}


def test_comparar_detecta_diferencias():
    a = _linea()
    assert comparar(a, copy.deepcopy(a))["ok"]
    b = copy.deepcopy(a)
    b["respuesta"] = "Aplica la redacción distinta del artículo 11 de la Ley 1150 de 2007."
    assert comparar(a, b)["ok"]                         # cambia la redacción, no las normas
    c = copy.deepcopy(a)
    c["referencia_legal"] = "Ley 80 de 1993"
    r = comparar(a, c)
    assert not r["ok"] and not r["normas_iguales"]
    d = copy.deepcopy(a)
    d["pasajes_recuperados"][0]["inicio"] = 5
    assert not comparar(a, d)["pasajes_iguales"]


def test_validar_entrega(tmp_path):
    preg = tmp_path / "p.jsonl"
    preg.write_text("\n".join(json.dumps({"id": i, "formato": "semi_open"}) for i in (1, 2)),
                    encoding="utf-8")
    ent = tmp_path / "e.jsonl"
    ent.write_text(json.dumps(_linea()) + "\n", encoding="utf-8")
    r = validar(ent, preg)
    assert not r["ok"] and any("sin respuesta" in e for e in r["errores"])
    dos = _linea() | {"id": 2}
    ent.write_text(json.dumps(_linea()) + "\n" + json.dumps(dos) + "\n", encoding="utf-8")
    assert validar(ent, preg)["ok"]


@pytest.fixture(scope="module")
def llm_real():
    from src.generation.llm import LLM

    return LLM(dataclasses.replace(config, decoder_num_ctx=4096))


def test_simulacro_real(indice_prueba, llm_real, tmp_path, monkeypatch):
    monkeypatch.setattr("src.generation.llm.DIR_CACHE", tmp_path / "gen")
    _, rec = indice_prueba
    preguntas = tmp_path / "preguntas.jsonl"
    preguntas.write_text(json.dumps(PREG[0], ensure_ascii=False) + "\n", encoding="utf-8")
    entrega = tmp_path / "submissions.jsonl"
    ejecutar(PREG, rec, llm_real, entrega, tmp_path)
    res = verificar([920001], entrega, preguntas, rec, llm_real)     # regenera sin caché
    assert res[0]["ok"], res
