"""Pruebas del segmentador con texto inventado (TEXTO DE PRUEBA)."""
import pytest

from src.corpus.segmentar import ARTICULO_RE, id_articulo, segmentar, ventanas


@pytest.mark.parametrize("linea,esperado", [
    ("ARTÍCULO 1o. Texto.", "1"),
    ("ARTICULO 11A. Texto.", "11A"),
    ("Artículo 5 bis. Texto.", "5 bis"),
    ("ART. 20. Texto.", "20"),
    ("ARTÍCULO 240-1. Texto.", "240-1"),
    ("Artículo 2.2.1.1.1. Texto.", "2.2.1.1.1"),
    ("ARTICULO TRANSITORIO 3o. Texto.", "T3"),
    ("ARTÍCULO 7o. TRANSITORIO. Texto.", "T7"),
    ("ARTÍCULO 12º.- Texto.", "12"),
    ("ARTÍCULO 30", "30"),
])
def test_regex_articulo(linea, esperado):
    m = ARTICULO_RE.match(linea)
    assert m, linea
    assert id_articulo(m) == esperado


@pytest.mark.parametrize("linea", [
    "Artículo 5 de la Ley 100 de 1993 dispone...",
    "Articulos modificados por la presente ley",
    "El artículo 3o. dispone",
])
def test_no_es_encabezado(linea):
    assert ARTICULO_RE.match(linea) is None


NORMA = """LEY DE PRUEBA
Por la cual se dictan normas de prueba.
EL CONGRESO DE PRUEBA DECRETA:
TÍTULO I
DISPOSICIONES GENERALES
ARTÍCULO 1o. OBJETO. TEXTO DE PRUEBA del primer artículo.
PARÁGRAFO. Parágrafo de prueba.
Notas de Vigencia
- Artículo modificado por una norma de prueba.
Concordancias
Ley de prueba; Art. 99
ARTÍCULO 2o. TEXTO DE PRUEBA del segundo artículo.
Legislación Anterior
Texto original:
ARTÍCULO 2o. Versión anterior del segundo artículo.
CAPÍTULO II
ARTÍCULO 3o. TEXTO DE PRUEBA del tercer artículo, que cita el
Artículo 5 de la Ley 100 de 1993 dispone algo en su propia línea.
"""


def test_segmentar_norma():
    segs = segmentar(NORMA, "ley")
    tipos = [(s.tipo, s.articulo) for s in segs]
    assert tipos == [("preambulo", None), ("articulo", "1"), ("nota", "1"),
                     ("articulo", "2"), ("nota", "2"), ("articulo", "3")]
    art1 = segs[1]
    assert "PARÁGRAFO. Parágrafo de prueba." in art1.texto
    assert "Notas de Vigencia" not in art1.texto
    assert art1.seccion == "TÍTULO I DISPOSICIONES GENERALES"
    assert "Art. 99" not in "".join(s.texto for s in segs)          # concordancias fuera
    assert "Versión anterior" in segs[4].texto                        # repetición → nota
    assert "CAPÍTULO II" not in segs[4].texto
    assert segs[5].seccion == "CAPÍTULO II"
    assert "Artículo 5 de la Ley 100" in segs[5].texto               # referencia, no corte
    assert [s.orden for s in segs] == list(range(6))


SENTENCIA = "\n".join([
    "Sentencia de prueba",
    "I. ANTECEDENTES",
    *[f"Párrafo de antecedentes {i} " + "palabra " * 60 for i in range(8)],
    "II. CONSIDERACIONES",
    "Consideración de prueba " + "palabra " * 40,
    "III. DECISIÓN",
    "RESUELVE:",
    "PRIMERO. Declarar TEXTO DE PRUEBA.",
])


def test_segmentar_sentencia():
    segs = segmentar(SENTENCIA, "sentencia")
    secciones = [s.seccion for s in segs]
    assert secciones[0] is None
    assert "ANTECEDENTES" in secciones and "CONSIDERACIONES" in secciones
    assert secciones[-1] == "RESUELVE"
    assert "PRIMERO. Declarar" in segs[-1].texto
    antecedentes = [s for s in segs if s.seccion == "ANTECEDENTES"]
    assert len(antecedentes) >= 2
    assert all(len(s.texto.split()) <= 300 for s in antecedentes)


def test_ventanas_con_solape_y_parrafo_gigante():
    parrafos = [f"p{i} " + "x " * 99 for i in range(6)]   # 100 palabras c/u
    vs = ventanas(parrafos, palabras=300, solape=0.15)
    assert len(vs) >= 2 and all(len(v.split()) <= 300 for v in vs)
    gigante = ventanas(["y " * 1000], palabras=300, solape=0.15)
    assert len(gigante) >= 4 and all(len(v.split()) <= 300 for v in gigante)


def test_sin_articulos_cae_a_ventanas():
    segs = segmentar("Circular de prueba sin artículos.\nOtra línea.", "circular")
    assert segs and all(s.tipo == "seccion" for s in segs)


@pytest.mark.parametrize("linea,esperado", [
    # Títulos verdaderos (mayúsculas o numerados)
    ("I. ANTECEDENTES", "ANTECEDENTES"),
    ("Consideraciones y fundamentos", None),            # sin numeración ni mayúsculas
    ("II. Consideraciones y fundamentos", "CONSIDERACIONES"),
    ("1. Competencia", "COMPETENCIA"),
    ("VII. DECISIÓN", "DECISIÓN"),
    ("RESUELVE:", "RESUELVE"),
    ("SÍNTESIS DE LA DECISIÓN", "SÍNTESIS"),
    ("V. CONCEPTO DEL PROCURADOR GENERAL DE LA NACIÓN", "CONCEPTO DEL MINISTERIO PÚBLICO"),
    ("SALVAMENTO DE VOTO DEL MAGISTRADO ALVARO TAFUR", "SALVAMENTO DE VOTO"),
    ("ACLARACIÓN DE VOTO DEL MAGISTRADO", "ACLARACIÓN DE VOTO"),
    # Falsos positivos reales (C-355 de 2006 y otras)
    ("concepto del Procurador.", None),
    ("concepto de vida protegido por la Convención[44].", None),
    ("aclaración de voto basada esencialmente en las argumentaciones esbozadas en la", None),
    ("Salvamento de voto: Stevens).", None),
    ("salvamento de voto, con los cuales se explicó por qué la vida humana del niño", None),
    ("Salvamento Parcial de Voto de Alfredo Beltrán Sierra, Carlos Gaviria Díaz y", None),
    ("análisis del caso (“relativo a la inexistencia de una medida regresiva e", None),
    ("7.1. Decisión", None),                                # subtítulo partido (SU-455 de 2020)
    ("2.3. COMPETENCIA", None),                             # numeración de varios niveles
    ("II. CONSIDERACIONES DE LA CORTE CONSTITUCIONAL", "CONSIDERACIONES"),
])
def test_titulo_seccion(linea, esperado):
    from src.corpus.segmentar import titulo_seccion

    assert titulo_seccion(linea) == esperado


def test_orden_de_la_sentencia():
    from src.corpus.segmentar import secciones_sentencia

    texto = "\n".join([
        "Sentencia de prueba", "I. ANTECEDENTES", "Hechos de prueba.",
        "II. CONSIDERACIONES", "Razonamiento de prueba.",
        "SALVAMENTO DE VOTO FALSO",               # antes del RESUELVE: no es un salvamento
        "III. DECISIÓN", "En mérito de lo expuesto…", "RESUELVE:", "PRIMERO. Declarar exequible.",
        "SEGUNDO. Orden de prueba.", "Notifíquese, comuníquese y cúmplase.", "Magistrado de prueba",
        "ANEXO", "II. Consideraciones", "Texto del anexo.", "RESUELVE",   # anexo: sin etiqueta
        "SALVAMENTO DE VOTO DEL MAGISTRADO X", "Disiento porque…",
        "CONSIDERACIONES", "Argumento del salvamento.",                   # sigue siendo salvamento
        "ACLARACIÓN DE VOTO DE LA MAGISTRADA Y", "Aclaro que…",
    ])
    b = [(s, " ".join(l for l in lineas if l.strip())) for s, lineas in secciones_sentencia(texto)]
    etiquetas = [s for s, _ in b]
    assert etiquetas == [None, "ANTECEDENTES", "CONSIDERACIONES", "DECISIÓN", "RESUELVE", None,
                         "SALVAMENTO DE VOTO", "ACLARACIÓN DE VOTO"]
    resuelve = dict(b)["RESUELVE"]
    assert "SEGUNDO. Orden de prueba." in resuelve and "anexo" not in resuelve
    assert "Argumento del salvamento." in dict(b)["SALVAMENTO DE VOTO"]
    assert "SALVAMENTO DE VOTO FALSO" in dict(b)["CONSIDERACIONES"]


def test_titulo_de_voto_partido_en_dos_lineas():
    from src.corpus.segmentar import secciones_sentencia

    texto = "\n".join([
        "I. ANTECEDENTES", "Hechos.", "RESUELVE:", "PRIMERO. Declarar.",
        "Notifíquese y cúmplase.", "Magistrado de prueba",
        "ACLARACIÓN DE", "VOTO A LA SENTENCIA C-000 DE 2006 DEL MAGISTRADO X", "Aclaro que…",
    ])
    etiquetas = [s for s, _ in secciones_sentencia(texto)]
    assert etiquetas == [None, "ANTECEDENTES", "RESUELVE", None, "ACLARACIÓN DE VOTO"]
