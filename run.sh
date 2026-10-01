#!/usr/bin/env bash
# Comando único de reproducción. Uso: bash run.sh [--split sample|test] [--limite N]
#   [--rango INICIO FIN] [--tag NOMBRE] [--gpu] [--indice-existente] [--sin-ragas]
# Ej. en una GPU con el índice ya en build/: bash run.sh --split test --gpu --indice-existente --rango 1 250 --tag sabado_1
set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${EN_CONTENEDOR:-}" ]; then
  # Fuera de Docker: entorno virtual propio (Python >= 3.10).
  PY="${PYTHON:-python3}"
  command -v "$PY" >/dev/null 2>&1 || PY=python
  if [ ! -d .venv ]; then
    "$PY" -m venv .venv
  fi
  if [ -f .venv/bin/activate ]; then . .venv/bin/activate; else . .venv/Scripts/activate; fi
fi

export PYTHONIOENCODING=utf-8
exec python run.py "$@"
