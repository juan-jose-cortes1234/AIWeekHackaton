"""Interfaz gráfica: `python -m interfaz.app` → http://localhost:8000

Consulta de extremo a extremo con el mismo pipeline de la entrega (recuperación
híbrida + reranker + Qwen3-8B + post-filtro de citas + abstención) y
visualización de los pasajes recuperados y de las normas citadas, marcadas como
respaldadas o no por la evidencia (rúbrica §6.2).

- `POST /api/recuperar`: solo evidencia (rápido), para mostrarla mientras se genera.
- `POST /api/consulta`: respuesta completa + pasajes + citas.
"""
from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import config
from src.corpus.fuentes import normalizar_area
from src.generation.citas import cuerpos, localizar, respaldadas
from src.generation.responder import recuperar
from src.oficial import AREAS

ESTATICOS = Path(__file__).resolve().parent / "static"
CAMPOS_TEXTO = {
    "multiple_choice": ("justificacion",),
    "semi_open": ("respuesta", "referencia_legal"),
    "open_ended": ("marco_normativo", "analisis", "jurisprudencia", "conclusion"),
}


class Consulta(BaseModel):
    pregunta: str = Field(min_length=5, max_length=4000)
    formato: str = Field(default="semi_open", pattern="^(multiple_choice|semi_open|open_ended)$")
    area: str | None = None
    opciones: dict[str, str] | None = None
    sin_cache: bool = False


def _item(c: Consulta) -> dict:
    area = normalizar_area(c.area) if c.area else None
    item = {"id": 0, "formato": c.formato, "pregunta": c.pregunta.strip(), "area": area}
    if c.formato == "multiple_choice":
        opciones = {k.strip().upper(): v.strip() for k, v in (c.opciones or {}).items() if v.strip()}
        if len(opciones) < 2:
            raise HTTPException(422, "Una pregunta de selección múltiple necesita al menos 2 opciones.")
        item["opciones"] = opciones
    return item


def _pasajes_json(pasajes) -> list[dict]:
    return [{"n": n, "doc_id": p.doc_id, "encabezado": p.texto.split("\n", 1)[0],
             "texto": p.texto, "score": round(p.score, 4), "rerank": p.score_rerank,
             "origen": p.origen, "url": (p.meta or {}).get("url"),
             "inicio": p.inicio, "fin": p.fin}
            for n, p in enumerate(pasajes, start=1)]


def _citas_json(linea: dict, pasajes) -> list[dict]:
    soporte = respaldadas(pasajes)
    texto = " ".join(str(linea.get(k) or "") for k in CAMPOS_TEXTO[linea["formato"]])
    vistas, res = set(), []
    for i, f, cuerpo in sorted(localizar(texto)):
        if cuerpo in vistas:
            continue
        vistas.add(cuerpo)
        fuentes = [n for n, p in enumerate(pasajes[:10], start=1) if cuerpo in cuerpos(p.texto)]
        res.append({"cita": texto[i:f], "cuerpo": list(cuerpo), "respaldada": cuerpo in soporte,
                    "pasajes": fuentes})
    return res


def crear_app(rec=None, llm=None) -> FastAPI:
    app = FastAPI(title="RAG de derecho colombiano — Hackathon 2026")
    estado = {"rec": rec, "llm": llm, "error": None}
    cerrojo = threading.Lock()             # un modelo, una generación a la vez

    def recursos(necesita_llm: bool):
        with cerrojo:
            try:
                if estado["rec"] is None:
                    from src.retrieval.hibrido import Recuperador

                    estado["rec"] = Recuperador.cargar()
                if necesita_llm and estado["llm"] is None:
                    from src.generation.llm import LLM

                    estado["llm"] = LLM()
            except Exception as e:  # índice ausente, modelo no descargado…
                estado["error"] = str(e)
                raise HTTPException(503, f"No se pudo cargar el sistema: {e}") from e
        return estado["rec"], estado["llm"]

    @app.get("/api/estado")
    def api_estado():
        return {"indice": (config.index_dir / "index_manifest.json").is_file(),
                "recuperador_cargado": estado["rec"] is not None,
                "decoder_cargado": estado["llm"] is not None, "error": estado["error"],
                "encoder": config.encoder_model, "reranker": config.reranker_model,
                "decoder": f"{config.decoder_gguf_repo}/{config.decoder_gguf_file}"
                if config.decoder_backend == "llamacpp" else config.decoder_model,
                "areas": AREAS}

    @app.post("/api/recuperar")
    def api_recuperar(c: Consulta):
        item = _item(c)
        rec, _ = recursos(necesita_llm=False)
        t0 = time.perf_counter()
        pasajes = recuperar(item, rec)
        return {"pasajes": _pasajes_json(pasajes), "segundos": round(time.perf_counter() - t0, 2)}

    @app.post("/api/consulta")
    def api_consulta(c: Consulta):
        from src.pipeline.main import responder_item

        item = _item(c)
        rec, llm = recursos(necesita_llm=True)
        with cerrojo:
            linea, traza = responder_item(item, rec, llm, usar_cache=not c.sin_cache)
        pasajes = recuperar(item, rec)
        return {"respuesta": {k: v for k, v in linea.items() if k != "pasajes_recuperados"},
                "pasajes": _pasajes_json(pasajes), "citas": _citas_json(linea, pasajes),
                "traza": {k: traza[k] for k in ("motivo", "pertinencia_max", "pasajes_leidos",
                                                "citas_eliminadas", "s_recuperacion",
                                                "s_generacion", "s_total", "desde_cache")}}

    @app.get("/")
    def inicio():
        return FileResponse(ESTATICOS / "index.html")

    app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")
    return app


def main() -> None:
    import uvicorn

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--puerto", type=int, default=8000)
    args = ap.parse_args()
    print(f"Interfaz en http://{args.host}:{args.puerto}  (los modelos se cargan con la primera consulta)")
    uvicorn.run(crear_app(), host=args.host, port=args.puerto)


if __name__ == "__main__":
    main()
