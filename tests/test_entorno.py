"""Prueba de humo del entorno: dependencias clave y evaluador oficial importables."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_version_python():
    assert sys.version_info >= (3, 10)


def test_dependencias_importables():
    import bm25s  # noqa: F401
    import faiss  # noqa: F401
    import jsonschema  # noqa: F401
    import sentence_transformers  # noqa: F401


def test_evaluador_oficial_importable():
    sys.path.insert(0, str(RAIZ / "scripts"))
    import citations

    cuerpos = citations.bodies(citations.extract("Artículo 11 de la Ley 1150 de 2007"))
    assert ("ley", "1150", "2007") in cuerpos
