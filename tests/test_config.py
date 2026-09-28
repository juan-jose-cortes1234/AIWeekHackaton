"""Pruebas de src/config.py."""
from pathlib import Path

import pytest

from src.config import RAIZ, cargar


def _env(tmp_path: Path, contenido: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(contenido, encoding="utf-8")
    return p


def test_repr_enmascara_secretos(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = cargar(_env(tmp_path, "OPENROUTER_API_KEY=sk-secreta-123\nHF_TOKEN=hf_abc\n"))
    assert cfg.openrouter_api_key == "sk-secreta-123"
    texto = repr(cfg) + str(cfg)
    assert "sk-secreta-123" not in texto and "hf_abc" not in texto
    assert "openrouter_api_key='***'" in texto


def test_tipos_y_rutas(tmp_path, monkeypatch):
    for v in ("TOP_K_PASAJES", "USE_RERANKER", "CORPUS_RAW_DIR", "DECODER_TEMPERATURE"):
        monkeypatch.delenv(v, raising=False)
    cfg = cargar(_env(tmp_path, "TOP_K_PASAJES=7\nUSE_RERANKER=0\nCORPUS_RAW_DIR=./otra\nDECODER_TEMPERATURE=0\n"))
    assert cfg.top_k_pasajes == 7
    assert cfg.use_reranker is False
    assert cfg.corpus_raw_dir == (RAIZ / "otra").resolve()
    assert cfg.decoder_temperature == 0.0


def test_entorno_tiene_prioridad(tmp_path, monkeypatch):
    monkeypatch.setenv("DECODER_MODEL", "desde-entorno")
    cfg = cargar(_env(tmp_path, "DECODER_MODEL=desde-archivo\n"))
    assert cfg.decoder_model == "desde-entorno"


def test_fuente_corpus_auto(tmp_path, monkeypatch):
    monkeypatch.delenv("CORPUS_ZIP_URL", raising=False)
    monkeypatch.delenv("CORPUS_SOURCE", raising=False)
    assert cargar(_env(tmp_path, "")).fuente_corpus == "local"
    assert cargar(_env(tmp_path, "CORPUS_ZIP_URL=https://x/y.zip\n")).fuente_corpus == "nube"


def test_validar_final_exige_temperatura_cero(tmp_path, monkeypatch):
    monkeypatch.setenv("DECODER_TEMPERATURE", "0.7")
    with pytest.raises(ValueError):
        cargar(_env(tmp_path, "")).validar_final()


def test_lista_blanca_acepta_los_modelos_por_defecto(tmp_path, monkeypatch):
    for v in ("DECODER_BACKEND", "DECODER_MODEL", "DECODER_GGUF_REPO", "ENCODER_MODEL",
              "RERANKER_MODEL", "DECODER_TEMPERATURE"):
        monkeypatch.delenv(v, raising=False)
    cargar(_env(tmp_path, "")).validar_final()


@pytest.mark.parametrize("linea", [
    "DECODER_BACKEND=transformers\nDECODER_MODEL=gpt-4o\n",
    "DECODER_GGUF_REPO=google/gemini\n",
    "ENCODER_MODEL=jinaai/jina-embeddings-v3\n",
    "RERANKER_MODEL=cohere/rerank-3\n",
    "DECODER_BACKEND=openai_compat\n",
])
def test_lista_blanca_rechaza_modelos_cerrados(tmp_path, monkeypatch, linea):
    for v in ("DECODER_BACKEND", "DECODER_MODEL", "DECODER_GGUF_REPO", "ENCODER_MODEL",
              "RERANKER_MODEL", "DECODER_TEMPERATURE"):
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(ValueError):
        cargar(_env(tmp_path, linea)).validar_final()
