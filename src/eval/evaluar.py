"""Evaluador oficial con las llamadas al juez espaciadas (solo para mediciones internas).

    python -m src.eval.evaluar --submission runs/<tag>/submissions.jsonl --split sample --ragas \
        --out runs/<tag>/reporte_ragas_espaciado.json

Ejecuta `scripts/evaluate.py` **sin copiarlo ni modificarlo**, con los mismos argumentos que
recibiría directamente: misma validación, mismas métricas, mismo juez, mismo encoder, misma
fórmula y mismo reporte. Lo único distinto es cómo RAGAS hace las llamadas al juez: el
evaluador oficial deja los valores por defecto de RAGAS (hasta 16 llamadas simultáneas, 180 s
por ítem) y, cuando la red o el proveedor fallan, ese ítem queda sin veredicto y cuenta como
cero (en muestra_v3, v4 y v6 fallaron 6, 21 y 7 de 33 por `TimeoutError` y
`OpenAIConnectionError`). Aquí se le pasa a RAGAS un `run_config` con menos llamadas
simultáneas, más tiempo y reintentos.

Opciones propias (el resto se pasa tal cual al evaluador oficial):
    --hilos N        llamadas simultáneas al juez (por defecto 4; RAGAS usa 16)
    --timeout S      segundos por ítem (por defecto 600; RAGAS usa 180)
    --reintentos N   reintentos por llamada fallida (por defecto 10)

El jurado califica con `scripts/evaluate.py` en su entorno; esto solo sirve para que nuestras
comparaciones entre corridas no dependan de los fallos de red.
"""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EVALUADOR = RAIZ / "scripts" / "evaluate.py"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--reintentos", type=int, default=10)
    propios, resto = ap.parse_known_args(argv)

    if "--ragas" in resto:
        try:
            import ragas
            from ragas.run_config import RunConfig
        except ImportError:
            print("Falta RAGAS: pip install -r scripts/requirements-evaluador.txt")
            return 1
        original = ragas.evaluate
        config = RunConfig(max_workers=propios.hilos, timeout=propios.timeout,
                           max_retries=propios.reintentos)

        def evaluate_espaciado(*args, **kwargs):
            kwargs.setdefault("run_config", config)
            return original(*args, **kwargs)

        # evaluate.py hace `from ragas import evaluate` dentro de score_ragas, en el momento de
        # calificar: toma esta versión, que solo añade el run_config.
        ragas.evaluate = evaluate_espaciado
        print(f"Juez espaciado: {propios.hilos} llamadas simultáneas, {propios.timeout} s por ítem, "
              f"{propios.reintentos} reintentos.", flush=True)

    sys.argv = [str(EVALUADOR), *resto]
    sys.path.insert(0, str(EVALUADOR.parent))      # como al correrlo directamente
    try:
        runpy.run_path(str(EVALUADOR), run_name="__main__")
    except SystemExit as e:
        return int(e.code or 0) if not isinstance(e.code, str) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
