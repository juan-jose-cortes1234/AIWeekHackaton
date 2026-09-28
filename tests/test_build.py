"""Pruebas de T07: encabezado canónico, trazabilidad y literalidad de los fragmentos."""
import json

import pytest

from src.corpus.build import construir
from src.corpus.fragmentar import cuerpos, nombre_canonico
from src.corpus.fuentes import Fuente


def _fuente(**kw):
    base = dict(doc_id="x", archivo=None, titulo="", tipo="ley", numero="", anio="",
                organo_emisor="", fuente="", url="", fecha_consulta="", areas=[])
    base.update(kw)
    return Fuente(**base)


@pytest.mark.parametrize("kw,nombre,cuerpo", [
    (dict(tipo="constitucion", titulo="Constitución de 1991"),
     "Constitución Política de Colombia", ("constitucion", None, None)),
    (dict(tipo="codigo", titulo="Código General del Proceso", numero="1564", anio="2012"),
     "Código General del Proceso (Ley 1564 de 2012)", ("codigo_general_proceso", None, None)),
    (dict(tipo="codigo", titulo="Estatuto Tributario", numero="624", anio="1989"),
     "Estatuto Tributario (Decreto 624 de 1989)", ("estatuto_tributario", None, None)),
    (dict(tipo="codigo", titulo="Código Civil"), "Código Civil", ("codigo_civil", None, None)),
    (dict(tipo="ley", titulo="Ley 1150 de 2007", numero="1150", anio="2007"),
     "Ley 1150 de 2007", ("ley", "1150", "2007")),
    (dict(tipo="ley", titulo="Estatuto del Consumidor", numero="1480", anio="2011"),
     "Estatuto del Consumidor (Ley 1480 de 2011)", ("estatuto_consumidor", None, None)),
    (dict(tipo="decreto_ley", titulo="Decreto Ley 663 de 1993", numero="663", anio="1993"),
     "Decreto Ley 663 de 1993", ("decreto", "663", "1993")),
    (dict(tipo="sentencia", titulo="Sentencia SL-3385 de 2022", numero="SL-3385", anio="2022",
          organo_emisor="Corte Suprema de Justicia"),
     "Sentencia SL-3385 de 2022 de la Corte Suprema de Justicia", ("jurisprudencia", "SL-3385", "2022")),
    (dict(tipo="decision_andina", titulo="Decisión 486", numero="486", anio="2000"),
     "Decisión 486 de la Comisión de la Comunidad Andina", ("decision_andina_486", None, None)),
])
def test_nombre_canonico_reconocido_por_el_evaluador(kw, nombre, cuerpo):
    f = _fuente(**kw)
    assert nombre_canonico(f) == nombre
    assert cuerpo in cuerpos(nombre)


def test_build_literalidad_y_trazabilidad(corpus_crudo, tmp_path):
    salida = tmp_path / "build"
    total = construir(corpus_crudo, salida)
    filas = [json.loads(l) for l in (salida / "indice" / "chunks.jsonl").read_text(
        encoding="utf-8").splitlines()]
    assert filas and total["n_fragmentos"] == len(filas)

    textos = {}
    for f in filas:
        if f["doc_id"] not in textos:
            textos[f["doc_id"]] = (salida / "corpus" / f"{f['doc_id']}.txt").read_text(
                encoding="utf-8")
        # (b) literalidad: el pasaje es exactamente el tramo del documento procesado
        assert textos[f["doc_id"]][f["inicio"]:f["fin"]] == f["texto"]

    esperado = {d["doc_id"]: {tuple(c) for c in d["cuerpos"]} for d in total["documentos"]}
    for f in filas:
        # (a) trazabilidad: el evaluador reconoce la norma de cada fragmento
        assert esperado[f["doc_id"]], f["doc_id"]
        assert esperado[f["doc_id"]] & cuerpos(f["texto"]), f["chunk_id"]
        assert f["texto"].split("\n", 1)[0].startswith(f["nombre_canonico"])


def test_build_metadatos_y_particion(corpus_crudo, tmp_path):
    salida = tmp_path / "build"
    construir(corpus_crudo, salida)
    filas = [json.loads(l) for l in (salida / "indice" / "chunks.jsonl").read_text(
        encoding="utf-8").splitlines()]
    por_id = {}
    for f in filas:
        por_id.setdefault(f["doc_id"], []).append(f)

    cgp = por_id["ley_1564_2012"]
    assert [(f["tipo_fragmento"], f["articulo"]) for f in cgp] == [
        ("articulo", "6"), ("nota", "6"), ("articulo", "25")]
    assert cgp[0]["texto"].startswith("Código General del Proceso (Ley 1564 de 2012), artículo 6.")

    trans = [f for f in por_id["constitucion_1991"] if f["articulo"] == "T1"][0]
    assert "artículo transitorio 1." in trans["texto"]

    largos = por_id["ley_1150_2007"]
    assert len(largos) >= 3 and all(f["articulo"] == "11" for f in largos)
    assert all("(parte " in f["texto"].split("\n")[0] for f in largos)
    assert all(len(f["texto"].split()) <= 330 for f in largos)

    sent = por_id["sentencia_c-355_2006"]
    assert sent[-1]["seccion"] == "RESUELVE"
    assert sent[0]["texto"].startswith("Sentencia C-355 de 2006 de la Corte Constitucional.")
    assert sent[0]["areas"] == ["Derecho constitucional", "Derecho penal"]


def test_build_rechaza_fuentes_invalidas(tmp_path):
    raiz = tmp_path / "raw"
    raiz.mkdir()
    (raiz / "fuentes.csv").write_text("doc_id\nx\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        construir(raiz, tmp_path / "build")


def test_cli_build_bloquea_fuga(corpus_crudo, tmp_path):
    from src.corpus import build

    salida = tmp_path / "b"
    assert build.main(["--dir", str(corpus_crudo), "--out", str(salida)]) == 0
    assert (salida / "corpus" / "_fuga.json").is_file()
    (corpus_crudo / "banco.jsonl").write_text('{"id": 1, "legal_basis": "x"}\n', encoding="utf-8")
    assert build.main(["--dir", str(corpus_crudo), "--out", str(salida)]) == 1
