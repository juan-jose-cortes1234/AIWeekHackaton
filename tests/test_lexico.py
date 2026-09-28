"""Pruebas del índice BM25 y su tokenizador."""
import json

from src.corpus.build import construir
from src.index.lexico import IndiceBM25, construir_bm25, tokenizar


def test_tokenizador_conserva_identificadores():
    toks = tokenizar("Según la Sentencia SL3385-2022 y la C-355 de 2006, el Artículo 1o. "
                     "del ET, artículo 240-1 y el 2.2.1.1.1 de los contratos")
    for esperado in ("sl-3385", "c-355", "2006", "2022", "1", "240-1", "2.2.1.1.1", "contrat"):
        assert esperado in toks, esperado
    assert "de" not in toks and "según" not in toks and "segun" not in toks


def test_tokenizador_sin_tildes_y_stemming():
    assert tokenizar("liquidación") == tokenizar("LIQUIDACION")
    for plural, singular in (("contratos", "contrato"), ("trabajadores", "trabajador"),
                             ("obligaciones", "obligación")):
        assert tokenizar(plural) == tokenizar(singular)


def test_numero_distingue_articulos(corpus_crudo, tmp_path):
    salida = tmp_path / "build"
    construir(corpus_crudo, salida)
    idx = construir_bm25(salida / "indice")
    chunks = [json.loads(l) for l in (salida / "indice" / "chunks.jsonl").read_text(
        encoding="utf-8").splitlines()]
    top, _ = idx.buscar("artículo 1820 del Código Civil", k=1)[0]
    assert chunks[top]["articulo"] == "1820"
    top, _ = idx.buscar("artículo 1796", k=1)[0]
    assert chunks[top]["articulo"] == "1796"

    # Persistencia: cargar da los mismos puntajes.
    idx2 = IndiceBM25.cargar(salida / "indice" / "bm25")
    assert idx2.buscar("inmediación", k=3) == idx.buscar("inmediación", k=3)


def test_consulta_vacia_y_desempate_estable():
    idx = IndiceBM25.construir(["plazo uno", "plazo dos", "otra cosa"])
    assert idx.buscar("de la", k=5) == []
    res = idx.buscar("plazo", k=5)
    assert [i for i, _ in res] == [0, 1]
