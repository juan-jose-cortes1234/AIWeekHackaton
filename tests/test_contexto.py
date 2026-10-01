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
    extra = consultas_extra(MC)                      # modo "clave": la opción va primero
    assert len(extra) == 4
    assert all(e.startswith(str(v).strip()) for e, (_, v) in zip(extra, sorted(MC["opciones"].items())))
    assert consultas_extra(SEMI) == []
    previo = dataclasses.replace(config, mc_consulta_opcion="pregunta")
    assert all(e.startswith(MC["pregunta"].strip()) for e in consultas_extra(MC, previo))


def test_palabras_clave_prefiere_las_raras():
    from src.generation.responder import palabras_clave

    pregunta = ("Habiendo hecho la lectura previa de la Resolución 368 de 2014, lea con atención "
                "y responda: ¿qué vicio configura ignorar la consulta previa de los pueblos indígenas?")
    todas = palabras_clave(pregunta, 50)
    assert "lea" not in todas and "responda" not in todas and "de" not in todas
    assert "368" in todas and "2014" in todas
    raras = {"pueblos": 3, "indígenas": 2, "vicio": 5, "consulta": 40, "368": 1}
    elegidas = palabras_clave(pregunta, 4, lambda w: raras.get(w, 1000))
    assert elegidas == ["368", "vicio", "pueblos", "indígenas"]       # las 4 más raras, en orden


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
    assert set(r.datos["descarte_opciones"]) <= {"A", "B", "C", "D"}
    # Modo "abierta" (C-08, por defecto): hubo respuesta sin opciones y una letra por similitud.
    assert r.extra["mc_modo"] == "abierta" and r.extra["respuesta_abierta"]
    assert r.extra["opcion_por_similitud"] in {"A", "B", "C", "D"}
    assert r.datos["justificacion"].strip()


def test_mc_elige_primero_por_defecto():
    props = list(esquema(MC)["properties"])
    assert props[0] == "respuesta_correcta" and "descarte_opciones" in props
    assert '"descarte_opciones"' in mensajes(MC, [])[1]["content"]


def test_mc_analiza_opciones_antes_de_elegir():
    cfg = dataclasses.replace(config, mc_analisis_previo=True, mc_modo="directo")
    props = list(esquema(MC, cfg)["properties"])
    assert props.index("analisis_opciones") < props.index("respuesta_correcta")
    assert '"analisis_opciones"' in mensajes(MC, [], cfg)[1]["content"]


def test_recuperacion_por_opcion(indice_prueba):
    from collections import Counter

    from src.generation.responder import recuperar

    _, rec = indice_prueba
    pasajes = recuperar(MC, rec)
    ids = [p.chunk_id for p in pasajes]
    assert len(ids) == len(set(ids)) <= config.top_k_pasajes           # sin duplicados
    marcadas = Counter((p.meta or {}).get("opcion") for p in pasajes)
    assert sum(v for k, v in marcadas.items() if k) >= 1               # hay evidencia por opción
    assert pasajes[0].meta["articulo"] == "1820"                       # la pregunta sigue primero
    texto = mensajes(MC, pasajes)[1]["content"]
    assert "(recuperado para la opción" in texto


def test_mc_abierta_paso_1_sin_opciones_paso_2_con_respuesta():
    from src.generation.contexto import esquema_mc_abierta

    pasajes = [_pasaje(1, "Código Civil, artículo 1820.\nTEXTO DE PRUEBA")]
    pasajes[0].meta = {"opcion": "B"}
    paso1 = mensajes(MC, pasajes, etapa="abierta")[1]["content"]
    assert "La sociedad conyugal" not in paso1 and "A)" not in paso1          # sin opciones
    assert "recuperado para la opción" not in paso1                          # ni marcas
    assert set(esquema_mc_abierta()["required"]) == {"respuesta", "pasajes_usados"}
    paso2 = mensajes(MC, pasajes, etapa="desde_abierta",
                     respuesta_abierta="RESPUESTA PRELIMINAR DE PRUEBA")[1]["content"]
    assert "RESPUESTA PRELIMINAR DE PRUEBA" in paso2 and "A) La sociedad conyugal" in paso2
    assert "(recuperado para la opción B)" in paso2
