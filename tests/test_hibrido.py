"""Pruebas del recuperador híbrido con el encoder real (bge-m3) y el mini-corpus de prueba."""
import pytest

from src.retrieval.hibrido import Recuperador


@pytest.fixture
def rec(indice_prueba):
    return indice_prueba[1]


def test_router_articulo_explicito(rec):
    res = rec.buscar("¿Qué dispone el artículo 1820 del Código Civil?")
    assert res[0].meta["articulo"] == "1820" and "router" in res[0].origen
    res = rec.buscar("Según el artículo 6 del Código General del Proceso, ¿qué es la inmediación?")
    assert res[0].doc_id == "ley_1564_2012" and res[0].meta["articulo"] == "6"


def test_router_por_alias_de_ley(rec):
    res = rec.buscar("¿Qué establece el artículo 11 de la Ley 1150 de 2007 sobre el plazo?")
    assert res[0].doc_id == "ley_1150_2007" and res[0].meta["articulo"] == "11"


def test_determinista(rec):
    q = "debido proceso en la Constitución"
    a = [(p.chunk_id, p.score) for p in rec.buscar(q, area="Derecho constitucional")]
    b = [(p.chunk_id, p.score) for p in rec.buscar(q, area="Derecho constitucional")]
    assert a == b and a


def test_diversidad_por_articulo(rec):
    res = rec.buscar("plazo artículo 11 Ley 1150 de 2007 palabra1 palabra200 palabra400", k=10)
    del_11 = [p for p in res if p.doc_id == "ley_1150_2007" and p.meta["articulo"] == "11"]
    assert 1 <= len(del_11) <= rec.cfg.max_por_articulo


def test_pasaje_de_entrega_literal_y_con_norma(rec, indice_prueba):
    from src.oficial import citations

    res = rec.buscar("sociedad conyugal", k=5)
    assert len(res) <= 5
    for p in res:
        e = p.a_entrega()
        assert set(e) == {"doc_id", "inicio", "fin", "texto", "score"}
        txt = (indice_prueba[0] / "corpus" / f"{p.doc_id}.txt").read_text(encoding="utf-8")
        assert txt[e["inicio"]:e["fin"]] == e["texto"]
        assert citations.extract(e["texto"])            # el evaluador reconoce la norma


def test_consultas_extra_amplian_candidatos(rec):
    con = rec.buscar("definiciones", consultas_extra=["cuantía"], k=10)
    assert any(rec.chunks[p.id]["articulo"] == "25" for p in con)


def test_modelo_distinto_al_del_indice(indice_prueba):
    class Otro:
        nombre = "otro/modelo"

    with pytest.raises(ValueError):
        Recuperador.cargar(indice_prueba[0] / "indice", encoder=Otro())


def test_tope_por_documento_y_excepcion_si_se_menciona(rec):
    import dataclasses
    from collections import Counter

    estricto = Recuperador(rec.chunks, rec.denso, rec.bm25, rec.encoder,
                           dataclasses.replace(rec.cfg, max_por_documento=1), rec.reranker)
    sin_mencion = estricto.buscar("plazo de liquidación palabra1 palabra200 palabra400", k=10)
    assert max(Counter(p.doc_id for p in sin_mencion).values()) == 1
    con_mencion = estricto.buscar("plazo según la Ley 1150 de 2007 palabra1 palabra200 palabra400", k=10)
    assert Counter(p.doc_id for p in con_mencion)["ley_1150_2007"] > 1   # mencionada: supera el tope


def test_frecuencia_documental_bm25(rec):
    assert rec.bm25.frecuencia("de") is None                  # palabra vacía
    assert rec.bm25.frecuencia("zzzinexistente") == 0
    assert rec.bm25.frecuencia("definiciones") > 0


def test_tope_de_complementarios_y_excepcion_si_se_menciona(rec, tmp_path):
    import dataclasses

    lista = tmp_path / "complementarios.txt"
    lista.write_text("# comentario\nley_1150_2007\n", encoding="utf-8")
    cfg = dataclasses.replace(rec.cfg, max_complementarios=1, max_por_documento=0,
                              documentos_complementarios=lista)
    tope = Recuperador(rec.chunks, rec.denso, rec.bm25, rec.encoder, cfg, rec.reranker)
    assert tope.complementarios == frozenset({"ley_1150_2007"})
    sin_mencion = tope.buscar("plazo de liquidación palabra1 palabra200 palabra400", k=10)
    assert sum(p.doc_id == "ley_1150_2007" for p in sin_mencion) <= 1
    con_mencion = tope.buscar("plazo según la Ley 1150 de 2007 palabra1 palabra200 palabra400", k=10)
    assert sum(p.doc_id == "ley_1150_2007" for p in con_mencion) > 1    # mencionada: sin tope


def test_aplicar_cuota_de_normas():
    from src.retrieval.hibrido import aplicar_cuota

    es = lambda x: x.startswith("N")
    # Faltan normas entre los 4 primeros: las mejores normas siguientes reemplazan a los últimos.
    assert aplicar_cuota(["S1", "S2", "N1", "S3", "S4", "N2", "N3"], 4, 2, es) == ["S1", "S2", "N1", "N2"]
    # Ya hay suficientes, o no hay normas candidatas: queda igual.
    assert aplicar_cuota(["N1", "N2", "S1", "S2", "S3"], 4, 2, es) == ["N1", "N2", "S1", "S2"]
    assert aplicar_cuota(["S1", "S2", "S3", "S4", "S5"], 4, 2, es) == ["S1", "S2", "S3", "S4"]
