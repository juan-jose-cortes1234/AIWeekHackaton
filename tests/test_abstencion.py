"""Pruebas de la abstención (lógica pura y con el recuperador real)."""
import jsonschema
import json

from src.config import RAIZ
from src.generation.abstencion import decidir, registro_abstencion
from src.retrieval.hibrido import Pasaje

SEMI = {"id": 7, "formato": "semi_open"}
MC = {"id": 8, "formato": "multiple_choice"}
ABIERTA = {"id": 9, "formato": "open_ended"}
OK_SEMI = {"respuesta": "Una respuesta.", "palabras_clave": ["a"], "referencia_legal": "x"}


def P(rerank=None, denso=None, origen=None):
    return Pasaje(id=1, chunk_id="d#1", doc_id="d", inicio=0, fin=5, texto="Ley 1 de 2000.\nx",
                  score=1.0, score_rerank=rerank, score_denso=denso, origen=origen or ["denso"])


def test_mc_nunca_se_abstiene():
    assert not decidir(MC, [], None).abstener
    assert not decidir(MC, [P(rerank=0.0001)], None).abstener


def test_texto_libre_sin_pasajes_o_sin_respuesta():
    assert decidir(SEMI, [], OK_SEMI).abstener
    assert decidir(SEMI, [P(rerank=0.9)], None).abstener
    assert decidir(SEMI, [P(rerank=0.9)], {"respuesta": "", "referencia_legal": ""}).abstener


def test_umbral_rerank_y_denso():
    # El mecanismo sigue disponible si se configura un umbral (antes: 0.05 y 0.35).
    import dataclasses
    from src.config import config

    cfg = dataclasses.replace(config, umbral_abstencion=0.05, umbral_abstencion_denso=0.35)
    assert decidir(SEMI, [P(rerank=0.01)], OK_SEMI, cfg).abstener
    assert not decidir(SEMI, [P(rerank=0.6)], OK_SEMI, cfg).abstener
    assert decidir(SEMI, [P(denso=0.2)], OK_SEMI, cfg).abstener          # sin reranker
    assert not decidir(SEMI, [P(denso=0.6)], OK_SEMI, cfg).abstener


def test_umbral_por_defecto_evidencia_insuficiente():
    # C-19: requisito mínimo del Paso 4: abstenerse cuando el corpus no da fundamento suficiente.
    assert decidir(SEMI, [P(rerank=0.01)], OK_SEMI).abstener           # < 0,025
    assert not decidir(SEMI, [P(rerank=0.03)], OK_SEMI).abstener       # >= 0,025
    assert decidir(SEMI, [P(denso=0.2)], OK_SEMI).abstener             # sin reranker: < 0,35


def test_router_evita_abstencion():
    assert not decidir(SEMI, [P(rerank=0.001, origen=["router"])], OK_SEMI).abstener


def test_registro_valida_con_el_esquema_oficial():
    esquema = json.loads((RAIZ / "schema" / "submission.schema.json").read_text(encoding="utf-8"))
    for item in (SEMI, ABIERTA):
        reg = registro_abstencion(item, [P(rerank=0.01)])
        jsonschema.validate(reg, esquema)
        assert reg["abstencion"] is True and reg["pasajes_recuperados"]


def test_con_recuperador_real(indice_prueba):
    _, rec = indice_prueba
    ajena = "¿Qué tarifa tiene el impuesto al carbono para combustibles de aviación?"
    pasajes = rec.buscar(ajena, k=10)
    import dataclasses
    from src.config import config

    con_umbral = dataclasses.replace(config, umbral_abstencion=0.05, umbral_abstencion_denso=0.35)
    assert decidir({"id": 1, "formato": "semi_open"}, pasajes, OK_SEMI, con_umbral).abstener
    assert not decidir({"id": 1, "formato": "multiple_choice"}, pasajes, None).abstener
    propia = rec.buscar("¿Qué es la sociedad conyugal según el Código Civil?", k=10)
    assert not decidir({"id": 2, "formato": "semi_open"}, propia, OK_SEMI).abstener


def test_sin_campo_principal_se_abstiene():
    # Salida rescatada que solo trajo palabras clave: no hay respuesta que evaluar.
    assert decidir(SEMI, [P(rerank=0.9)], {"respuesta": "", "palabras_clave": ["a"],
                                           "referencia_legal": "x"}).abstener
    assert not decidir(ABIERTA, [P(rerank=0.9)], {"analisis": "Algo.", "marco_normativo": "",
                                                   "jurisprudencia": "", "conclusion": ""}).abstener
