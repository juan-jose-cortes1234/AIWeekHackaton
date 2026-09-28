"""Pruebas del reranker real (bge-reranker-v2-m3) y su integración en el recuperador."""
import dataclasses

from src.retrieval.hibrido import Recuperador


def test_puntua_pertinencia(reranker_real):
    q = "¿Cuál es el plazo para liquidar un contrato estatal?"
    s = reranker_real.puntuar(q, [
        "Ley 1150 de 2007, artículo 11. La liquidación de los contratos se hará dentro del "
        "término fijado o, en su defecto, dentro de los cuatro meses siguientes. TEXTO DE PRUEBA.",
        "Código Civil, artículo 1820. TEXTO DE PRUEBA sobre la sociedad conyugal.",
    ])
    assert s.shape == (2,) and 0 <= s.min() and s.max() <= 1
    assert s[0] > s[1]


def test_recuperador_usa_reranker(indice_prueba):
    _, rec = indice_prueba
    res = rec.buscar("sociedad conyugal", k=5)
    reord = [p for p in res if "rerank" in p.origen]
    assert reord and all(p.score_rerank is not None for p in reord)
    puntajes = [p.score for p in reord]
    assert puntajes == sorted(puntajes, reverse=True)
    assert res[0].meta["articulo"] == "1820"


def test_sin_reranker_por_configuracion(indice_prueba):
    _, rec = indice_prueba
    cfg = dataclasses.replace(rec.cfg, use_reranker=False)
    sin = Recuperador(rec.chunks, rec.denso, rec.bm25, rec.encoder, cfg, rec.reranker)
    res = sin.buscar("sociedad conyugal", k=5)
    assert all(p.score_rerank is None and "rerank" not in p.origen for p in res)
