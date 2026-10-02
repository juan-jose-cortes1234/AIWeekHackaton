"""Configuración única del sistema, leída de `.env` en la raíz del repositorio.

Las variables del entorno tienen prioridad sobre el archivo. Las rutas relativas
se resuelven contra la raíz del repo. Los secretos nunca aparecen en `repr`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, fields
from pathlib import Path

from dotenv import dotenv_values

# La GPU es solo para PyTorch (encoder, reranker) y llama.cpp (decoder). Si el entorno
# trae JAX o TensorFlow (p. ej. Colab), bm25s/transformers los importan y XLA reserva el
# 75 % de la VRAM al arrancar, dejando sin memoria al decoder. Se fuerzan a CPU.
for _var, _valor in (("JAX_PLATFORMS", "cpu"), ("XLA_PYTHON_CLIENT_PREALLOCATE", "false"),
                     ("TF_FORCE_GPU_ALLOW_GROWTH", "true"), ("USE_TF", "0"), ("USE_JAX", "0")):
    os.environ.setdefault(_var, _valor)

# La consola de Windows usa cp1252: un "→" en un print tumbaba `src.corpus.build` antes de la
# guardia anti-fuga. Toda salida de consola va en UTF-8 (lo que no se pueda mostrar se reemplaza).
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure") and (_flujo.encoding or "").lower() not in ("utf-8", "utf8"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]

# Lista blanca: solo modelos de pesos y licencia abiertos (enunciado §3.1 y §3.2).
# El sistema corre todo en proceso desde Hugging Face; no hay APIs de terceros.
MODELOS_ABIERTOS = {
    "decoder": {
        "Qwen/Qwen3-8B": "Apache-2.0",
        "Qwen/Qwen3-8B-GGUF": "Apache-2.0",
        # Gemma 4 E4B: 7.996.156.490 parámetros en total con las partes multimodales
        # (safetensors de google/gemma-4-E4B-it), por debajo del límite de 8B del reto.
        "google/gemma-4-E4B-it": "Apache-2.0",
        "ggml-org/gemma-4-E4B-it-GGUF": "Apache-2.0",
        "BSC-LT/salamandra-7b-instruct": "Apache-2.0",
    },
    "encoder": {
        "BAAI/bge-m3": "MIT",
        "intfloat/multilingual-e5-large": "MIT",
    },
    "reranker": {
        "BAAI/bge-reranker-v2-m3": "Apache-2.0",
    },
}
BACKENDS_DECODER = ("llamacpp", "transformers")

SECRETOS = {"openrouter_api_key", "hf_token"}


def _ruta(valor: str) -> Path:
    p = Path(valor).expanduser()
    return p if p.is_absolute() else (RAIZ / p).resolve()


@dataclass(frozen=True)
class Config:
    team_name: str = ""
    openrouter_api_key: str = field(default="", repr=False)

    corpus_raw_dir: Path = RAIZ / "corpus_raw"
    corpus_out_dir: Path = RAIZ / "build" / "corpus"
    index_dir: Path = RAIZ / "build" / "indice"
    corpus_source: str = "auto"
    corpus_zip_url: str = ""
    corpus_zip_sha256: str = ""

    encoder_model: str = "BAAI/bge-m3"
    encoder_device: str = "cpu"
    encoder_max_length: int = 512
    encoder_batch_size: int = 16
    use_reranker: bool = True
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_candidatos: int = 20
    top_k_pasajes: int = 10
    pasajes_prompt: int = 10
    palabras_por_pasaje: int = 0      # 0 = pasajes completos (flujo final)
    candidatos: int = 50
    rrf_k: int = 60
    peso_denso: float = 1.0
    peso_bm25: float = 1.0
    boost_area: float = 0.002
    boost_cuerpo: float = 0.01
    max_por_articulo: int = 3
    puestos_pregunta: int = 4         # MC: puestos para la pregunta; el resto, por opción
    pasajes_por_opcion: int = 2       # MC: pasajes de cada opción a considerar por ronda
    rerank_candidatos_opcion: int = 8 # MC: candidatos que el reranker reordena por opción
    mc_analisis_previo: bool = False  # MC: True = analizar cada opción antes de elegir (C-03)
    mc_modo: str = "directo"           # MC: "directo" = elegir con las opciones a la vista; "abierta" = responder sin opciones y luego elegir (C-08, descartado por latencia)
    mc_razonamiento_tokens: int = 0     # MC: tope del modo de razonamiento de Qwen3 (C-09; apagado: ganancia inestable, menos citas y el doble de tiempo); >0 lo activa
    mc_consulta_opcion: str = "clave"  # MC: "clave" = opción + palabras clave de la pregunta; "pregunta" = pregunta completa + opción (C-03)
    mc_palabras_clave: int = 10       # MC: palabras de la pregunta que acompañan a cada opción (modo "clave")
    max_por_documento: int = 4        # 0 = sin tope; no aplica a documentos mencionados
    cuota_normas: int = 4             # pasajes reservados a normas (no sentencias ni conceptos) entre los 10 (C-14); 0 = sin cupo
    max_complementarios: int = 0      # pasajes de documentos complementarios entre los 10 (C-10; 0 = sin tope, decisión 2026-10-02)
    documentos_complementarios: Path = RAIZ / "config" / "documentos_complementarios.txt"
    umbral_cita: float = 0.5
    max_referencias: int = 6
    umbral_abstencion: float = 0.0     # texto libre: 0 = sin abstención por baja pertinencia (C-13, pesos oficiales)
    umbral_abstencion_denso: float = 0.0  # ídem cuando no hay reranker (antes 0.35)

    decoder_backend: str = "llamacpp"
    decoder_model: str = "google/gemma-4-E4B-it"          # C-15 (antes Qwen/Qwen3-8B)
    decoder_gguf_repo: str = "ggml-org/gemma-4-E4B-it-GGUF"  # antes Qwen/Qwen3-8B-GGUF
    decoder_gguf_file: str = "gemma-4-E4B-it-Q8_0.gguf"      # antes Qwen3-8B-Q4_K_M.gguf
    decoder_device: str = "cpu"
    decoder_temperature: float = 0.0
    decoder_seed: int = 42
    decoder_num_ctx: int = 8192
    decoder_threads: int = 0

    hf_token: str = field(default="", repr=False)

    def __repr__(self) -> str:
        partes = []
        for f in fields(self):
            v = getattr(self, f.name)
            if f.name in SECRETOS:
                v = "***" if v else ""
            partes.append(f"{f.name}={v!r}")
        return "Config(" + ", ".join(partes) + ")"

    __str__ = __repr__

    @property
    def fuente_corpus(self) -> str:
        """Modo efectivo del corpus: 'nube' o 'local' (resuelve 'auto')."""
        if self.corpus_source in ("nube", "local"):
            return self.corpus_source
        return "nube" if self.corpus_zip_url else "local"

    def validar_final(self) -> None:
        """Reglas que deben cumplirse en una ejecución calificable."""
        if self.decoder_temperature != 0:
            raise ValueError("DECODER_TEMPERATURE debe ser 0 en la ejecución final.")
        if self.corpus_source not in ("auto", "nube", "local"):
            raise ValueError("CORPUS_SOURCE debe ser auto, nube o local.")
        if self.decoder_backend not in BACKENDS_DECODER:
            raise ValueError(f"DECODER_BACKEND debe ser uno de {BACKENDS_DECODER}.")
        self.validar_modelos()

    def validar_modelos(self) -> None:
        """Rechaza cualquier modelo fuera de la lista blanca de modelos abiertos."""
        decoder = (self.decoder_gguf_repo if self.decoder_backend == "llamacpp"
                   else self.decoder_model)
        for tipo, nombre in (("decoder", decoder), ("encoder", self.encoder_model),
                             ("reranker", self.reranker_model)):
            if nombre not in MODELOS_ABIERTOS[tipo]:
                raise ValueError(
                    f"{tipo} '{nombre}' no está en la lista blanca de modelos abiertos "
                    f"({sorted(MODELOS_ABIERTOS[tipo])}). Solo se admiten modelos de licencia "
                    "abierta; para añadir uno, verifique su licencia y agréguelo en src/config.py.")


def _convertir(tipo, valor: str):
    if tipo in (bool, "bool"):
        return valor.strip().lower() in ("1", "true", "si", "sí", "yes")
    if tipo in (int, "int"):
        return int(valor)
    if tipo in (float, "float"):
        return float(valor)
    if tipo in (Path, "Path"):
        return _ruta(valor)
    return valor.strip()


def cargar(env_path: Path | None = None) -> Config:
    """Construye la configuración desde `.env` (si existe) y el entorno."""
    archivo = dotenv_values(env_path or RAIZ / ".env") if (env_path or RAIZ / ".env").is_file() else {}
    valores = {}
    for f in fields(Config):
        clave = f.name.upper()
        crudo = os.environ.get(clave) or archivo.get(clave)
        if crudo is None or str(crudo).strip() == "":
            continue
        valores[f.name] = _convertir(f.type, str(crudo))
    return Config(**valores)


config = cargar()
