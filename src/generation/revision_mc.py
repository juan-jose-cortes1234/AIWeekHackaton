"""Revisión experimental con consultas formuladas por el decoder abierto real.

No usa respuestas esperadas ni añade documentos al índice. El diagnóstico sirve
solo para buscar; la decisión final recibe exclusivamente textos del corpus.
"""
from __future__ import annotations

import dataclasses
import time

from src.generation.contexto import esquema
from src.generation.llm import Generacion


def esquema_contraste(item, propuesta):
    letras = [l for l in sorted(item.get("opciones") or {}) if l != propuesta]
    return {"type": "object", "additionalProperties": False,
            "properties": {
                "alternativas": {"type": "array", "maxItems": 2,
                                  "items": {"type": "string", "enum": letras}},
                "dato_discriminante": {"type": "string"},
                "consultas": {"type": "array", "maxItems": 2,
                              "items": {"type": "string"}}},
            "required": ["alternativas", "dato_discriminante", "consultas"]}


def consultas_validas(datos):
    """Acota y deduplica texto del modelo; no redacta consultas nuevas."""
    resultado = []
    for texto in (datos or {}).get("consultas", [])[:2]:
        if not isinstance(texto, str):
            continue
        consulta = " ".join(texto.split()[:80])
        if consulta and consulta.casefold() not in {s.casefold() for s in resultado}:
            resultado.append(consulta)
    return resultado


def contexto_revision(originales, nuevos, cfg):
    """Reserva cuatro originales, hasta cuatro nuevos y completa con los anteriores.

    Mantiene textos y offsets intactos. No duplica pasajes ni excede diez. Los
    pasajes de búsquedas del contraste se intercalan antes de llamar a esta función.
    """
    elegidos, vistos, por_doc = [], set(), {}
    originales_ids = {p.chunk_id for p in originales}
    nuevos = [p for p in nuevos if p.chunk_id not in originales_ids]

    def admitir(p):
        if p.chunk_id in vistos or len(elegidos) >= cfg.top_k_pasajes:
            return False
        if (cfg.max_por_documento and por_doc.get(p.doc_id, 0) >= cfg.max_por_documento
                and "router" not in (p.origen or [])):
            return False
        elegidos.append(p)
        vistos.add(p.chunk_id)
        por_doc[p.doc_id] = por_doc.get(p.doc_id, 0) + 1
        return True

    for p in originales[:min(cfg.puestos_pregunta, cfg.top_k_pasajes)]:
        admitir(p)
    incluidos = 0
    for p in nuevos:
        if incluidos >= 4:
            break
        incluidos += admitir(p)
    for p in originales:
        admitir(p)
    return elegidos


def agregar_usos(final, generaciones):
    def sumar(campo):
        valores = [getattr(g, campo) for g in generaciones]
        return sum(v or 0 for v in valores) if any(v is not None for v in valores) else None
    return dataclasses.replace(final, segundos=sum(g.segundos for g in generaciones),
                               tokens_prompt=sumar("tokens_prompt"),
                               tokens_salida=sumar("tokens_salida"),
                               desde_cache=all(g.desde_cache for g in generaciones))


def revisar(item, originales, propuesta: Generacion, n_leidos, extra, rec, llm, cfg, usar_cache):
    """Devuelve pasajes, generación, número leído y trazas para el mismo postproceso."""
    from jsonschema import Draft202012Validator
    from src.generation.responder import preparar_contexto

    letra = (propuesta.datos or {}).get("respuesta_correcta")
    etapas = [propuesta]
    traza = dict(extra)
    traza.update(revision_propuesta=letra, revision_aplicada=False,
                 revision_chunk_ids_iniciales=[p.chunk_id for p in originales],
                 revision_indices_iniciales=extra.get("indices_pasajes_leidos", []),
                 revision_consultas=[], s_recuperacion_revision=0.0)

    def conservar(motivo):
        traza["revision_motivo"] = motivo
        return originales, agregar_usos(propuesta, etapas), n_leidos, traza

    if letra not in (item.get("opciones") or {}):
        return conservar("propuesta_invalida")
    try:
        msgs, indices = preparar_contexto(
            item, originales, llm, cfg, etapa="contraste", max_tokens=300,
            instruccion_extra=f"Propuesta preliminar a comprobar: {letra}.")
        e = esquema_contraste(item, letra)
        contraste = llm.generar(msgs, esquema=e, max_tokens=300, usar_cache=usar_cache)
        etapas.append(contraste)
        traza["revision_contraste_indices"] = indices
        traza["revision_contraste"] = contraste.datos
        if contraste.truncada or contraste.datos is None or not Draft202012Validator(e).is_valid(contraste.datos):
            return conservar("contraste_invalido")
        consultas = consultas_validas(contraste.datos)
        traza["revision_consultas"] = consultas
        if not consultas:
            return conservar("sin_consultas")
        t0 = time.perf_counter()
        try:
            listas = [rec.buscar(q, area=item.get("area"), k=4,
                                 n_rerank=cfg.mc_rerank_candidatos_pregunta) for q in consultas]
        finally:
            traza["s_recuperacion_revision"] = time.perf_counter() - t0
        nuevos = [lista[i] for i in range(4) for lista in listas if i < len(lista)]
        traza["revision_chunk_ids_busqueda"] = [[p.chunk_id for p in lista] for lista in listas]
        originales_ids = {p.chunk_id for p in originales}
        finales = contexto_revision(originales, nuevos, cfg)
        if not any(p.chunk_id not in originales_ids for p in finales):
            return conservar("sin_pasajes_nuevos")
        msgs, numeros = preparar_contexto(
            item, finales, llm, cfg, etapa="revision", max_tokens=500,
            instruccion_extra=f"Propuesta preliminar, sujeta a verificación: {letra}.")
        if not any(finales[i - 1].chunk_id not in originales_ids for i in numeros):
            return conservar("evidencia_nueva_no_cabe")
        e = esquema(item, cfg, numeros_pasajes=numeros)
        final = llm.generar(msgs, esquema=e, max_tokens=500, usar_cache=usar_cache)
        etapas.append(final)
        traza["revision_resultado"] = (final.datos or {}).get("respuesta_correcta")
        if final.truncada or final.datos is None or not Draft202012Validator(e).is_valid(final.datos):
            return conservar("respuesta_final_invalida")
        traza.update(revision_aplicada=True, revision_motivo="evidencia_adicional",
                     indices_pasajes_leidos=numeros,
                     chunk_ids_leidos=[finales[i - 1].chunk_id for i in numeros])
        from src.generation.seleccion_mc import cobertura
        traza.update(cobertura_recuperada=cobertura(finales, item.get("opciones") or {}),
                     cobertura_leida=cobertura([finales[i - 1] for i in numeros],
                                              item.get("opciones") or {}))
        return finales, agregar_usos(final, etapas), len(numeros), traza
    except Exception as exc:
        # El control original sigue utilizable; la omisión y su causa quedan explícitas.
        return conservar(f"error_revision: {type(exc).__name__}: {exc}")
