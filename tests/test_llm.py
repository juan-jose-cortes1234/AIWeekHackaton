"""Pruebas del decoder real (Qwen3-8B GGUF vía llama-cpp-python) y del parser JSON."""
import dataclasses

import pytest

from src.config import config
from src.generation.llm import LLM, extraer_json


@pytest.mark.parametrize("texto,esperado", [
    ('{"a": 1}', {"a": 1}),
    ('```json\n{"a": "x}"}\n```', {"a": "x}"}),
    ('<think>pienso {no json}</think>\nRespuesta: {"b": [1, 2]} fin', {"b": [1, 2]}),
    ('texto {roto y luego {"c": true}', {"c": True}),
    ("sin json", None),
])
def test_extraer_json(texto, esperado):
    assert extraer_json(texto) == esperado


@pytest.fixture(scope="session")
def llm_real():
    cfg = dataclasses.replace(config, decoder_backend="llamacpp", decoder_num_ctx=2048)
    return LLM(cfg)


ESQUEMA = {"type": "object",
           "properties": {"respuesta_correcta": {"type": "string", "enum": ["A", "B", "C", "D"]},
                          "justificacion": {"type": "string"}},
           "required": ["respuesta_correcta", "justificacion"]}

MENSAJES = [
    {"role": "system", "content": "Respondes en español y solo en JSON."},
    {"role": "user", "content": "¿Cuánto es 2 + 2? Opciones: A) 3  B) 4  C) 5  D) 22. "
                                "Devuelve respuesta_correcta y una justificacion de una frase."},
]


def test_json_forzado_y_determinista(llm_real, tmp_path):
    g1 = llm_real.generar(MENSAJES, esquema=ESQUEMA, max_tokens=80, usar_cache=False,
                          dir_cache=tmp_path)
    assert g1.datos and g1.datos["respuesta_correcta"] in "ABCD"
    assert g1.datos["respuesta_correcta"] == "B"
    g2 = llm_real.generar(MENSAJES, esquema=ESQUEMA, max_tokens=80, usar_cache=False,
                          dir_cache=tmp_path)
    assert g2.texto == g1.texto                       # temperatura 0 → misma salida


def test_cache(llm_real, tmp_path):
    g1 = llm_real.generar(MENSAJES, esquema=ESQUEMA, max_tokens=80, dir_cache=tmp_path)
    g2 = llm_real.generar(MENSAJES, esquema=ESQUEMA, max_tokens=80, dir_cache=tmp_path)
    assert not g1.desde_cache and g2.desde_cache and g2.texto == g1.texto


def test_rechaza_modelo_fuera_de_lista_blanca():
    cfg = dataclasses.replace(config, decoder_gguf_repo="openai/gpt-oss")
    with pytest.raises(ValueError):
        LLM(cfg)


@pytest.mark.parametrize("texto,esperado", [
    ('{"marco_normativo": "Ley 1 de 2000.", "analisis": "Primera oración. Segunda sin termi',
     {"marco_normativo": "Ley 1 de 2000."}),
    ('{"a": "x", "b": [1, 2', {"a": "x"}),
    ('{"a": "x", "b": "y"}', {"a": "x", "b": "y"}),
    ('{"a": "sin cerrar', None),
    ('texto sin json', None),
    ('{"a": "con \\"comillas\\" dentro", "b": "cor', {"a": 'con "comillas" dentro'}),
])
def test_reparar_json_truncado(texto, esperado):
    from src.generation.llm import reparar_json_truncado

    assert reparar_json_truncado(texto) == esperado


def test_salida_cortada_se_rescata_sin_reintentar(llm_real, tmp_path):
    esquema = {"type": "object",
               "properties": {"marco_normativo": {"type": "string"}, "analisis": {"type": "string"},
                              "conclusion": {"type": "string"}},
               "required": ["marco_normativo", "analisis", "conclusion"]}
    msgs = [{"role": "system", "content": "Respondes en español y solo en JSON."},
            {"role": "user", "content": "Escribe un marco_normativo de una frase sobre el contrato "
                                        "de compraventa, luego un analisis MUY extenso de al menos "
                                        "30 oraciones y una conclusion."}]
    g = llm_real.generar(msgs, esquema=esquema, max_tokens=120, usar_cache=False, dir_cache=tmp_path)
    assert g.truncada
    assert g.tokens_salida <= 125                    # sin reintento: no se duplican los tokens
    assert g.datos and g.datos.get("marco_normativo")
