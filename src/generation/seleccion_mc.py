"""Selección determinista de evidencia MC; no consulta ni carga modelos.

Las asociaciones por opción describen consultas, nunca respaldo jurídico.
Los scores de consultas diferentes no se comparan: se utilizan rangos.
"""
from __future__ import annotations

import dataclasses
from collections import Counter

from src.config import Config


def opciones_pasaje(p) -> set[str]:
    meta = p.meta or {}
    return set(meta.get("opciones") or ([meta["opcion"]] if meta.get("opcion") else []))


def cobertura(pasajes, letras) -> dict[str, int]:
    return {l: sum(l in opciones_pasaje(p) for p in pasajes) for l in sorted(letras)}


def prioridad_cobertura(p, pasajes, letras, objetivo: int = 2) -> tuple:
    """Favorece primero la peor cobertura; luego el rango en esas consultas."""
    cuenta = cobertura(pasajes, letras)
    asociadas = opciones_pasaje(p)
    balance = tuple(sorted(min(objetivo, cuenta[l] + (l in asociadas)) for l in cuenta))
    rangos = (p.meta or {}).get("rangos_opcion") or {}
    utilidad = sum(1 / (60 + rangos.get(l, 1000))
                   for l in asociadas if l in cuenta and cuenta[l] < objetivo)
    rango_base = (p.meta or {}).get("rango_pregunta", 1000)
    return balance, utilidad, -rango_base


def seleccionar_mc(base, por_opcion, cfg: Config, documentos_mencionados=frozenset(),
                   complementarios=frozenset()):
    """Une evidencia compartida y aplica diversidad al conjunto final de diez."""
    pool = {}
    for grupo, candidatos in [(None, base), *sorted(por_opcion.items())]:
        for rango, p in enumerate(candidatos, 1):
            if p.chunk_id not in pool:
                meta = {k: v for k, v in (p.meta or {}).items()
                        if k not in {"opcion", "opciones", "rangos_opcion", "rango_pregunta"}}
                meta.update(opciones=[], rangos_opcion={})
                pool[p.chunk_id] = dataclasses.replace(p, meta=meta, origen=list(p.origen))
            unido = pool[p.chunk_id]
            unido.origen = sorted(set(unido.origen) | set(p.origen))
            if grupo is None:
                unido.meta["rango_pregunta"] = rango
                unido.meta["router_pregunta"] = "router" in p.origen
            else:
                unido.meta["opciones"].append(grupo)
                unido.meta["rangos_opcion"][grupo] = rango
    for p in pool.values():
        p.meta["opciones"] = sorted(set(p.meta["opciones"]))

    elegidos = []
    documentos, unidades = Counter(), Counter()
    n_complementarios = 0
    limite = min(10, cfg.top_k_pasajes)
    letras = sorted(por_opcion)

    def admisible(p):
        unidad = (p.doc_id, p.meta.get("articulo") or p.meta.get("seccion") or p.chunk_id)
        mencionado = p.doc_id in documentos_mencionados or p.meta.get("router_pregunta", False)
        return (p not in elegidos
                and (not cfg.max_por_articulo or unidades[unidad] < cfg.max_por_articulo)
                and (mencionado or not cfg.max_por_documento
                     or documentos[p.doc_id] < cfg.max_por_documento)
                and (mencionado or p.doc_id not in complementarios or not cfg.max_complementarios
                     or n_complementarios < cfg.max_complementarios))

    def agregar(p):
        nonlocal n_complementarios
        elegidos.append(p)
        documentos[p.doc_id] += 1
        unidades[(p.doc_id, p.meta.get("articulo") or p.meta.get("seccion") or p.chunk_id)] += 1
        if (p.doc_id in complementarios and p.doc_id not in documentos_mencionados
                and not p.meta.get("router_pregunta", False)):
            n_complementarios += 1

    # Reserva espacio para al menos una evidencia por opción cuando es posible.
    puestos = min(cfg.puestos_pregunta, max(0, limite - len(letras)))
    for original in base:
        if len(elegidos) >= puestos:
            break
        p = pool[original.chunk_id]
        if admisible(p):
            agregar(p)

    while len(elegidos) < limite:
        candidatos = [p for p in pool.values() if admisible(p)]
        if not candidatos:
            break
        # Desempate por chunk, independiente de la letra y del orden del diccionario.
        candidatos.sort(key=lambda p: p.chunk_id)
        elegido = max(candidatos, key=lambda p: prioridad_cobertura(
            p, elegidos, letras, cfg.pasajes_por_opcion))
        agregar(elegido)
    return elegidos


def quitar_por_presupuesto(pasajes, numeros, letras):
    """Índice local a omitir: conserva opciones, artículos directos y rangos altos."""
    def prioridad(i):
        restantes = pasajes[:i] + pasajes[i + 1:]
        balance = tuple(sorted(cobertura(restantes, letras).values()))
        directos = sum(bool(p.meta.get("router_pregunta")) for p in restantes)
        p = pasajes[i]
        rango = min([p.meta.get("rango_pregunta", 1000),
                     *p.meta.get("rangos_opcion", {}).values()])
        return balance, directos, rango, len(p.texto), numeros[i]
    return max(range(len(pasajes)), key=prioridad)


def seleccionar_contexto(pasajes, limite: int, presupuesto: int, contar, letras):
    """Presupuesto medido por el renderizador/tokenizer del llamador.

    `contar(indices)` mide el prompt completo, no una estimación por palabras.
    La función solo selecciona índices y permite probar el algoritmo sin modelos.
    """
    numeros = list(range(1, min(10, len(pasajes)) + 1))
    omitidos = []
    while len(numeros) > limite or contar(numeros) > presupuesto:
        if not numeros:
            raise ValueError("La pregunta y las instrucciones exceden la ventana de contexto.")
        indice = quitar_por_presupuesto([pasajes[i - 1] for i in numeros], numeros, letras)
        omitidos.append(numeros.pop(indice))
    for numero in reversed(omitidos):
        if len(numeros) >= limite:
            break
        propuesta = sorted(numeros + [numero])
        if contar(propuesta) <= presupuesto:
            numeros = propuesta
    return numeros
