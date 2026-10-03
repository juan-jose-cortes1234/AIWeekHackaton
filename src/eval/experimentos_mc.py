"""Prueba MC controlada con modelos reales, cargados una sola vez.

python -m src.eval.experimentos_mc --tag mc_v17 --perfiles v12,verificacion
Las respuestas esperadas se reservan para evaluar y no se pasan al pipeline.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json

from src.config import RAIZ, config
from src.pipeline.main import ejecutar, leer_jsonl
from src.pipeline.perfiles_mc import PERFILES, configurar
from src.eval.multiple_choice import comparar


def calidad_experimento(trazas):
    """No interpretar una ganancia basada en fallbacks o etapas que fallaron."""
    return {
        "errores_generacion": sum(bool(t.get("excepcion") or t.get("errores_esquema")) for t in trazas),
        "fallback_mc": sum(bool(t.get("fallback_mc")) for t in trazas),
        "revision_aplicadas": sum(bool(t.get("revision_aplicada")) for t in trazas),
        "revision_errores": sum(str(t.get("revision_motivo", "")).startswith("error_revision") for t in trazas),
        "pensamiento_cortado": sum(bool(t.get("razonamiento_truncado")) for t in trazas),
        "verificacion_aplicadas": sum("verificacion_auditorias" in t for t in trazas),
        "verificacion_errores": sum(bool(t.get("verificacion_incompleta")) for t in trazas),
        "verificacion_citas_rechazadas": sum(len(a.get("citas_rechazadas", []))
            for t in trazas for a in t.get("verificacion_auditorias", {}).values()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--perfiles", default="v12,verificacion")
    ap.add_argument("--directorio", type=Path, default=RAIZ / "runs")
    args = ap.parse_args(argv)
    nombres = args.perfiles.split(",")
    if len(set(nombres)) != len(nombres) or any(n not in PERFILES for n in nombres):
        ap.error(f"Perfiles distintos y válidos: {', '.join(PERFILES)}")
    if "v12" not in nombres:
        ap.error("Incluya v12 como control en la misma sesión.")
    nombres = ["v12"] + [n for n in nombres if n != "v12"]
    for nombre in nombres:
        configurar(config, nombre).validar_final()
    oro = [q for q in leer_jsonl(RAIZ / "data/sample_50.jsonl")
           if q["formato"] == "multiple_choice"]
    preguntas = [{k: v for k, v in q.items() if k in (
        "id", "formato", "area", "sub_tarea", "pregunta", "opciones")} for q in oro]
    cfg = configurar(config, "v12")
    cfg.validar_final()
    from src.generation.llm import LLM
    from src.retrieval.hibrido import Recuperador
    rec, llm = Recuperador.cargar(cfg=cfg), LLM(cfg)
    if "pensamiento" in nombres:
        # Comprobar la plantilla y la API antes de ejecutar las 60 respuestas.
        import inspect
        from src.generation.contexto import mensajes
        llm.contar_tokens(mensajes(preguntas[0], [], cfg), gemma_pensamiento_tokens=512)
        if "temp" not in inspect.signature(llm.modelo.generate).parameters:
            raise RuntimeError("La versión de llama-cpp-python no ofrece generate(temp=...).")
    baseline = None
    resumen = {}
    for nombre in nombres:
        actual = configurar(config, nombre)
        actual.validar_final()
        rec.cfg = actual
        directorio = args.directorio / f"{args.tag}_{nombre}"
        salida = directorio / "submissions.jsonl"
        print(f"\nPerfil {nombre}: {salida}", flush=True)
        ejecutar(preguntas, rec, llm, salida, directorio, cfg=actual, usar_cache=False)
        filas = leer_jsonl(salida)
        if nombre == "v12":
            baseline = filas
        trazas = leer_jsonl(directorio / "trazas.jsonl")
        reporte = comparar(oro, filas, baseline, trazas)
        (directorio / "comparacion_mc.json").write_text(
            json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
        resumen[nombre] = {k: reporte[k] for k in (
            "aciertos", "n", "ganancias", "perdidas", "latencia_media_ms")}
        calidad = calidad_experimento(trazas)
        resumen[nombre].update(calidad)
        resumen[nombre]["comparacion_utilizable"] = (
            len(filas) == len(preguntas) == len(trazas)
            and not any(calidad[k] for k in ("errores_generacion", "fallback_mc", "revision_errores",
                                            "verificacion_errores")))
        print(resumen[nombre], flush=True)
        if not resumen[nombre]["comparacion_utilizable"]:
            print("Perfil con errores o fallbacks: su puntuación no acredita una mejora del decoder.", flush=True)
    destino = args.directorio / f"{args.tag}_experimentos.json"
    destino.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
