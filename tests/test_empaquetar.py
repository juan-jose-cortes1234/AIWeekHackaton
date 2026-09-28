"""Pruebas del empaquetado: estructura oficial, determinismo e ida y vuelta con la descarga."""
import dataclasses
import json
import zipfile

import pytest

from src.config import config
from src.corpus import manifest as man
from src.corpus.empaquetar import ErrorEmpaquetado, empaquetar
from src.corpus.nube import extraer, validar_zip
from src.retrieval.hibrido import Recuperador


@pytest.fixture
def cfg_prueba(indice_prueba, tmp_path):
    build, _ = indice_prueba
    manifiesto = tmp_path / "corpus_manifest.json"
    resumen = json.loads((build / "corpus" / "_resumen.json").read_text(encoding="utf-8"))
    manifiesto.write_text(json.dumps(man.construir_manifiesto(resumen)), encoding="utf-8")
    cfg = dataclasses.replace(config, corpus_out_dir=build / "corpus", index_dir=build / "indice",
                              team_name="Los Juristas 2026")
    return cfg, manifiesto


def test_estructura_y_determinismo(cfg_prueba, tmp_path):
    cfg, manifiesto = cfg_prueba
    r1 = empaquetar(cfg, tmp_path / "a.zip", manifiesto)
    r2 = empaquetar(cfg, tmp_path / "b.zip", manifiesto)
    assert r1["sha256"] == r2["sha256"]                      # mismo contenido ⇒ mismo hash
    with zipfile.ZipFile(r1["zip"]) as z:
        nombres = z.namelist()
        assert "LICENSE" in nombres and "corpus_manifest.json" in nombres
        assert b"Attribution 4.0 International" in z.read("LICENSE")
    for req in ("indice/index.faiss", "indice/chunks.jsonl", "indice/index_manifest.json"):
        assert req in nombres
    assert any(n.startswith("indice/bm25/") for n in nombres)
    assert any(n.startswith("corpus/") and n.endswith(".txt") for n in nombres)
    assert not any(n.endswith(".origen_nube.json") for n in nombres)
    assert validar_zip(r1["zip"], cfg) == ""


def test_nombre_por_equipo(cfg_prueba, monkeypatch, tmp_path):
    cfg, manifiesto = cfg_prueba
    monkeypatch.setattr("src.corpus.empaquetar.RAIZ", tmp_path)
    r = empaquetar(cfg, manifiesto=manifiesto)
    assert r["zip"].name == "corpus_los_juristas_2026.zip"


def test_ida_y_vuelta(cfg_prueba, tmp_path, encoder_real, reranker_real, indice_prueba):
    cfg, manifiesto = cfg_prueba
    r = empaquetar(cfg, tmp_path / "c.zip", manifiesto)
    destino = dataclasses.replace(cfg, corpus_out_dir=tmp_path / "x" / "corpus",
                                  index_dir=tmp_path / "x" / "indice")
    extraer(r["zip"], validar_zip(r["zip"], destino), destino)
    rec2 = Recuperador.cargar(destino.index_dir, encoder=encoder_real, reranker=reranker_real)
    q = "sociedad conyugal"
    assert [p.chunk_id for p in rec2.buscar(q)] == [p.chunk_id for p in indice_prueba[1].buscar(q)]


def test_rechaza_indice_desactualizado(cfg_prueba, tmp_path):
    cfg, manifiesto = cfg_prueba
    copia = tmp_path / "idx"
    import shutil

    shutil.copytree(cfg.index_dir, copia)
    with (copia / "chunks.jsonl").open("a", encoding="utf-8") as fh:
        fh.write("\n")
    with pytest.raises(ErrorEmpaquetado, match="desactualizado"):
        empaquetar(dataclasses.replace(cfg, index_dir=copia), tmp_path / "d.zip", manifiesto)
