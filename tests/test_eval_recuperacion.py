"""Pruebas de las métricas de recuperación y del reporte de brechas."""
import json

from src.config import RAIZ
from src.eval import brechas
from src.eval.recuperacion import evaluar

PREGUNTAS_PRUEBA = [
    {"id": 1, "formato": "semi_open", "area": "Derecho civil",
     "pregunta": "¿Qué dice el artículo 1820 del Código Civil sobre la sociedad conyugal?",
     "legal_basis": "Artículo 1820 del Código Civil."},
    {"id": 2, "formato": "multiple_choice", "area": "Derecho administrativo",
     "pregunta": "¿Cuál es el plazo previsto?",
     "opciones": {"A": "Ley 1150 de 2007, plazo", "B": "otra"},
     "legal_basis": "Artículo 11 de la Ley 1150 de 2007"},
    {"id": 3, "formato": "semi_open", "area": "Derecho laboral",
     "pregunta": "¿Qué regula el Código Sustantivo del Trabajo sobre vacaciones?",
     "legal_basis": "Código Sustantivo del Trabajo"},
    {"id": 4, "formato": "semi_open", "area": "Derecho civil", "pregunta": "x",
     "legal_basis": "Doctrina."},
]


def test_evaluar_recuperacion(indice_prueba):
    _, rec = indice_prueba
    rep = evaluar(rec, PREGUNTAS_PRUEBA, k=10)
    assert rep["items_evaluados"] == 3                    # "Doctrina." no es citable
    por_id = {d["id"]: d for d in rep["detalle"]}
    assert por_id[1]["acierto"] and por_id[2]["acierto"]
    assert not por_id[3]["acierto"]                       # el CST no está en el mini-corpus
    assert por_id[3]["faltantes"] == [["codigo_sustantivo_trabajo", None, None]]
    assert rep["acierto_at_k"] == round(2 / 3, 4)


def test_brechas_sin_corpus_y_con_corpus(indice_prueba, tmp_path):
    muestra = [json.loads(l) for l in (RAIZ / "data" / "sample_50.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    seed = RAIZ / "data" / "seed_targets.json"

    vacio = brechas.calcular(set(), seed, muestra)
    assert vacio["items_seed_cubiertos"] == 0 and vacio["faltan_seed"][0]["norma"] == "Constitucion"

    presentes = brechas.cuerpos_en_corpus(indice_prueba[0] / "corpus" / "_resumen.json")
    r = brechas.calcular(presentes, seed, muestra)
    assert ("constitucion", None, None) in presentes
    assert all(f["norma"] != "Constitucion" for f in r["faltan_seed"])
    assert r["items_seed_cubiertos"] > 0
    nombres = [f["nombre"] for f in r["faltan_muestra"]]
    assert "Codigo penal" in nombres and "Constitucion" not in nombres

    md = brechas.markdown(r)
    assert md.startswith("# Brechas del corpus") and "| Ítems del banco |" in md
