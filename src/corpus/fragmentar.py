"""Encabezado canónico y fragmentos finales que se indexan.

Cada fragmento empieza con el nombre de su norma en una forma que
`scripts/citations.py` (el extractor del jurado) reconoce. Sin eso, las citas
del sistema no cuentan como respaldadas aunque la recuperación sea correcta.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.corpus.fuentes import Fuente
from src.corpus.segmentar import Segmento, ventanas
from src.oficial import citations

MAX_PALABRAS = 300   # ~450 tokens de bge-m3: deja margen al encabezado dentro de 512
SOLAPE = 0.15

_BASE_POR_TIPO = {
    "ley": "Ley {n} de {a}",
    "decreto": "Decreto {n} de {a}",
    "decreto_ley": "Decreto Ley {n} de {a}",
    "acto_legislativo": "Acto Legislativo {n} de {a}",
    "resolucion": "Resolución {n} de {a}",
    "circular": "Circular {n} de {a}",
    "sentencia": "Sentencia {n} de {a}",
    "decision_andina": "Decisión {n} de la Comisión de la Comunidad Andina",
}
_ALIAS = dict(citations._ALIAS_NUM)


@dataclass
class Fragmento:
    doc_id: str
    texto: str
    tipo_fragmento: str
    articulo: str | None
    seccion: str | None
    parte: int = 1
    partes: int = 1
    meta: dict = field(default_factory=dict)


def _limpio(s: str) -> str:
    return citations.norm(s)


def nombre_canonico(f: Fuente) -> str:
    """Nombre con el que se encabeza cada fragmento del documento."""
    if f.tipo == "constitucion":
        return "Constitución Política de Colombia"
    if f.tipo == "codigo":
        if "(" in f.titulo or not (f.numero and f.anio):
            return f.titulo
        for kind, palabra in (("ley", "Ley"), ("decreto", "Decreto")):
            if (kind, f.numero.lstrip("0")) in _ALIAS:
                return f"{f.titulo} ({palabra} {f.numero} de {f.anio})"
        return f.titulo
    plantilla = _BASE_POR_TIPO.get(f.tipo)
    if not plantilla:
        return f.titulo
    base = plantilla.format(n=f.numero, a=f.anio)
    if f.tipo == "sentencia":
        return f"{base} de la {f.organo_emisor}" if f.organo_emisor else base
    if _limpio(base) in _limpio(f.titulo) or _limpio(f.titulo) in _limpio(base):
        return base
    return f"{f.titulo} ({base})"


def cuerpos(texto: str) -> set[tuple]:
    """Cuerpos normativos que el evaluador extrae de un texto."""
    return citations.bodies(citations.extract(texto))


def cuerpos_documento(f: Fuente) -> set[tuple]:
    return cuerpos(nombre_canonico(f))


def _ref_articulo(art: str) -> str:
    if art.startswith("T"):
        return f"artículo transitorio {art[1:]}"
    return f"artículo {art}"


def encabezado(f: Fuente, s: Segmento) -> str:
    nombre = nombre_canonico(f)
    if s.tipo == "articulo":
        return f"{nombre}, {_ref_articulo(s.articulo)}."
    if s.tipo == "nota":
        return f"{nombre}, {_ref_articulo(s.articulo)} (notas de vigencia y jurisprudencia)."
    if s.tipo == "preambulo":
        return f"{nombre} (encabezado)."
    return f"{nombre}. [{s.seccion}]" if s.seccion else f"{nombre}."


def fragmentar(f: Fuente, segmentos: list[Segmento]) -> list[Fragmento]:
    """Convierte segmentos en fragmentos con encabezado, partiendo los largos."""
    res: list[Fragmento] = []
    for s in segmentos:
        cab = encabezado(f, s)
        if len(s.texto.split()) <= MAX_PALABRAS:
            trozos = [s.texto]
        else:
            parrafos = [p for p in re.split(r"\n+", s.texto) if p.strip()]
            trozos = ventanas(parrafos, MAX_PALABRAS, SOLAPE)
        for k, t in enumerate(trozos, start=1):
            cab_k = cab if len(trozos) == 1 else f"{cab} (parte {k} de {len(trozos)})"
            res.append(Fragmento(
                doc_id=f.doc_id, texto=f"{cab_k}\n{t.strip()}", tipo_fragmento=s.tipo,
                articulo=s.articulo, seccion=s.seccion, parte=k, partes=len(trozos)))
    return res
