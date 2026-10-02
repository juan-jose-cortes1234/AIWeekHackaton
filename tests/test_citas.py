"""Pruebas del post-filtro de citas, calificadas con el evaluador oficial."""
import pytest

import src.oficial  # noqa: F401  (añade scripts/ al path)
import evaluate
from src.generation.citas import (completar_anios, filtrar, limitar, localizar, postprocesar,
                                  referencia, respaldadas)
from src.retrieval.hibrido import Pasaje


def P(n, texto, rerank=None, origen=None):
    return Pasaje(id=n, chunk_id=f"d#{n}", doc_id="d", inicio=0, fin=len(texto), texto=texto,
                  score=1.0, score_rerank=rerank, origen=origen or ["denso"])


PASAJES = [
    P(1, "Ley 1150 de 2007, artículo 11.\nTEXTO DE PRUEBA sobre liquidación.", rerank=0.9),
    P(2, "Constitución Política de Colombia, artículo 29.\nTEXTO DE PRUEBA de debido proceso.",
      rerank=0.7),
    P(3, "Código Civil, artículo 1820.\nTEXTO DE PRUEBA de sociedad conyugal.", rerank=0.1),
    P(4, "Sentencia C-355 de 2006 de la Corte Constitucional. [RESUELVE]\nTEXTO DE PRUEBA.",
      rerank=0.05),
]
INVENTADAS = ("Según el artículo 99 de la Ley 9999 de 2020, el plazo es de cuatro meses. "
              "Esto concuerda con el artículo 5 del Código Penal y la Sentencia T-123 de 2019. "
              "La Ley 1150 regula la liquidación. El artículo 29 de la Constitución lo exige.")


def _sin_respaldo(sub: dict) -> dict:
    return evaluate.citations.score(evaluate.answer_text(sub), "", evaluate.citas_respaldadas(sub))


def test_localizar_coincide_con_el_evaluador():
    spans = localizar(INVENTADAS)
    assert {c for _, _, c in spans} == evaluate.citations.bodies(
        evaluate.citations.extract(INVENTADAS))
    for i, f, _ in spans:
        assert INVENTADAS[i:f].strip()


def test_completar_anio_unico():
    soporte = respaldadas(PASAJES)
    assert completar_anios("La Ley 1150 regula.", soporte) == "La Ley 1150 de 2007 regula."
    assert completar_anios("La Ley 80 regula.", soporte) == "La Ley 80 regula."


def test_filtrar_elimina_solo_lo_no_respaldado():
    soporte = respaldadas(PASAJES)
    texto, elim = filtrar(completar_anios(INVENTADAS, soporte), soporte)
    quedan = evaluate.citations.bodies(evaluate.citations.extract(texto))
    assert quedan <= soporte
    assert ("ley", "1150", "2007") in quedan and ("constitucion", None, None) in quedan
    assert elim and "cuatro meses" in texto        # el contenido se conserva
    assert "Sentencia la normativa" not in texto and "Sentencia T-123" not in texto


@pytest.mark.parametrize("formato,datos", [
    ("multiple_choice", {"respuesta_correcta": "A", "justificacion": INVENTADAS,
                         "descarte_opciones": {"B": "Lo prohíbe la Ley 7777 de 2001.",
                                               "C": "No aplica.", "A": "x"},
                         "pasajes_usados": [1, 2]}),
    ("semi_open", {"respuesta": INVENTADAS, "palabras_clave": ["plazo", "liquidación", "contrato"],
                   "referencia_legal": "Ley 9999 de 2020", "pasajes_usados": [1]}),
    ("open_ended", {"marco_normativo": INVENTADAS, "analisis": INVENTADAS,
                    "jurisprudencia": "Sentencia T-123 de 2019 y Sentencia C-355 de 2006.",
                    "conclusion": "Aplica el artículo 11 de la Ley 1150 de 2007.",
                    "pasajes_usados": [1, 4]}),
])
def test_cero_citas_sin_respaldo_segun_el_evaluador(formato, datos):
    item = {"id": 1, "formato": formato, "opciones": {"A": "a", "B": "b", "C": "c", "D": "d"}}
    pp = postprocesar(item, datos, PASAJES)
    sub = {"id": 1, "formato": formato, "abstencion": False, **pp.campos,
           "pasajes_recuperados": [p.a_entrega() for p in PASAJES]}
    r = _sin_respaldo(sub)
    assert r["citas_sin_respaldo"] == 0, r["detalle"]
    assert r["n_citadas"] >= 1
    assert "pasajes_usados" not in pp.campos


def test_render_referencias_desde_metadatos():
    item = {"id": 1, "formato": "semi_open"}
    pp = postprocesar(item, {"respuesta": "Una oración. Otra. Tercera.", "palabras_clave": [],
                             "referencia_legal": "", "pasajes_usados": [3]}, PASAJES)
    # usado por el modelo (P3) + pertinentes por rerank ≥ 0,5 (P1, P2); no P4.
    assert pp.referencias == ["Código Civil, artículo 1820", "Ley 1150 de 2007, artículo 11",
                              "Constitución Política de Colombia, artículo 29"]
    assert pp.campos["referencia_legal"].startswith("Código Civil, artículo 1820")
    assert referencia(PASAJES[3]) == "Sentencia C-355 de 2006 de la Corte Constitucional"


def test_descarte_no_incluye_letra_elegida():
    item = {"id": 1, "formato": "multiple_choice"}
    pp = postprocesar(item, {"respuesta_correcta": "A", "justificacion": "Por la Ley 1150 de 2007.",
                             "descarte_opciones": {"A": "x", "B": "y"}, "pasajes_usados": [1]},
                      PASAJES)
    assert set(pp.campos["descarte_opciones"]) == {"B"}
    assert "Fundamento normativo: Ley 1150 de 2007, artículo 11" in pp.campos["justificacion"]


def test_limites_de_extension():
    texto = " ".join(f"Oración número {i} con varias palabras de relleno." for i in range(10))
    assert len(limitar(texto, 5).split(". ")) <= 5
    corto = limitar(" ".join(["Palabra " * 60 + "fin."] * 4), 5, 150)
    assert len(corto.split()) <= 150


def test_abierta_rescatada_completa_campos_obligatorios():
    item = {"id": 1, "formato": "open_ended"}
    datos = {"marco_normativo": "Aplica el artículo 11 de la Ley 1150 de 2007.",
             "analisis": "El contrato no se liquidó. El plazo supletorio es de cuatro meses.",
             "pasajes_usados": [1]}                      # sin jurisprudencia ni conclusión (cortada)
    pp = postprocesar(item, datos, PASAJES)
    for campo in ("marco_normativo", "analisis", "jurisprudencia", "conclusion"):
        assert pp.campos[campo].strip(), campo
    sub = {"id": 1, "formato": "open_ended", "abstencion": False, **pp.campos,
           "pasajes_recuperados": [p.a_entrega() for p in PASAJES]}
    assert evaluate.validate([sub], {1}) == []


def test_citas_solapadas_no_corrompen_el_texto():
    # Caso 679 (muestra_v6): un código dentro de una cita más larga se reemplazaba dos veces
    # y quedaba "la normativa aplicla normativa aplicable…".
    from src.generation.citas import REEMPLAZO, _quitar_spans, localizar

    t = "Artículo 49 de la Constitución Política de Colombia, que garantiza el derecho a la salud."
    limpio = _quitar_spans(t, [(i, f) for i, f, _ in localizar(t)])
    assert limpio.count(REEMPLAZO) == 1
    assert "garantiza el derecho a la salud" in limpio and "aplicla" not in limpio


def test_abierta_no_pasa_de_500_palabras():
    from src.generation.citas import MAX_PALABRAS_ABIERTA, postprocesar

    item = {"id": 9, "formato": "open_ended", "pregunta": "Caso de prueba."}
    largo = " ".join(f"Oración de análisis número {i} " + "palabra " * 70 + "." for i in range(8))
    pp = postprocesar(item, {"marco_normativo": "Marco.", "analisis": largo,
                             "jurisprudencia": "Juris.", "conclusion": "Conclusión."}, [])
    total = sum(len(str(pp.campos[c]).split()) for c in ("marco_normativo", "analisis",
                                                         "jurisprudencia", "conclusion"))
    assert total <= MAX_PALABRAS_ABIERTA and pp.campos["analisis"]
