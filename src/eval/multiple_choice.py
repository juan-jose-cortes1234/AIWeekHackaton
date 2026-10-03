"""Compara corridas MC por ID, sin cargar modelos ni ejecutar el juez.

python -m src.eval.multiple_choice --submission runs/mc_nuevo/submissions.jsonl \
    --baseline runs/muestra_v12/submissions.jsonl --out runs/mc_nuevo/comparacion.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from src.config import RAIZ
from src.oficial import common, citations


def leer(ruta):
    filas = [json.loads(l) for l in Path(ruta).read_text(encoding="utf-8").splitlines() if l.strip()]
    if len({x["id"] for x in filas}) != len(filas):
        raise ValueError(f"IDs duplicados en {ruta}")
    return filas


def comparar(preguntas, respuestas, baseline=None, trazas=None):
    oro = {q["id"]: q for q in preguntas if q.get("formato") == "multiple_choice"
           and q["id"] not in common.FLAWED_IDS}
    def mapa(filas):
        mc = [r for r in filas if r.get("formato") == "multiple_choice"
              and r["id"] not in common.FLAWED_IDS]
        if len({r["id"] for r in mc}) != len(mc):
            raise ValueError("La corrida tiene IDs MC duplicados.")
        return {r["id"]: r for r in mc}
    actual, anterior = mapa(respuestas), mapa(baseline or [])
    extras = set(actual) - set(oro)
    if extras:
        raise ValueError(f"IDs MC ajenos a la muestra evaluable: {sorted(extras)}")
    if baseline is not None and not set(actual) <= set(anterior):
        raise ValueError("El baseline no contiene todos los IDs MC de la corrida nueva.")
    traces = {t["id"]: t for t in (trazas or [])}
    detalle, ganancias, perdidas = [], [], []
    for qid in sorted(actual):
        q, r = oro[qid], actual[qid]
        acierto = not r.get("abstencion") and r.get("respuesta_correcta") == q["respuesta_correcta"]
        previo = anterior.get(qid)
        antes = (not previo.get("abstencion") and
                 previo.get("respuesta_correcta") == q["respuesta_correcta"]) if previo else None
        if antes is not None and acierto and not antes:
            ganancias.append(qid)
        if antes is not None and antes and not acierto:
            perdidas.append(qid)
        soporte = set().union(*(citations.extract(p.get("texto", ""))
                               for p in r.get("pasajes_recuperados", [])[:10]))
        ref = citations.extract(q.get("legal_basis") or "")
        tr = traces.get(qid, {})
        detalle.append({"id": qid, "esperada": q["respuesta_correcta"],
                        "respuesta": r.get("respuesta_correcta"), "acierto": acierto,
                        "baseline": previo.get("respuesta_correcta") if previo else None,
                        "baseline_acierto": antes,
                        "citas": citations.score(r.get("justificacion", ""),
                                                 q.get("legal_basis", ""), soporte),
                        "fundamento_citable": bool(ref),
                        "suficiencia_evidencia": "requiere_revision",
                        "cobertura_leida": tr.get("cobertura_leida"),
                        "fallback_mc": tr.get("fallback_mc"),
                        "json_valido": tr.get("json_valido"),
                        "latencia_ms": r.get("latencia_ms"),
                        "desde_cache": tr.get("desde_cache")})
    n = len(detalle)
    tiempos = [d["latencia_ms"] for d in detalle if d["latencia_ms"] is not None]
    return {"n": n, "aciertos": sum(d["acierto"] for d in detalle),
            "accuracy": sum(d["acierto"] for d in detalle) / n if n else None,
            "completa": set(actual) == set(oro), "ids_faltantes": sorted(set(oro) - set(actual)),
            "ganancias": ganancias, "perdidas": perdidas,
            "latencia_media_ms": mean(tiempos) if tiempos else None,
            "advertencia": "Presencia de citas no demuestra suficiencia; revisar evidencia por ítem.",
            "detalle": detalle}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--submission", type=Path, required=True)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--preguntas", type=Path, default=RAIZ / "data/sample_50.jsonl")
    ap.add_argument("--trazas", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    try:
        reporte = comparar(leer(args.preguntas), leer(args.submission),
                           leer(args.baseline) if args.baseline else None,
                           leer(args.trazas) if args.trazas else None)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    salida = args.out or args.submission.parent / "comparacion_mc.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MC {reporte['aciertos']}/{reporte['n']}; ganancias={reporte['ganancias']}; "
          f"pérdidas={reporte['perdidas']}; completa={reporte['completa']}")
    print(salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
