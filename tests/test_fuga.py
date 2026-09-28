"""Pruebas de la guardia anti-fuga."""
import json

from src.config import RAIZ
from src.corpus.build import construir
from src.corpus.fuga import revisar, revisar_crudo, revisar_fragmentos

SAMPLE = RAIZ / "data" / "sample_50.jsonl"


def _muestra():
    return [json.loads(l) for l in SAMPLE.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_corpus_de_prueba_limpio(corpus_crudo, tmp_path):
    construir(corpus_crudo, tmp_path / "build")
    inf = revisar(tmp_path / "build" / "indice" / "chunks.jsonl", corpus_crudo, [SAMPLE])
    assert inf.ok, inf.graves


def test_detecta_pregunta_copiada():
    q = _muestra()[0]
    frag = {"chunk_id": "x#00000", "texto": "Ley 1 de 2000, artículo 1.\n" + q["pregunta"]}
    inf = revisar_fragmentos([frag], [q])
    assert not inf.ok and "x#00000" in inf.graves[0]


def test_detecta_respuesta_esperada_copiada():
    q = next(r for r in _muestra() if r.get("respuesta_esperada"))
    frag = {"chunk_id": "y#00000", "texto": "Doctrina.\n" + q["respuesta_esperada"]}
    inf = revisar_fragmentos([frag], [q])
    assert not inf.ok


def test_coincidencia_menor_solo_para_revision():
    q = {"id": 1, "pregunta": "¿Cuál es el plazo?",
         "respuesta_esperada": " ".join(f"w{i}" for i in range(40))}
    frag = {"chunk_id": "z#00000", "texto": " ".join(f"w{i}" for i in range(10))}
    inf = revisar_fragmentos([frag], [q])
    assert inf.ok and inf.revision


def test_banco_dentro_del_corpus_crudo(corpus_crudo):
    (corpus_crudo / "copia.jsonl").write_text('{"id": 1, "respuesta_esperada": "x"}\n',
                                              encoding="utf-8")
    assert revisar_crudo(corpus_crudo)
