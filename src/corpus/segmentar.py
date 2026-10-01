"""Segmentación del texto limpio en unidades con sentido jurídico.

- Normas (constitución, códigos, leyes, decretos…): un segmento por **artículo**.
  Las notas del editor que publica la Secretaría del Senado (vigencia,
  jurisprudencia, legislación anterior) salen como segmento aparte de tipo
  `nota`, ligado a su artículo; las "Concordancias" se descartan (son listas de
  referencias que meten ruido en la recuperación).
- Sentencias y conceptos: por **secciones** (antecedentes, consideraciones,
  resuelve…) y, dentro de cada sección, ventanas de ~300 palabras con solape que
  respetan los párrafos. El RESUELVE siempre queda en segmentos propios.

La partición por longitud máxima del encoder y el encabezado canónico se hacen
después, en `src.corpus.fragmentar`.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# ARTÍCULO 1o. · ARTICULO 11A. · Artículo 5 bis. · ART. 20. · ARTÍCULO 240-1. ·
# Artículo 2.2.1.1.1. (decretos únicos) · ARTICULO TRANSITORIO 3o. · ARTÍCULO 1o. TRANSITORIO.
ARTICULO_RE = re.compile(
    r"^(?:ART[IÍ]CULO|ART\.)\s+"
    r"(?P<trans1>TRANSITORIO\s+)?"
    r"(?P<num>\d{1,5}(?:\.\d{1,4})*(?:-\d{1,3})?)"
    r"\s*(?:[oº°](?![a-záéíóúñ]))?\.?\s*"
    r"(?P<letra>[A-Z](?![a-záéíóúñ\w]))?\s*"
    r"(?P<bis>bis|ter|quater)?\s*"
    r"(?P<trans2>TRANSITORIO)?\s*"
    r"(?P<fin>[\.\-:–—]|$)",
    re.IGNORECASE,
)
ENCABEZADO_ESTRUCTURA_RE = re.compile(
    r"^(LIBRO|PARTE|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N|SUBSECCI[OÓ]N)\s+[\wÁÉÍÓÚ]+", re.IGNORECASE)
NOTA_RE = re.compile(
    r"^(notas? de vigencia|jurisprudencia vigencia|jurisprudencia concordante|notas? del editor|"
    r"legislaci[oó]n anterior|texto original|notas? de la relator[ií]a)\s*:?\s*$", re.IGNORECASE)
CONCORDANCIA_RE = re.compile(r"^(concordancias|doctrina concordante)\s*:?\s*$", re.IGNORECASE)


PALABRAS_VENTANA = 300
SOLAPE = 0.15


@dataclass
class Segmento:
    tipo: str                 # articulo | nota | preambulo | seccion
    texto: str
    articulo: str | None = None
    seccion: str | None = None
    orden: int = 0


def id_articulo(m: re.Match) -> str:
    """Identificador normalizado del artículo: '11A', '5 bis', '240-1', 'T3'."""
    num = m.group("num")
    if m.group("letra"):
        num += m.group("letra").upper()
    if m.group("bis"):
        num += " " + m.group("bis").lower()
    if m.group("trans1") or m.group("trans2"):
        num = "T" + num
    return num


def _es_articulo(linea: str) -> re.Match | None:
    m = ARTICULO_RE.match(linea)
    if not m:
        return None
    # "Artículo 5 de la Ley…" empieza igual pero no es encabezado: exige un
    # terminador (., -, :) o que la línea termine tras el número.
    return m


# --------------------------------------------------------------------------- normas

def segmentar_norma(texto: str) -> list[Segmento]:
    segs: list[Segmento] = []
    seccion: str | None = None
    actual: dict | None = None      # {"art", "cuerpo": [...], "nota": [...], "modo"}
    preambulo: list[str] = []
    vistos: set[str] = set()
    lineas = texto.split("\n")

    def cerrar():
        nonlocal actual
        if actual is None:
            return
        cuerpo = "\n".join(actual["cuerpo"]).strip()
        if cuerpo:
            segs.append(Segmento("articulo", cuerpo, actual["art"], actual["seccion"]))
        nota = "\n".join(actual["nota"]).strip()
        if nota:
            segs.append(Segmento("nota", nota, actual["art"], actual["seccion"]))
        actual = None

    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        m = _es_articulo(linea) if linea else None
        if m:
            art = id_articulo(m)
            if art in vistos and actual is not None:
                # Repetición (texto anterior citado en una nota): va a la nota.
                actual["nota"].append(linea)
                actual["modo"] = "nota"
                i += 1
                continue
            cerrar()
            vistos.add(art)
            actual = {"art": art, "cuerpo": [linea], "nota": [], "modo": "cuerpo",
                      "seccion": seccion}
        elif linea and ENCABEZADO_ESTRUCTURA_RE.match(linea) and len(linea) <= 160:
            titulo = linea
            sig = lineas[i + 1].strip() if i + 1 < len(lineas) else ""
            if sig and sig.isupper() and not _es_articulo(sig) and len(sig) <= 160:
                titulo += " " + sig
                i += 1
            seccion = titulo
            if actual is not None:
                actual["modo"] = "cuerpo_cerrado"
        elif actual is None:
            preambulo.append(lineas[i])
        elif linea and NOTA_RE.match(linea):
            actual["modo"] = "nota"
            actual["nota"].append(linea)
        elif linea and CONCORDANCIA_RE.match(linea):
            actual["modo"] = "descartar"
        else:
            if actual["modo"] == "cuerpo":
                actual["cuerpo"].append(lineas[i])
            elif actual["modo"] == "nota":
                actual["nota"].append(lineas[i])
            elif actual["modo"] == "descartar" and not linea:
                pass  # las concordancias terminan cuando aparece otra nota o artículo
        i += 1
    cerrar()

    pre = "\n".join(preambulo).strip()
    if pre:
        segs.insert(0, Segmento("preambulo", pre))
    for n, s in enumerate(segs):
        s.orden = n
    return segs


# --------------------------------------------------------------------------- sentencias

def ventanas(parrafos: list[str], palabras: int = PALABRAS_VENTANA,
             solape: float = SOLAPE) -> list[str]:
    """Agrupa párrafos en ventanas de ~`palabras` con solape; parte párrafos enormes."""
    unidades: list[str] = []
    for p in parrafos:
        toks = p.split()
        if len(toks) <= palabras:
            unidades.append(p)
        else:
            paso = max(1, int(palabras * (1 - solape)))
            for k in range(0, len(toks), paso):
                unidades.append(" ".join(toks[k:k + palabras]))
                if k + palabras >= len(toks):
                    break
    res: list[str] = []
    actual: list[str] = []
    n = 0
    for u in unidades:
        w = len(u.split())
        if actual and n + w > palabras:
            res.append("\n".join(actual))
            # Solape: se arrastran párrafos finales hasta ~solape·palabras.
            arrastre, m = [], 0
            for prev in reversed(actual):
                pw = len(prev.split())
                if m + pw > palabras * solape:
                    break
                arrastre.insert(0, prev)
                m += pw
            actual, n = arrastre, m
        actual.append(u)
        n += w
    if actual:
        res.append("\n".join(actual))
    return res


# --- Detección estricta de secciones (C-04) -------------------------------------------
# Un título solo se acepta si (a) coincide COMPLETO con una sección conocida (no basta que
# la línea empiece igual: "concepto del Procurador." o "aclaración de voto basada en…" son
# frases del texto) y (b) está en mayúsculas o lleva numeración ("I.", "2.", "B)").
# Además se respeta el orden de la sentencia: un solo RESUELVE; tras la fórmula de cierre
# ("Notifíquese…") el texto (firmas, anexos) queda sin etiqueta; los salvamentos y
# aclaraciones de voto solo se reconocen después del RESUELVE y sus títulos internos no
# cambian la sección. Ante la duda, sin etiqueta: una etiqueta falsa (p. ej. un argumento
# marcado como [RESUELVE]) confunde más al modelo que ninguna.
SALVAMENTO = "SALVAMENTO DE VOTO"
ACLARACION = "ACLARACIÓN DE VOTO"
RESUELVE = "RESUELVE"
_TITULOS = (
    ("SÍNTESIS", r"SINTESIS( DE LA (DECISION|PROVIDENCIA))?"),
    ("ANTECEDENTES", r"ANTECEDENTES( PROCESALES)?"),
    ("HECHOS", r"(LOS )?HECHOS( RELEVANTES)?"),
    ("LA DEMANDA", r"(LA )?DEMANDA"),
    ("NORMA DEMANDADA", r"(TEXTO DE )?(LA |LAS )?NORMAS? (DEMANDADAS?|ACUSADAS?)"),
    ("INTERVENCIONES", r"INTERVENCIONES( CIUDADANAS)?"),
    ("CONCEPTO DEL MINISTERIO PÚBLICO",
     r"CONCEPTO DEL? (SENOR )?(PROCURADOR( GENERAL DE LA NACION)?|MINISTERIO PUBLICO)"),
    ("PROBLEMA JURÍDICO", r"(EL )?PROBLEMAS? JURIDICOS?( Y METODOLOGIA( DE (LA )?DECISION)?)?"),
    ("CONSIDERACIONES", r"CONSIDERACIONES( DE LA (CORTE( CONSTITUCIONAL)?|SALA( PLENA)?))?"
                        r"( Y FUNDAMENTOS)?|"
                        r"FUNDAMENTOS( JURIDICOS)?"),
    ("COMPETENCIA", r"COMPETENCIA"),
    ("CASO CONCRETO", r"(EL )?CASO CONCRETO|ANALISIS DEL CASO( CONCRETO)?"),
    ("DECISIÓN", r"DECISION"),
    (RESUELVE, r"RESUELVE"),
)
_TITULOS_RE = [(nombre, re.compile(patron)) for nombre, patron in _TITULOS]
_VOTO_RE = re.compile(r"(SALVAMENTO|ACLARACION)( PARCIAL)? DE VOTO\b.*")
_VOTO_PARTIDO_RE = re.compile(r"(SALVAMENTO|ACLARACION)( PARCIAL)?( DE)?")
_NUMERACION_RE = re.compile(r"^(?:[IVXLC]{1,6}|\d{1,2}(?:\.\d{1,2})*|[A-H])\s*[\.\-\)]\s*")
_CIERRE_RE = re.compile(r"^(notif[ií]quese|c[oó]piese|comun[ií]quese|publ[ií]quese|c[uú]mplase)",
                        re.IGNORECASE)


def _normal(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).upper().strip(" .:;")


def _mayusculas(s: str) -> bool:
    letras = [c for c in s if c.isalpha()]
    return bool(letras) and sum(c.isupper() for c in letras) / len(letras) >= 0.8


def titulo_seccion(linea: str) -> str | None:
    """Nombre canónico de la sección si `linea` es un título de sentencia; si no, None."""
    s = linea.strip()
    if not s or len(s) > 200:
        return None
    m = _NUMERACION_RE.match(s)
    if m and "." in m.group(0).strip().rstrip(".-)"):
        return None                        # "7.1. Decisión del juez…": subtítulo, no sección
    numerada, resto = bool(m), s[m.end():] if m else s
    norm = _normal(resto)
    if _mayusculas(resto) and _VOTO_RE.fullmatch(norm):
        return SALVAMENTO if norm.startswith("SALVAMENTO") else ACLARACION
    if len(s) > 120 or not (numerada or _mayusculas(resto)):
        return None
    for nombre, patron in _TITULOS_RE:
        if patron.fullmatch(norm):
            return nombre
    return None


def secciones_sentencia(texto: str) -> list[tuple[str | None, list[str]]]:
    """Bloques (sección, líneas) de una sentencia, respetando el orden del documento."""
    bloques: list[tuple[str | None, list[str]]] = [(None, [])]
    estado = "cuerpo"                      # cuerpo → resuelve → cierre → voto
    lineas = texto.split("\n")
    for i, linea in enumerate(lineas):
        t = titulo_seccion(linea)
        if (t is None and estado != "cuerpo" and i + 1 < len(lineas)
                and _VOTO_PARTIDO_RE.fullmatch(_normal(linea)) and _mayusculas(linea)):
            # "ACLARACIÓN DE" / "VOTO A LA SENTENCIA…": título de voto partido en dos líneas.
            t = titulo_seccion(f"{linea.strip()} {lineas[i + 1].strip()}")
        if t in (SALVAMENTO, ACLARACION) and estado != "cuerpo":
            bloques.append((t, [linea]))
            estado = "voto"
        elif estado == "cuerpo" and t and t not in (SALVAMENTO, ACLARACION):
            bloques.append((t, [linea]))
            if t == RESUELVE:
                estado = "resuelve"
        elif estado == "resuelve" and _CIERRE_RE.match(linea.strip()):
            bloques.append((None, [linea]))   # firmas y anexos: sin etiqueta
            estado = "cierre"
        else:
            bloques[-1][1].append(linea)
    return bloques


def segmentar_sentencia(texto: str) -> list[Segmento]:
    bloques = secciones_sentencia(texto)

    segs: list[Segmento] = []
    for nombre, lineas in bloques:
        cuerpo = "\n".join(lineas).strip()
        if not cuerpo:
            continue
        parrafos = [p.strip() for p in re.split(r"\n\s*\n|\n", cuerpo) if p.strip()]
        for v in ventanas(parrafos):
            segs.append(Segmento("seccion", v, seccion=nombre))
    for n, s in enumerate(segs):
        s.orden = n
    return segs


def segmentar(texto: str, tipo: str) -> list[Segmento]:
    """Segmenta según el tipo de documento de `fuentes.csv`."""
    if tipo in ("sentencia", "concepto"):
        return segmentar_sentencia(texto)
    segs = segmentar_norma(texto)
    if not any(s.tipo == "articulo" for s in segs):
        # Documento sin artículos reconocibles (p. ej. circulares): ventanas.
        return segmentar_sentencia(texto)
    return segs
