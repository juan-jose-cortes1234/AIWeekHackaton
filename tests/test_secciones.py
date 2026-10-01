"""Pruebas del chequeo automático de secciones (conteos inventados)."""
from collections import Counter

from src.corpus.secciones import alertas


def test_sentencia_sana_sin_avisos():
    assert alertas(Counter({"ANTECEDENTES": 10, "COMPETENCIA": 30, "RESUELVE": 3})) == []


def test_resuelve_desbordado():
    # Síntoma de la T-760 de 2008 con el detector viejo: 494 de 885 fragmentos en RESUELVE.
    avisos = alertas(Counter({"RESUELVE": 494, "CONSIDERACIONES": 391}))
    assert avisos == ["RESUELVE = 494/885 fragmentos"]


def test_sin_resuelve_ni_parte_motiva():
    assert alertas(Counter({"ANTECEDENTES": 5, "(sin sección)": 2})) == [
        "sin RESUELVE", "sin parte motiva"]
