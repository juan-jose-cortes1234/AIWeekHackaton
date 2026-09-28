"""Reordenamiento con un cross-encoder abierto (`BAAI/bge-reranker-v2-m3`, Apache-2.0).

Recibe consulta y fragmento juntos y devuelve una pertinencia en [0, 1]
(sigmoide del logit), útil también como señal para la abstención.

Costo medido (2026-09-27): en CPU Ryzen 7 8840HS, ~15 s por 30 pares de ~300
palabras; en GPU es inferior a 1 s. En CPU conviene `RERANK_CANDIDATOS` bajo o
`USE_RERANKER=0`.
"""
from __future__ import annotations

import numpy as np

from src.config import config


class Reranker:
    def __init__(self, nombre: str | None = None, dispositivo: str | None = None,
                 max_length: int = 512, batch_size: int = 16):
        from sentence_transformers import CrossEncoder

        self.nombre = nombre or config.reranker_model
        self.batch_size = batch_size
        self.modelo = CrossEncoder(self.nombre, max_length=max_length,
                                   device=dispositivo or config.encoder_device,
                                   token=config.hf_token or None)

    def puntuar(self, consulta: str, textos: list[str]) -> np.ndarray:
        if not textos:
            return np.zeros(0, dtype=np.float32)
        s = self.modelo.predict([(consulta, t) for t in textos], batch_size=self.batch_size,
                                show_progress_bar=False, convert_to_numpy=True)
        s = np.asarray(s, dtype=np.float32).reshape(-1)
        if s.min() < 0 or s.max() > 1:          # por si el modelo devuelve logits crudos
            s = 1.0 / (1.0 + np.exp(-s))
        return s
