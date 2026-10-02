"""Post-filtro determinista de citas (ARQUITECTURA §6, paso 4 del enunciado).

El evaluador castiga con el doble cada cita que no corresponde al fundamento y
no está en los pasajes recuperados. Aquí:

1. Se completan leyes/decretos citados sin año (“Ley 1150”) cuando los pasajes
   resuelven el año de forma única (el evaluador no reconoce la cita sin año).
2. Se localiza cada cita con las **mismas expresiones regulares del evaluador**
   (`scripts/citations.py`) y se reemplaza la que no esté respaldada por los 10
   primeros pasajes; si no se puede, se elimina la oración.
3. Las referencias se **renderizan desde los metadatos** de los pasajes usados y
   de los pertinentes (su encabezado canónico), de modo que son reproducibles
   aunque la redacción del modelo varíe (verificación en vivo).
4. Se aplican los límites de extensión del enunciado.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from src.config import Config, config
from src.oficial import citations as C

MAX_EVIDENCIA = 10
REEMPLAZO = "la normativa aplicable"
SIN_JURISPRUDENCIA = "La evidencia recuperada no incluye jurisprudencia pertinente para el caso."
SIN_RESPALDO_OPCION = "La evidencia recuperada no respalda esta opción."
MAX_PALABRAS_ABIERTA = 500   # tope de las respuestas abiertas (los cuatro campos juntos), C-20
_ORACION = re.compile(r"(?<=[.;:!?])\s+(?=[A-ZÁÉÍÓÚÑ¿(\"“])")
_SENTENCIA_PREVIA = re.compile(r"(?:\b(?:la|las|el)\s+)?\bsentencias?\s+(?:de\s+tutela\s+|de\s+unificaci[óo]n\s+)?$",
                               re.IGNORECASE)
_CUERPO_ART = re.compile(
    r"(?:\b(?:los|las|el|la)\s+)?\b(?:art[íi]culos?|arts?\.?)\s+[\w\s,.-]{0,40}?\s+(?:de\s+la|del|de)\s+$",
    re.IGNORECASE)


# --------------------------------------------------------------------------- localización

def _norm_misma_longitud(texto: str) -> str:
    """Como `citations.norm`, pero sin colapsar espacios: conserva los offsets."""
    out = []
    for ch in texto:
        base = unicodedata.normalize("NFD", ch)
        base = "".join(c for c in base if unicodedata.category(c) != "Mn") or " "
        out.append(base[0].lower() if not ch.isspace() else " ")
    return "".join(out)


def localizar(texto: str) -> list[tuple[int, int, tuple]]:
    """Spans (inicio, fin, cuerpo) de cada cita que el evaluador extraería."""
    t = _norm_misma_longitud(texto)
    res: list[tuple[int, int, tuple]] = []
    for m in C._NORM_RE.finditer(t):
        kind = next(k for k, vs in C.NORM_TYPES.items()
                    if any(re.fullmatch(v.replace(" ", r"\s+"), re.sub(r"\s+", " ", m.group(1)))
                           for v in vs))
        alias = C._ALIAS_NUM.get((kind, m.group(2)))
        cuerpo = (alias, None, None) if alias else (kind, m.group(2), m.group(3))
        res.append((m.start(), m.end(), cuerpo))
    for m in C._BARE_LAW_RE.finditer(t):
        alias = C._ALIAS_NUM.get((m.group(1), m.group(2)))
        if alias:
            res.append((m.start(), m.end(), (alias, None, None)))
    for code, variantes in C.CODES.items():
        for v in sorted(variantes, key=len, reverse=True):
            pat = r"(?<![\w.])" + re.escape(v).replace(r"\ ", r"\s+") + r"(?![\w])"
            for m in re.finditer(pat, t):
                res.append((m.start(), m.end(), (code, None, None)))
    for m in C._SENT_RE.finditer(t):
        anio = m.group(3)
        if len(anio) == 2:
            anio = ("20" if int(anio) < 50 else "19") + anio
        res.append((m.start(), m.end(),
                    ("jurisprudencia", f"{m.group(1).upper()}-{int(m.group(2))}", anio)))
    return res


def cuerpos(texto: str) -> set[tuple]:
    return C.bodies(C.extract(texto))


def respaldadas(pasajes) -> set[tuple]:
    r: set[tuple] = set()
    for p in pasajes[:MAX_EVIDENCIA]:
        r |= cuerpos(p.texto)
    return r


# --------------------------------------------------------------------------- limpieza

def completar_anios(texto: str, soporte: set[tuple]) -> str:
    """“Ley 1150” → “Ley 1150 de 2007” si el año es único en los pasajes."""
    def sustituir(m: re.Match) -> str:
        tipo = C.norm(m.group(1))
        anios = sorted({c[2] for c in soporte if c[0] == tipo and c[1] == m.group(2) and c[2]})
        return f"{m.group(0)} de {anios[0]}" if len(anios) == 1 else m.group(0)
    return re.sub(r"\b(Ley|Decreto)\s+(\d{2,5})\b(?!\s*(?:de|del|/|-)\s*\d{4})", sustituir, texto,
                  flags=re.IGNORECASE)


def _quitar_spans(texto: str, spans: list[tuple[int, int]]) -> str:
    # Tramos finales sobre el texto original (con "el artículo 5 del " o "la Sentencia " que
    # los precede) y unidos si se solapan: reemplazar por separado dos tramos que se pisan
    # (p. ej. un código dentro de una cita más larga) corrompía el texto ("la normativa
    # aplicla normativa aplicable…", caso 679 en muestra_v6).
    tramos = []
    for ini, fin in spans:
        previo = (_CUERPO_ART.search(texto[:ini])       # “el artículo 5 del ” antes de la norma
                  or _SENTENCIA_PREVIA.search(texto[:ini]))  # “la Sentencia ” antes de “T-123…”
        tramos.append((previo.start() if previo else ini, fin))
    unidos: list[list[int]] = []
    for ini, fin in sorted(tramos):
        if unidos and ini <= unidos[-1][1]:
            unidos[-1][1] = max(unidos[-1][1], fin)
        else:
            unidos.append([ini, fin])
    for ini, fin in reversed(unidos):
        texto = texto[:ini] + REEMPLAZO + texto[fin:]
    return re.sub(rf"({re.escape(REEMPLAZO)})(\s*[,;y]\s*{re.escape(REEMPLAZO)})+", r"\1", texto)


def filtrar(texto: str, soporte: set[tuple]) -> tuple[str, list[str]]:
    """Elimina del texto toda cita cuyo cuerpo no esté en `soporte`."""
    if not texto:
        return texto, []
    eliminadas: list[str] = []
    oraciones = _ORACION.split(texto.strip())
    salida = []
    for o in oraciones:
        malos = [(i, f) for i, f, c in localizar(o) if c not in soporte]
        if malos:
            eliminadas += [o[i:f] for i, f in malos]
            o = _quitar_spans(o, malos)
            if not cuerpos(o) <= soporte:        # último recurso: se descarta la oración
                continue
        salida.append(o)
    return " ".join(salida).strip(), eliminadas


# --------------------------------------------------------------------------- render

def referencia(pasaje) -> str:
    """Referencia canónica de un pasaje a partir de su encabezado."""
    cab = pasaje.texto.split("\n", 1)[0]
    cab = re.sub(r"\s*\(parte \d+ de \d+\)", "", cab)
    cab = re.sub(r"\s*\((?:encabezado|notas de vigencia y jurisprudencia)\)", "", cab)
    cab = re.sub(r"\s*\[[^\]]*\]", "", cab)
    return cab.strip().rstrip(".").strip()


def referencias(pasajes, usados: list[int] | None, cfg: Config = config) -> list[str]:
    """Referencias de los pasajes usados por el modelo y de los pertinentes, sin repetir."""
    evid = pasajes[:MAX_EVIDENCIA]
    elegidos = [evid[i - 1] for i in (usados or []) if isinstance(i, int) and 1 <= i <= len(evid)]
    for p in evid:
        pert = p.score_rerank if p.score_rerank is not None else None
        if (pert is not None and pert >= cfg.umbral_cita) or "router" in (p.origen or []):
            elegidos.append(p)
    if not elegidos and evid:
        elegidos.append(evid[0])
    vistas, res = set(), []
    for p in elegidos:
        r = referencia(p)
        if r and r not in vistas:
            vistas.add(r)
            res.append(r)
    return res[:cfg.max_referencias]


# --------------------------------------------------------------------------- extensión

def limitar(texto: str, max_oraciones: int, max_palabras: int | None = None) -> str:
    oraciones = [o for o in _ORACION.split((texto or "").strip()) if o]
    oraciones = oraciones[:max_oraciones]
    if max_palabras:
        res, n = [], 0
        for o in oraciones:
            w = len(o.split())
            if res and n + w > max_palabras:
                break
            res.append(o if n + w <= max_palabras else " ".join(o.split()[:max_palabras - n]))
            n += w
        oraciones = res
    return " ".join(oraciones).strip()


# --------------------------------------------------------------------------- orquestación

@dataclass
class Postproceso:
    campos: dict
    eliminadas: list[str] = field(default_factory=list)
    referencias: list[str] = field(default_factory=list)


def postprocesar(item: dict, datos: dict, pasajes, cfg: Config = config) -> Postproceso:
    """Campos finales de la entrega, sin citas sin respaldo."""
    soporte = respaldadas(pasajes)
    refs = referencias(pasajes, datos.get("pasajes_usados"), cfg)
    elim: list[str] = []

    def limpio(texto: str) -> str:
        t, e = filtrar(completar_anios(str(texto or ""), soporte), soporte)
        elim.extend(e)
        return t

    f = item["formato"]
    if f == "multiple_choice":
        just = limpio(datos.get("justificacion"))
        if refs:
            just = f"{just} Fundamento normativo: {'; '.join(refs)}.".strip()
        # Los descartes salen del análisis por opción (C-03); "descarte_opciones" queda como
        # respaldo si una salida antigua o rescatada lo trae.
        fuente = datos.get("analisis_opciones") or datos.get("descarte_opciones") or {}
        descartes = {l: limpio(v) for l, v in fuente.items()
                     if l != datos.get("respuesta_correcta") and str(v or "").strip()}
        for l in sorted(item.get("opciones") or {}):
            if l != datos.get("respuesta_correcta") and not descartes.get(l):
                descartes[l] = SIN_RESPALDO_OPCION
        campos = {"respuesta_correcta": datos.get("respuesta_correcta"),
                  "justificacion": just, "descarte_opciones": descartes}
    elif f == "semi_open":
        resp = limitar(limpio(datos.get("respuesta")), 5, 150)
        ref_modelo = limpio(datos.get("referencia_legal"))
        campos = {"respuesta": resp,
                  "palabras_clave": [str(k).strip() for k in (datos.get("palabras_clave") or [])
                                     if str(k).strip()][:6],
                  "referencia_legal": "; ".join(refs) or ref_modelo}
    else:
        marco = limpio(datos.get("marco_normativo"))
        analisis = limitar(limpio(datos.get("analisis")), 8)
        juris = limpio(datos.get("jurisprudencia"))
        concl = limpio(datos.get("conclusion"))
        # Respuesta rescatada de una salida cortada: completar lo que falte, sin inventar
        # contenido jurídico (el evaluador da por fallida una línea con campos vacíos).
        if analisis and not concl:
            concl = limitar(analisis.split(". ")[-1], 1) or analisis
        if (marco or analisis) and not juris:
            juris = SIN_JURISPRUDENCIA
        ya = cuerpos(" ".join((marco, analisis, juris, concl)))
        faltan = [r for r in refs if not cuerpos(r) <= ya]
        if faltan:
            marco = f"{marco} Normas aplicables: {'; '.join(faltan)}.".strip()
        # Tope de MAX_PALABRAS_ABIERTA para los cuatro campos juntos (C-20): si se pasa, se
        # recorta el análisis (el campo más largo) a las palabras que queden disponibles.
        resto = sum(len(t.split()) for t in (marco, juris, concl))
        if resto + len(analisis.split()) > MAX_PALABRAS_ABIERTA:
            analisis = limitar(analisis, 8, max(MAX_PALABRAS_ABIERTA - resto, 60))
        campos = {"marco_normativo": marco, "analisis": analisis,
                  "jurisprudencia": juris, "conclusion": concl}
    return Postproceso(campos=campos, eliminadas=elim, referencias=refs)
