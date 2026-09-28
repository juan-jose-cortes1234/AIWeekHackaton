"""Lectura y validación de `fuentes.csv`, el inventario del corpus crudo.

Formato definido en GUIA_CORPUS.md §3. Acepta separador `,` o `;` y UTF-8 con o
sin BOM (lo que produce Excel con "CSV UTF-8").
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from src.oficial import AREA_SLUG, AREAS

TIPOS = {
    "constitucion", "codigo", "ley", "decreto", "decreto_ley", "acto_legislativo",
    "decision_andina", "resolucion", "circular", "sentencia", "concepto",
}
# Tipos que necesitan número y año para producir una cita reconocible.
TIPOS_CON_NUMERO = {"ley", "decreto", "decreto_ley", "acto_legislativo", "decision_andina",
                    "resolucion", "circular", "sentencia"}

OBLIGATORIAS = ("doc_id", "archivo", "titulo", "tipo", "organo_emisor", "fuente", "url",
                "fecha_consulta", "areas")
OPCIONALES = ("numero", "anio", "vigencia", "notas")
VIGENCIAS = {"", "vigente", "derogada", "parcial"}

DOC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")
SENTENCIA_RE = re.compile(r"^(C|T|SU|SL|SC|SP|STC|STL|AC|AU)-\d{1,5}$", re.IGNORECASE)

_SLUG_A_AREA = {slug: area for area, slug in AREA_SLUG.items()}


def _clave_area(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.strip().lower())


_AREA_POR_CLAVE = {_clave_area(a): a for a in AREAS}
_AREA_POR_CLAVE.update({_clave_area(s): a for s, a in _SLUG_A_AREA.items()})
# Forma corta del área de mercados, que en el nombre oficial lleva corchetes.
_AREA_POR_CLAVE["derecho de los mercados"] = _SLUG_A_AREA["mercados"]


@dataclass
class Fuente:
    """Una fila válida de `fuentes.csv`."""
    doc_id: str
    archivo: Path
    titulo: str
    tipo: str
    numero: str
    anio: str
    organo_emisor: str
    fuente: str
    url: str
    fecha_consulta: str
    areas: list[str]
    vigencia: str = ""
    notas: str = ""


@dataclass
class Resultado:
    fuentes: list[Fuente] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errores


def normalizar_area(texto: str) -> str | None:
    """Devuelve el nombre oficial del área a partir del nombre o del slug."""
    return _AREA_POR_CLAVE.get(_clave_area(texto))


def _leer_filas(ruta: Path) -> tuple[list[str], list[dict]]:
    texto = ruta.read_text(encoding="utf-8-sig")
    primera = texto.splitlines()[0] if texto else ""
    sep = ";" if primera.count(";") > primera.count(",") else ","
    lector = csv.DictReader(texto.splitlines(), delimiter=sep)
    cabecera = [(c or "").strip().lower() for c in (lector.fieldnames or [])]
    filas = []
    for fila in lector:
        filas.append({(k or "").strip().lower(): (v or "").strip() for k, v in fila.items()
                      if k is not None})
    return cabecera, filas


def validar(raiz_corpus: Path) -> Resultado:
    """Valida `raiz_corpus/fuentes.csv` y devuelve las fuentes válidas y los errores."""
    res = Resultado()
    csv_path = raiz_corpus / "fuentes.csv"
    if not csv_path.is_file():
        res.errores.append(f"No existe {csv_path}. Ver GUIA_CORPUS.md §3.")
        return res

    cabecera, filas = _leer_filas(csv_path)
    faltan = [c for c in OBLIGATORIAS + ("numero", "anio") if c not in cabecera]
    if faltan:
        res.errores.append(f"fuentes.csv: faltan columnas {faltan}")
        return res
    desconocidas = [c for c in cabecera if c and c not in OBLIGATORIAS + OPCIONALES]
    if desconocidas:
        res.avisos.append(f"fuentes.csv: columnas ignoradas {desconocidas}")

    vistos: dict[str, int] = {}
    for i, f in enumerate(filas, start=2):  # la fila 1 es la cabecera
        if not any(f.values()):
            continue
        errs: list[str] = []
        pre = f"fila {i} ({f.get('doc_id') or 'sin doc_id'})"

        for c in OBLIGATORIAS:
            if not f.get(c):
                errs.append(f"'{c}' vacío")

        doc_id = f.get("doc_id", "")
        if doc_id and not DOC_ID_RE.match(doc_id):
            errs.append(f"doc_id '{doc_id}' debe ser minúsculas sin tildes ni espacios")
        if doc_id in vistos:
            errs.append(f"doc_id repetido (ya en fila {vistos[doc_id]})")
        vistos.setdefault(doc_id, i)

        tipo = f.get("tipo", "").lower()
        if tipo and tipo not in TIPOS:
            errs.append(f"tipo '{tipo}' inválido; use uno de {sorted(TIPOS)}")
        numero, anio = f.get("numero", ""), f.get("anio", "")
        if tipo in TIPOS_CON_NUMERO and not (numero and anio):
            errs.append(f"el tipo '{tipo}' necesita 'numero' y 'anio'")
        if anio and not re.fullmatch(r"\d{4}", anio):
            errs.append(f"anio '{anio}' debe tener 4 dígitos")
        if tipo == "sentencia" and numero and not SENTENCIA_RE.match(numero):
            errs.append(f"numero de sentencia '{numero}' debe ser como C-355 o SL-3385")
        if tipo == "codigo" and not (numero and anio):
            res.avisos.append(f"{pre}: código sin numero/anio; la cita dependerá solo del nombre")

        archivo = raiz_corpus / f.get("archivo", "")
        if f.get("archivo") and not archivo.exists():
            errs.append(f"no existe el archivo o carpeta '{f['archivo']}'")

        url = f.get("url", "")
        if url and not re.match(r"^https?://", url):
            errs.append("url debe empezar por http:// o https://")

        fecha = f.get("fecha_consulta", "")
        if fecha:
            try:
                date.fromisoformat(fecha)
            except ValueError:
                errs.append(f"fecha_consulta '{fecha}' debe ser AAAA-MM-DD")

        areas = []
        for a in re.split(r"\|", f.get("areas", "")):
            if not a.strip():
                continue
            oficial = normalizar_area(a)
            if oficial is None:
                errs.append(f"área desconocida '{a.strip()}'")
            elif oficial not in areas:
                areas.append(oficial)

        vigencia = f.get("vigencia", "").lower()
        if vigencia not in VIGENCIAS:
            errs.append(f"vigencia '{vigencia}' inválida; use vigente, derogada o parcial")

        if errs:
            res.errores.extend(f"{pre}: {e}" for e in errs)
            continue
        res.fuentes.append(Fuente(
            doc_id=doc_id, archivo=archivo, titulo=f["titulo"], tipo=tipo,
            numero=numero.upper() if tipo == "sentencia" else numero, anio=anio,
            organo_emisor=f["organo_emisor"], fuente=f["fuente"], url=url,
            fecha_consulta=fecha, areas=areas, vigencia=vigencia, notas=f.get("notas", "")))
    if not res.fuentes and not res.errores:
        res.errores.append("fuentes.csv no tiene filas.")
    return res
