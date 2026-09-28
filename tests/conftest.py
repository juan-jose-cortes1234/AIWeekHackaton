"""Fixtures compartidos: un corpus crudo mínimo con TEXTO DE PRUEBA.

Los textos son inventados y están marcados; solo imitan la forma de las normas
reales para probar la ingesta. Nunca se usan fuera de las pruebas.
"""
from pathlib import Path

import pytest

CABECERA = ("doc_id,archivo,titulo,tipo,numero,anio,organo_emisor,fuente,url,"
            "fecha_consulta,areas,vigencia,notas")

LARGO = " ".join(f"palabra{i}" for i in range(700))

DOCUMENTOS = {
    "constitucion_1991": (
        "normas/constitucion.html", "Constitución Política de 1991", "constitucion", "", "",
        "Asamblea Nacional Constituyente", "Derecho constitucional",
        "<p>PREÁMBULO DE PRUEBA</p><p>TÍTULO I</p>"
        "<p>ARTÍCULO 1o. TEXTO DE PRUEBA sobre el Estado.</p>"
        "<p>ARTÍCULO 29. TEXTO DE PRUEBA sobre el debido proceso.</p>"
        "<p>ARTICULO TRANSITORIO 1o. TEXTO DE PRUEBA transitorio.</p>"),
    "ley_1564_2012": (
        "normas/cgp.html", "Código General del Proceso", "codigo", "1564", "2012",
        "Congreso de la República", "procesal|civil",
        "<p>ARTÍCULO 6o. INMEDIACIÓN. TEXTO DE PRUEBA de inmediación.</p>"
        "<p>Notas de Vigencia</p><p>- Nota de prueba.</p>"
        "<p>ARTÍCULO 25. CUANTÍA. TEXTO DE PRUEBA de cuantía.</p>"),
    "codigo_civil": (
        "normas/cc.txt", "Código Civil", "codigo", "", "", "Congreso", "civil|familia",
        "ARTICULO 1820. TEXTO DE PRUEBA sobre la sociedad conyugal.\n"
        "ARTICULO 1796. TEXTO DE PRUEBA sobre obligaciones."),
    "ley_1150_2007": (
        "normas/ley_1150_2007.html", "Ley 1150 de 2007", "ley", "1150", "2007", "Congreso",
        "administrativo",
        f"<p>ARTÍCULO 11. DEL PLAZO. TEXTO DE PRUEBA.</p><p>{LARGO}</p>"),
    "decreto_2153_1992": (
        "normas/d2153.txt", "Decreto 2153 de 1992", "decreto", "2153", "1992", "Presidencia",
        "mercados",
        "ARTÍCULO 45. DEFINICIONES. TEXTO DE PRUEBA de definiciones."),
    "sentencia_c-355_2006": (
        "jurisprudencia/c-355-06.htm", "Sentencia C-355 de 2006", "sentencia", "C-355", "2006",
        "Corte Constitucional", "constitucional|penal",
        "<p>I. ANTECEDENTES</p><p>TEXTO DE PRUEBA de antecedentes.</p>"
        "<p>RESUELVE:</p><p>PRIMERO. TEXTO DE PRUEBA de la decisión.</p>"),
}


def crear_corpus(raiz: Path) -> Path:
    """Escribe el mini-corpus de prueba en `raiz` y devuelve la ruta."""
    filas = [CABECERA]
    for doc_id, (archivo, titulo, tipo, num, anio, organo, areas, contenido) in DOCUMENTOS.items():
        ruta = raiz / archivo
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8")
        filas.append(",".join([doc_id, archivo, titulo, tipo, num, anio, organo, "Prueba",
                               f"https://ejemplo.gov.co/{doc_id}", "2026-09-28", areas,
                               "vigente", ""]))
    (raiz / "fuentes.csv").write_text("\n".join(filas) + "\n", encoding="utf-8")
    return raiz


@pytest.fixture
def corpus_crudo(tmp_path: Path) -> Path:
    return crear_corpus(tmp_path / "corpus_raw")


@pytest.fixture(scope="session")
def encoder_real():
    """El encoder configurado en .env (bge-m3 por defecto), cargado una vez por sesión."""
    from src.index.encoder import EncoderST

    return EncoderST()


@pytest.fixture(scope="session")
def reranker_real():
    """El reranker configurado en .env (bge-reranker-v2-m3 por defecto)."""
    from src.retrieval.reranker import Reranker

    return Reranker()


@pytest.fixture(scope="session")
def indice_prueba(tmp_path_factory, encoder_real, reranker_real):
    """Mini-corpus de prueba procesado e indexado con el encoder real: (dir build, Recuperador)."""
    from src.corpus.build import construir
    from src.index.build import construir_indice
    from src.index.lexico import construir_bm25
    from src.retrieval.hibrido import Recuperador

    base = tmp_path_factory.mktemp("indice_prueba")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.index.encoder.DIR_CACHE", base / "cache")
        salida = base / "build"
        construir(crear_corpus(base / "corpus_raw"), salida)
        construir_indice(salida / "indice", enc=encoder_real, dir_corpus=salida / "corpus")
        construir_bm25(salida / "indice")
    return salida, Recuperador.cargar(salida / "indice", encoder=encoder_real,
                                      reranker=reranker_real)
