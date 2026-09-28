"""Prueba de punta a punta del pipeline con los modelos reales sobre el mini-corpus."""
import dataclasses
import json

import jsonschema
import pytest

from src.config import RAIZ, config
from src.pipeline.main import ejecutar, esquema_oficial

PREGUNTAS = [
    {"id": 910001, "formato": "multiple_choice", "area": "Derecho civil",
     "pregunta": "Según el artículo 1820 del Código Civil, ¿qué regula esa disposición?",
     "opciones": {"A": "La sociedad conyugal", "B": "El impuesto de renta",
                  "C": "La acción de tutela", "D": "El contrato de trabajo"}},
    {"id": 910002, "formato": "semi_open", "area": "Derecho administrativo",
     "sub_tarea": "Requisitos legales",
     "pregunta": "¿Qué dispone el artículo 11 de la Ley 1150 de 2007 sobre el plazo?"},
    {"id": 910003, "formato": "semi_open", "area": "Derecho tributario",
     "sub_tarea": "Definición básica",
     "pregunta": "¿Qué tarifa tiene el impuesto al carbono para combustibles de aviación?"},
]


@pytest.fixture(scope="module")
def llm_real():
    from src.generation.llm import LLM

    return LLM(dataclasses.replace(config, decoder_num_ctx=4096))


def test_pipeline_real(indice_prueba, llm_real, tmp_path, monkeypatch):
    monkeypatch.setattr("src.generation.llm.DIR_CACHE", tmp_path / "gen")
    _, rec = indice_prueba
    salida = tmp_path / "run" / "submissions.jsonl"
    res = ejecutar(PREGUNTAS, rec, llm_real, salida, tmp_path / "run")
    assert res["respondidas_ahora"] == 3 and res["errores_esquema"] == 0

    lineas = [json.loads(l) for l in salida.read_text(encoding="utf-8").splitlines()]
    esquema = esquema_oficial()
    for l in lineas:
        jsonschema.validate(l, esquema)
        assert "pasajes_usados" not in l and len(l["pasajes_recuperados"]) <= 10
        assert isinstance(l["latencia_ms"], int)
    mc, semi, ajena = lineas
    assert mc["respuesta_correcta"] == "A" and not mc["abstencion"]
    assert not semi["abstencion"] and "Ley 1150 de 2007" in semi["referencia_legal"]
    assert ajena["abstencion"] is True and ajena["respuesta"] == ""

    # Calificación con el evaluador oficial: ninguna cita sin respaldo.
    import src.oficial  # noqa: F401
    import evaluate

    for l in lineas:
        if not l["abstencion"]:
            r = evaluate.citations.score(evaluate.answer_text(l), "",
                                         evaluate.citas_respaldadas(l))
            assert r["citas_sin_respaldo"] == 0, r["detalle"]

    trazas = [json.loads(l) for l in (tmp_path / "run" / "trazas.jsonl").read_text(
        encoding="utf-8").splitlines()]
    assert [t["id"] for t in trazas] == [910001, 910002, 910003]
    assert (tmp_path / "run" / "tiempos.json").is_file()

    # Reanudable: una segunda corrida no regenera nada.
    res2 = ejecutar(PREGUNTAS, rec, llm_real, salida, tmp_path / "run")
    assert res2["respondidas_ahora"] == 0 and res2["ya_existentes"] == 3


def test_recorta_evidencia_si_no_cabe(indice_prueba, llm_real):
    from src.generation.responder import mensajes_que_caben, recuperar

    _, rec = indice_prueba
    item = PREGUNTAS[1]
    pasajes = recuperar(item, rec)
    completo, n_completo = mensajes_que_caben(item, pasajes, llm_real)
    estrecho = dataclasses.replace(config, decoder_num_ctx=1200)
    llm_real.cfg, original = estrecho, llm_real.cfg
    try:
        msgs, n = mensajes_que_caben(item, pasajes, llm_real)
    finally:
        llm_real.cfg = original
    assert n < n_completo
    assert llm_real.contar_tokens(msgs) <= 1200 - 400
