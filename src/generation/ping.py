"""Prueba de humo del decoder real: `python -m src.generation.ping [--sin-cache]`.

Carga el modelo configurado (lista blanca, temperatura 0), genera un JSON corto
y reporta tiempos y tokens por segundo.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from src.config import config
from src.generation.llm import LLM

ESQUEMA = {"type": "object",
           "properties": {"respuesta": {"type": "string"},
                          "palabras_clave": {"type": "array", "items": {"type": "string"}}},
           "required": ["respuesta", "palabras_clave"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sin-cache", action="store_true")
    args = ap.parse_args(argv)
    t0 = time.perf_counter()
    llm = LLM()
    carga = time.perf_counter() - t0
    g = llm.generar([
        {"role": "system", "content": "Eres un asistente que responde en español y en JSON."},
        {"role": "user", "content": "En una oración, ¿qué es un contrato? Devuelve 'respuesta' "
                                    "y 'palabras_clave'."},
    ], esquema=ESQUEMA, max_tokens=150, usar_cache=not args.sin_cache)
    print(f"backend={config.decoder_backend} modelo={llm.id_modelo}")
    print(f"carga={carga:.1f}s generación={g.segundos:.1f}s cache={g.desde_cache} "
          f"tokens_prompt={g.tokens_prompt} tokens_salida={g.tokens_salida}")
    if g.tokens_salida and g.segundos:
        print(f"≈ {g.tokens_salida / g.segundos:.1f} tokens/s (incluye lectura del prompt)")
    print(json.dumps(g.datos, ensure_ascii=False))
    return 0 if g.datos else 1


if __name__ == "__main__":
    sys.exit(main())
