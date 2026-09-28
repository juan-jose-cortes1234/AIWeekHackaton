"""Pipeline principal: preguntas → `submissions.jsonl` según el esquema oficial.

Uso:
    python -m src.pipeline.main --split sample                  # muestra, salida en runs/<tag>/
    python -m src.pipeline.main --split test --out submissions.jsonl   # sábado
    python -m src.pipeline.main --split sample --ids 51,290 --no-cache --out runs/verif.jsonl

Por ítem: recuperar (híbrido + reranker) → generar (Qwen3-8B, temperatura 0) →
post-filtro de citas → abstención → validación contra el esquema → escritura
inmediata (reanudable: los ids ya presentes en la salida se saltan).
Trazas por ítem en `<dir>/trazas.jsonl` y tiempos en `<dir>/tiempos.json`.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

from src.config import RAIZ, Config, config
from src.generation.abstencion import decidir, registro_abstencion
from src.generation.citas import postprocesar
from src.generation.contexto import LETRAS, MAX_TOKENS, esquema
from src.generation.responder import mensajes_que_caben, recuperar

ENTRADAS = {"sample": RAIZ / "data" / "sample_50.jsonl", "test": RAIZ / "data" / "test_992.jsonl"}
CAMPOS_INTERNOS = ("pasajes_usados",)


def leer_jsonl(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def esquema_oficial() -> dict:
    return json.loads((RAIZ / "schema" / "submission.schema.json").read_text(encoding="utf-8"))


def respaldo_mc(item: dict, pasajes, rec) -> str:
    """Letra determinista si el modelo no devolvió una MC utilizable: la opción que el
    reranker (o, sin él, el orden alfabético) considera más pertinente a la evidencia."""
    letras = [l for l in LETRAS if l in (item.get("opciones") or {})] or ["A"]
    if getattr(rec, "reranker", None) is None or not pasajes:
        return letras[0]
    evidencia = "\n".join(p.texto for p in pasajes[:3])
    puntos = rec.reranker.puntuar(evidencia, [f"{item['pregunta']} {item['opciones'][l]}"
                                              for l in letras])
    return max(zip(letras, puntos), key=lambda x: (x[1], -letras.index(x[0])))[0]


def responder_item(item: dict, rec, llm, cfg: Config = config, usar_cache: bool = True):
    """Devuelve (línea de entrega, traza)."""
    t0 = time.perf_counter()
    pasajes = recuperar(item, rec, cfg)
    t1 = time.perf_counter()
    msgs, n_leidos = mensajes_que_caben(item, pasajes, llm, cfg)
    g = llm.generar(msgs, esquema=esquema(item), max_tokens=MAX_TOKENS[item["formato"]],
                    usar_cache=usar_cache)
    t2 = time.perf_counter()

    datos = dict(g.datos or {})
    if item["formato"] == "multiple_choice" and datos.get("respuesta_correcta") not in LETRAS:
        datos["respuesta_correcta"] = respaldo_mc(item, pasajes, rec)
        datos.setdefault("justificacion", "")
        datos.setdefault("descarte_opciones", {})
    pp = postprocesar(item, datos, pasajes, cfg) if datos else None
    decision = decidir(item, pasajes, pp.campos if pp else None, cfg)

    if decision.abstener:
        linea = registro_abstencion(item, pasajes)
    else:
        linea = {"id": item["id"], "formato": item["formato"], "abstencion": False,
                 **{k: v for k, v in pp.campos.items() if k not in CAMPOS_INTERNOS},
                 "pasajes_recuperados": [p.a_entrega() for p in pasajes]}
    linea["latencia_ms"] = int((time.perf_counter() - t0) * 1000)

    traza = {
        "id": item["id"], "formato": item["formato"], "abstencion": decision.abstener,
        "motivo": decision.motivo, "pertinencia_max": decision.pertinencia_max,
        "pasajes": [{"chunk_id": p.chunk_id, "score": round(p.score, 5),
                     "rerank": p.score_rerank, "denso": p.score_denso, "bm25": p.score_bm25,
                     "origen": p.origen} for p in pasajes],
        "pasajes_leidos": n_leidos,
        "pasajes_usados": (g.datos or {}).get("pasajes_usados"),
        "citas_eliminadas": pp.eliminadas if pp else [],
        "referencias": pp.referencias if pp else [],
        "json_valido": g.datos is not None, "desde_cache": g.desde_cache,
        "tokens_prompt": g.tokens_prompt, "tokens_salida": g.tokens_salida,
        "s_recuperacion": round(t1 - t0, 3), "s_generacion": round(t2 - t1, 3),
        "s_total": round(time.perf_counter() - t0, 3),
    }
    return linea, traza


def _percentiles(valores: list[float]) -> dict:
    if not valores:
        return {}
    v = sorted(valores)
    return {"n": len(v), "media": round(statistics.mean(v), 2), "p50": round(v[len(v) // 2], 2),
            "p95": round(v[min(len(v) - 1, int(0.95 * len(v)))], 2), "max": round(v[-1], 2)}


def ejecutar(preguntas: list[dict], rec, llm, salida: Path, dir_trazas: Path,
             cfg: Config = config, usar_cache: bool = True, reanudar: bool = True) -> dict:
    import jsonschema

    validador = jsonschema.Draft202012Validator(esquema_oficial())
    salida.parent.mkdir(parents=True, exist_ok=True)
    dir_trazas.mkdir(parents=True, exist_ok=True)
    hechos = {r["id"] for r in leer_jsonl(salida)} if (reanudar and salida.is_file()) else set()
    if not reanudar and salida.exists():
        salida.unlink()

    pendientes = [q for q in preguntas if q["id"] not in hechos]
    tiempos = {"s_recuperacion": [], "s_generacion": [], "s_total": []}
    errores = 0
    with salida.open("a", encoding="utf-8", newline="\n") as out, \
            (dir_trazas / "trazas.jsonl").open("a", encoding="utf-8", newline="\n") as tr:
        for n, item in enumerate(pendientes, start=1):
            linea, traza = responder_item(item, rec, llm, cfg, usar_cache)
            problemas = [e.message for e in validador.iter_errors(linea)]
            if problemas:                      # nunca se escribe una línea inválida
                errores += 1
                traza["errores_esquema"] = problemas
                pasajes = recuperar(item, rec, cfg)
                if item["formato"] == "multiple_choice":
                    linea = {"id": item["id"], "formato": item["formato"], "abstencion": False,
                             "respuesta_correcta": respaldo_mc(item, pasajes, rec),
                             "justificacion": "", "descarte_opciones": {},
                             "pasajes_recuperados": [p.a_entrega() for p in pasajes],
                             "latencia_ms": linea.get("latencia_ms", 0)}
                else:
                    linea = registro_abstencion(item, pasajes) | {
                        "latencia_ms": linea.get("latencia_ms", 0)}
            out.write(json.dumps(linea, ensure_ascii=False) + "\n")
            out.flush()
            tr.write(json.dumps(traza, ensure_ascii=False) + "\n")
            tr.flush()
            for k in tiempos:
                tiempos[k].append(traza[k])
            print(f"[{n}/{len(pendientes)}] id={item['id']} {item['formato']:15} "
                  f"abst={'sí' if linea['abstencion'] else 'no'} {traza['s_total']:.1f}s",
                  flush=True)

    resumen = {"respondidas_ahora": len(pendientes), "ya_existentes": len(hechos),
               "errores_esquema": errores, "tiempos": {k: _percentiles(v) for k, v in tiempos.items()},
               "salida": str(salida)}
    (dir_trazas / "tiempos.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    return resumen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=("sample", "test"), default="sample")
    ap.add_argument("--input", type=Path, default=None, help="JSONL de preguntas (anula --split)")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--tag", default=None, help="nombre de la corrida en runs/")
    ap.add_argument("--ids", default=None, help="ids separados por coma")
    ap.add_argument("--limite", type=int, default=None, help="solo las primeras N preguntas")
    ap.add_argument("--no-cache", action="store_true", help="regenera sin usar la caché")
    ap.add_argument("--desde-cero", action="store_true", help="no reanuda: sobrescribe la salida")
    args = ap.parse_args(argv)

    config.validar_final()
    entrada = args.input or ENTRADAS[args.split]
    if not entrada.is_file():
        print(f"No existe {entrada}.")
        return 1
    if not (config.index_dir / "index_manifest.json").is_file():
        print("No hay índice. Con corpus local: `python -m src.corpus.build` y "
              "`python -m src.index.build`; con el corpus de la nube: `python -m src.corpus.nube`.")
        return 1

    preguntas = leer_jsonl(entrada)
    if args.ids:
        ids = {int(x) for x in args.ids.split(",") if x.strip()}
        preguntas = [q for q in preguntas if q["id"] in ids]
    if args.limite:
        preguntas = preguntas[:args.limite]
    tag = args.tag or f"{datetime.now():%Y%m%d_%H%M}_{args.split}"
    dir_run = RAIZ / "runs" / tag
    salida = args.out or dir_run / "submissions.jsonl"

    from src.generation.llm import LLM
    from src.retrieval.hibrido import Recuperador

    print(f"Cargando índice y modelos… ({len(preguntas)} preguntas → {salida})", flush=True)
    rec = Recuperador.cargar()
    llm = LLM()
    res = ejecutar(preguntas, rec, llm, salida, dir_run, usar_cache=not args.no_cache,
                   reanudar=not args.desde_cero)
    t = res["tiempos"].get("s_total", {})
    print(f"\nListo: {res['respondidas_ahora']} nuevas, {res['ya_existentes']} ya existentes, "
          f"{res['errores_esquema']} con errores de esquema. s/pregunta p50={t.get('p50')} "
          f"p95={t.get('p95')}")
    print(f"Evaluar: python scripts/evaluate.py --submission {salida} --split {args.split}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
