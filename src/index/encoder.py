"""Encoder abierto con caché de embeddings por hash del texto.

- Vectores normalizados (producto interno = coseno), float32.
- Prefijos `query: ` / `passage: ` si el modelo es de la familia E5 (enunciado B.2).
- La caché (`build/cache/emb/<modelo>.npz`) evita recalcular los fragmentos que
  no cambiaron al añadir documentos: en CPU el embedding es la etapa más cara.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Protocol

import numpy as np

from src.config import RAIZ, config

DIR_CACHE = RAIZ / "build" / "cache" / "emb"


class Codificador(Protocol):
    nombre: str
    dimension: int

    def codificar(self, textos: list[str], es_consulta: bool) -> np.ndarray: ...


def _es_e5(nombre: str) -> bool:
    return "e5" in nombre.lower()


class EncoderST:
    """Envoltura de sentence-transformers para el encoder configurado."""

    def __init__(self, nombre: str | None = None, dispositivo: str | None = None,
                 max_length: int | None = None, batch_size: int | None = None):
        from sentence_transformers import SentenceTransformer

        self.nombre = nombre or config.encoder_model
        self.batch_size = batch_size or config.encoder_batch_size
        self.modelo = SentenceTransformer(self.nombre, device=dispositivo or config.encoder_device,
                                          token=config.hf_token or None)
        self.modelo.max_seq_length = max_length or config.encoder_max_length
        self.max_length = self.modelo.max_seq_length
        dim = (getattr(self.modelo, "get_embedding_dimension", None)
               or self.modelo.get_sentence_embedding_dimension)
        self.dimension = int(dim())

    def _prefijar(self, textos: list[str], es_consulta: bool) -> list[str]:
        if not _es_e5(self.nombre):
            return textos
        p = "query: " if es_consulta else "passage: "
        return [p + t for t in textos]

    def codificar(self, textos: list[str], es_consulta: bool = False) -> np.ndarray:
        if not textos:
            return np.zeros((0, self.dimension), dtype=np.float32)
        v = self.modelo.encode(self._prefijar(textos, es_consulta), batch_size=self.batch_size,
                               normalize_embeddings=True, convert_to_numpy=True,
                               show_progress_bar=len(textos) > 256)
        return v.astype(np.float32)


def _slug(nombre: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", nombre).strip("_").lower()


def hash_texto(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


class CacheEmbeddings:
    """Caché persistente {sha256(texto) → vector} por modelo."""

    def __init__(self, nombre_modelo: str, directorio: Path | None = None):
        self.ruta = (directorio or DIR_CACHE) / f"{_slug(nombre_modelo)}.npz"
        self.vectores: dict[str, np.ndarray] = {}
        if self.ruta.is_file():
            datos = np.load(self.ruta, allow_pickle=False)
            for k, v in zip(datos["claves"], datos["vectores"]):
                self.vectores[str(k)] = v

    def guardar(self) -> None:
        if not self.vectores:
            return
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        claves = sorted(self.vectores)
        np.savez(self.ruta, claves=np.array(claves),
                 vectores=np.stack([self.vectores[k] for k in claves]).astype(np.float32))

    def codificar_pasajes(self, enc: Codificador, textos: list[str]) -> tuple[np.ndarray, int]:
        """Vectores de los pasajes en orden; devuelve también cuántos se calcularon."""
        claves = [hash_texto(t) for t in textos]
        faltan = sorted({k: t for k, t in zip(claves, textos) if k not in self.vectores}.items())
        if faltan:
            nuevos = enc.codificar([t for _, t in faltan], es_consulta=False)
            for (k, _), v in zip(faltan, nuevos):
                self.vectores[k] = v
        if not textos:
            return np.zeros((0, enc.dimension), dtype=np.float32), 0
        return np.stack([self.vectores[k] for k in claves]).astype(np.float32), len(faltan)
