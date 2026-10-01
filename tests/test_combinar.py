"""Pruebas del combinador de corridas (datos inventados)."""
import json

import pytest

from src.eval.combinar import combinar


def _escribir(carpeta, filas):
    carpeta.mkdir(parents=True)
    (carpeta / "submissions.jsonl").write_text(
        "".join(json.dumps(f) + "\n" for f in filas), encoding="utf-8")


def test_reemplaza_por_id_y_respeta_el_orden(tmp_path):
    _escribir(tmp_path / "base", [{"id": 1, "r": "a"}, {"id": 2, "r": "b"}, {"id": 3, "r": "c"}])
    _escribir(tmp_path / "parcial", [{"id": 3, "r": "C"}, {"id": 1, "r": "A"}])
    assert combinar(tmp_path / "base", tmp_path / "parcial", tmp_path / "out") == (3, 2)
    filas = [json.loads(l) for l in (tmp_path / "out" / "submissions.jsonl").read_text().splitlines()]
    assert [(f["id"], f["r"]) for f in filas] == [(1, "A"), (2, "b"), (3, "C")]


def test_id_ajeno_a_la_base(tmp_path):
    _escribir(tmp_path / "base", [{"id": 1}])
    _escribir(tmp_path / "parcial", [{"id": 9}])
    with pytest.raises(SystemExit):
        combinar(tmp_path / "base", tmp_path / "parcial", tmp_path / "out")
