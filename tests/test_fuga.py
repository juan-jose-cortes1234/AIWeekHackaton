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


def test_pregunta_y_respuesta_juntas_es_grave():
    q = next(r for r in _muestra() if r.get("respuesta_esperada") and len(r["pregunta"].split()) > 12)
    frag = {"chunk_id": "x#00000", "texto": q["pregunta"] + "\n" + q["respuesta_esperada"]}
    inf = revisar_fragmentos([frag], [q])
    assert not inf.ok and "pregunta y respuesta" in inf.graves[0]


def test_lista_de_preguntas_es_grave():
    qs = [r for r in _muestra() if len(r["pregunta"].split()) > 12][:3]
    frag = {"chunk_id": "banco#00000", "texto": "\n".join(q["pregunta"] for q in qs)}
    inf = revisar_fragmentos([frag], qs)
    assert not inf.ok and any("preguntas distintas" in g for g in inf.graves)


def test_cita_literal_de_una_norma_solo_para_revision():
    # Una respuesta esperada que reproduce un artículo: la norma oficial la contiene.
    q = next(r for r in _muestra() if r.get("respuesta_esperada"))
    frag = {"chunk_id": "norma#00000", "texto": "Código Civil, artículo 1.\n" + q["respuesta_esperada"]}
    inf = revisar_fragmentos([frag], [q])
    assert inf.ok and inf.revision
    solo_preg = {"chunk_id": "norma#00001", "texto": q["pregunta"]}
    inf2 = revisar_fragmentos([solo_preg], [q])
    assert inf2.ok


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
