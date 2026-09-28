"""Pruebas de prompts, esquemas y de una respuesta real de punta a punta (bge-m3 + reranker + Qwen3-8B)."""
import dataclasses

import pytest

from src.config import config
from src.generation.contexto import esquema, mensajes, recortar
from src.generation.responder import consultas_extra, responder
from src.retrieval.hibrido import Pasaje

MC = {"id": 900001, "formato": "multiple_choice", "area": "Derecho civil",
      "pregunta": "Según el artículo 1820 del Código Civil, ¿qué regula esa disposición?",
      "opciones": {"A": "La sociedad conyugal", "B": "El impuesto de renta",
                   "C": "La acción de tutela", "D": "El contrato de trabajo"}}
SEMI = {"id": 900002, "formato": "semi_open", "area": "Derecho procesal",
        "sub_tarea": "Definición básica", "pregunta": "¿Qué es la inmediación en el proceso?"}
ABIERTA = {"id": 900003, "formato": "open_ended", "area": "Derecho administrativo",
           "pregunta": "Una entidad no liquidó un contrato. ¿Qué plazo aplica?"}


def _pasaje(n, texto):
    return Pasaje(id=n, chunk_id=f"d#{n}", doc_id="d", inicio=0, fin=len(texto), texto=texto,
                  score=1.0)


def test_sin_recorte_por_defecto():
    t = "Ley 1150 de 2007, artículo 11.\n" + " ".join(f"w{i}" for i in range(500))
    assert config.palabras_por_pasaje == 0
    assert recortar(t, 0) == t


def test_recortar_conserva_encabezado():
    t = "Ley 1150 de 2007, artículo 11.\n" + " ".join(f"w{i}" for i in range(500))
    r = recortar(t, 50)
    assert r.startswith("Ley 1150 de 2007, artículo 11.\n") and r.endswith("[…]")
    assert len(r.split("\n", 1)[1].split()) == 51


def test_mensajes_mc_numerados_y_con_opciones():
    pasajes = [_pasaje(i, f"Código Civil, artículo {i}.\nTEXTO DE PRUEBA {i}") for i in range(1, 13)]
    m = mensajes(MC, pasajes)
    assert m[0]["role"] == "system" and m[1]["role"] == "user"
    u = m[1]["content"]
    assert "[P1] Código Civil, artículo 1." in u and f"[P{config.pasajes_prompt}]" in u
    assert f"[P{config.pasajes_prompt + 1}]" not in u
    assert "A) La sociedad conyugal" in u and "D) El contrato de trabajo" in u
    assert not any(f"{{{c}}}" in u for c in ("evidencia", "opciones", "pregunta", "area"))


@pytest.mark.parametrize("item,claves", [
    (MC, {"respuesta_correcta", "justificacion", "descarte_opciones", "pasajes_usados"}),
    (SEMI, {"respuesta", "palabras_clave", "referencia_legal", "pasajes_usados"}),
    (ABIERTA, {"marco_normativo", "analisis", "jurisprudencia", "conclusion", "pasajes_usados"}),
])
def test_esquemas_con_claves_del_evaluador(item, claves):
    e = esquema(item)
    assert set(e["required"]) == claves
    assert "(no se recuperó evidencia)" in mensajes(item, [])[1]["content"]
    if item is MC:
        assert e["properties"]["respuesta_correcta"]["enum"] == ["A", "B", "C", "D"]


def test_consultas_extra_mc():
    extra = consultas_extra(MC)
    assert len(extra) == 4 and all(e.startswith(MC["pregunta"]) for e in extra)
    assert consultas_extra(SEMI) == []


@pytest.fixture(scope="module")
def llm_pequeno_ctx():
    from src.generation.llm import LLM

    return LLM(dataclasses.replace(config, decoder_num_ctx=4096))


def test_respuesta_real_mc(indice_prueba, llm_pequeno_ctx, tmp_path, monkeypatch):
    monkeypatch.setattr("src.generation.llm.DIR_CACHE", tmp_path / "gen")
    _, rec = indice_prueba
    r = responder(MC, rec, llm_pequeno_ctx, usar_cache=False)
    assert r.pasajes and r.pasajes[0].meta["articulo"] == "1820"
    assert r.datos is not None
    assert r.datos["respuesta_correcta"] == "A"
    assert set(r.datos["descarte_opciones"]) <= {"B", "C", "D"}
    assert r.datos["justificacion"].strip()
