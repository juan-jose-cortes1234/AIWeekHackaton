"""Pruebas del manifiesto y de las tablas AUTO de CORPUS.md."""
import json
import shutil

from src.config import RAIZ
from src.corpus import manifest
from src.corpus.build import construir

CAMPOS_OFICIALES = {"doc_id", "titulo", "fuente", "url", "fecha_consulta", "areas"}


def test_manifest_y_corpus_md(corpus_crudo, tmp_path):
    salida = tmp_path / "build"
    construir(corpus_crudo, salida)
    md = tmp_path / "CORPUS.md"
    shutil.copy(RAIZ / "CORPUS.md", md)
    man = tmp_path / "corpus_manifest.json"

    rc = manifest.main(["--resumen", str(salida / "corpus" / "_resumen.json"),
                        "--manifest", str(man), "--corpus-md", str(md)])
    assert rc == 0

    datos = json.loads(man.read_text(encoding="utf-8"))
    assert datos["licencia"] == "CC-BY-4.0"
    assert len(datos["documentos"]) == 6
    for d in datos["documentos"]:
        assert CAMPOS_OFICIALES <= d.keys()
        assert len(d["sha256"]) == 64
    cgp = next(d for d in datos["documentos"] if d["doc_id"] == "ley_1564_2012")
    assert cgp["metodo_ingesta"] == "parser HTML + segmentacion por articulo"
    sent = next(d for d in datos["documentos"] if d["doc_id"] == "sentencia_c-355_2006")
    assert sent["metodo_ingesta"].endswith("segmentacion por seccion")

    texto = md.read_text(encoding="utf-8")
    assert "`ley_1150_2007`" in texto and "Aún no hay corpus" not in texto
    assert "| Documentos incorporados | 6 |" in texto
    assert "Derecho constitucional | 134 |" in texto
    assert "BORRADOR" in texto                      # la prosa del equipo no se toca

    # Idempotente: regenerar no duplica bloques.
    manifest.main(["--resumen", str(salida / "corpus" / "_resumen.json"),
                   "--manifest", str(man), "--corpus-md", str(md)])
    assert md.read_text(encoding="utf-8") == texto


def test_cobertura_seed_cuenta_normas_presentes(corpus_crudo, tmp_path):
    total = construir(corpus_crudo, tmp_path / "build")
    cob = manifest.cobertura_seed(total, RAIZ / "data" / "seed_targets.json")
    cubiertos, totales = cob["Derecho constitucional"]
    # La Constitución (90 ítems en el seed) y C-355/2006 están en el corpus de prueba.
    assert cubiertos >= 97 and totales > cubiertos
