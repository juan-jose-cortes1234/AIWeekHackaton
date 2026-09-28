"""Acceso a los módulos del evaluador oficial (`scripts/citations.py`, `scripts/common.py`).

El sistema usa exactamente el mismo extractor de citas que el jurado, para que
el respaldo que calculamos coincida con el que calcula `evaluate.py`.
"""
from __future__ import annotations

import sys

from src.config import RAIZ

_SCRIPTS = str(RAIZ / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import citations  # noqa: E402
import common  # noqa: E402

AREAS: list[str] = list(common.AREAS)
AREA_SLUG: dict[str, str] = dict(common.AREA_SLUG)

__all__ = ["citations", "common", "AREAS", "AREA_SLUG"]
