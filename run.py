"""Comando único de reproducción: `python run.py` (o `bash run.sh`).

1. Instala las dependencias si faltan.
2. Obtiene el corpus y el índice según `CORPUS_SOURCE`:
   - nube (por defecto si `CORPUS_ZIP_URL` tiene valor): descarga y verifica el zip publicado;
   - local: valida `fuentes.csv`, construye el corpus, la guardia anti-fuga, el manifiesto y
     el índice (idempotente: si nada cambió, no recalcula).
3. Corre el pipeline sobre la muestra (o el split indicado).
4. Califica con el evaluador oficial `scripts/evaluate.py` (con `--ragas` si hay llave y
   dependencias del juez).

Opciones: --split sample|test · --limite N · --rango INICIO FIN · --tag NOMBRE · --gpu ·
--indice-existente · --sin-ragas · --no-cache

En una máquina con GPU y el índice ya descomprimido en build/ (p. ej. el sábado, una parte del
banco por máquina):

    python run.py --split test --gpu --indice-existente --rango 1 250 --tag sabado_1
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
for _flujo in (sys.stdout, sys.stderr):        # consola de Windows (cp1252): tildes y flechas
    if hasattr(_flujo, "reconfigure") and (_flujo.encoding or "").lower() not in ("utf-8", "utf8"):
        _flujo.reconfigure(encoding="utf-8", errors="replace")
MODULOS = ("faiss", "sentence_transformers", "bm25s", "llama_cpp", "fitz", "jsonschema", "dotenv")


def paso(n: int, texto: str) -> None:
    print(f"\n=== [{n}/4] {texto}", flush=True)


def instalar_si_falta() -> None:
    faltan = [m for m in MODULOS if importlib.util.find_spec(m) is None]
    if not faltan:
        print("Dependencias presentes.")
        return
    print(f"Faltan {faltan}: instalando requirements.txt …", flush=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(RAIZ / "requirements.txt")],
                   check=True)


def preparar_corpus() -> None:
    from src.config import config

    config.validar_final()
    if config.fuente_corpus == "nube":
        from src.corpus.nube import ErrorNube, obtener

        try:
            info = obtener()
        except ErrorNube as e:
            sys.exit(f"ERROR (corpus en la nube): {e}")
        print(f"Corpus e índice de la nube listos (sha256 {info['sha256'][:12]}…).")
        return

    if not (config.corpus_raw_dir / "fuentes.csv").is_file():
        sys.exit("ERROR: no hay corpus. Configure CORPUS_ZIP_URL (+ CORPUS_ZIP_SHA256) para usar el "
                 "corpus publicado, o CORPUS_RAW_DIR con fuentes.csv (GUIA_CORPUS.md §3).")
    from src.corpus import build as corpus_build
    from src.corpus import manifest, validar
    from src.index import build as index_build

    salida = config.corpus_out_dir.parent
    for nombre, fn, argv in (
            ("validar fuentes.csv", validar.main, []),
            ("construir corpus (+ guardia anti-fuga)", corpus_build.main, ["--out", str(salida)]),
            ("manifiesto y CORPUS.md", manifest.main, []),
            ("índice FAISS + BM25", index_build.main, [])):
        print(f"--- {nombre}", flush=True)
        if fn(argv) != 0:
            sys.exit(f"ERROR en el paso: {nombre}")


def verificar_indice_existente() -> None:
    """--indice-existente: usar el índice de build/ tal cual (sin reconstruir el corpus).

    Comprueba que el manifiesto corresponda a chunks.jsonl e index.faiss (mismos sha256); así
    todas las máquinas usan exactamente el índice congelado.
    """
    import json

    from src.config import config
    from src.index.build import sha256_archivo

    config.validar_final()
    d = config.index_dir
    faltan = [n for n in ("chunks.jsonl", "index.faiss", "index_manifest.json", "bm25")
              if not (d / n).exists()]
    if faltan:
        sys.exit(f"ERROR (--indice-existente): faltan {faltan} en {d}. Descomprima el zip del "
                 "índice en la raíz del proyecto (docs/COMO_EJECUTAR.md §4).")
    m = json.loads((d / "index_manifest.json").read_text(encoding="utf-8"))
    if (m.get("sha256_chunks") != sha256_archivo(d / "chunks.jsonl")
            or m.get("sha256_faiss") != sha256_archivo(d / "index.faiss")):
        sys.exit("ERROR (--indice-existente): index_manifest.json no corresponde a chunks.jsonl / "
                 "index.faiss. Vuelva a descomprimir el zip del índice completo.")
    print(f"Índice existente verificado: {m.get('n_fragmentos')} fragmentos, "
          f"faiss {m['sha256_faiss'][:12]}…")


def ragas_disponible() -> bool:
    from src.config import config

    return bool(config.openrouter_api_key) and importlib.util.find_spec("ragas") is not None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=("sample", "test"), default="sample")
    ap.add_argument("--limite", type=int, default=None)
    ap.add_argument("--rango", type=int, nargs=2, metavar=("INICIO", "FIN"), default=None,
                    help="solo las preguntas en las posiciones INICIO a FIN (incluidas; 1 = la "
                         "primera). Para repartir el banco entre máquinas: 1 250, 251 500…")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--gpu", action="store_true",
                    help="encoder, reranker y decoder en CUDA (equivale a ENCODER_DEVICE=cuda y "
                         "DECODER_DEVICE=cuda en .env)")
    ap.add_argument("--indice-existente", action="store_true",
                    help="usar el índice ya presente en build/ (verificado por sha256) en lugar de "
                         "reconstruir corpus e índice")
    ap.add_argument("--sin-ragas", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args(argv)
    os.chdir(RAIZ)
    sys.path.insert(0, str(RAIZ))
    if args.gpu:
        # Antes de importar src.config (que lee el entorno al cargarse).
        os.environ.update({"ENCODER_DEVICE": "cuda", "DECODER_DEVICE": "cuda"})

    paso(1, "Dependencias")
    instalar_si_falta()

    paso(2, "Corpus e índice")
    if args.indice_existente:
        verificar_indice_existente()
    else:
        preparar_corpus()

    paso(3, f"Pipeline sobre '{args.split}'")
    from src.pipeline import main as pipeline

    tag = args.tag or f"{datetime.now():%Y%m%d_%H%M}_{args.split}"
    salida = RAIZ / "runs" / tag / "submissions.jsonl"
    argv_p = ["--split", args.split, "--tag", tag, "--out", str(salida)]
    if args.limite:
        argv_p += ["--limite", str(args.limite)]
    if args.rango:
        argv_p += ["--rango", str(args.rango[0]), str(args.rango[1])]
    if args.no_cache:
        argv_p.append("--no-cache")
    if pipeline.main(argv_p) != 0:
        return 1

    paso(4, "Evaluador oficial")
    if args.rango or args.limite:
        print("Corrida parcial: el evaluador oficial necesita todas las preguntas. Una las partes "
              "(cat runs/*/submissions.jsonl) y evalúe el resultado; ver docs/COMO_EJECUTAR.md §11.")
        return 0
    if args.split == "test" and not (RAIZ / "data" / "answer_key_992.jsonl").is_file():
        print("Split 'test': la clave de respuestas la tiene el jurado; no se evalúa aquí.")
        return 0
    cmd = [sys.executable, str(RAIZ / "scripts" / "evaluate.py"), "--submission", str(salida),
           "--split", args.split, "--out", str(salida.parent / "reporte.json")]
    if not args.sin_ragas and ragas_disponible():
        cmd.append("--ragas")
    else:
        print("(sin --ragas: falta OPENROUTER_API_KEY o `pip install -r "
              "scripts/requirements-evaluador.txt`)")
    return subprocess.run(cmd, env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode


if __name__ == "__main__":
    sys.exit(main())
