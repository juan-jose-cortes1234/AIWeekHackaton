# PROGRESO — bitácora de iteraciones

Cada iteración del loop añade una entrada **al final** con esta plantilla:

```
## <AAAA-MM-DD HH:MM> — Txx <título>
- Estado: hecho | parcial | bloqueado
- Qué se hizo:
- Cómo se verificó: (comandos y resultado)
- Métricas (si aplica): cerradas x/20 · citas x/20 · abstención x/10 · ragas x/30 · recall@10 cuerpos x · s/pregunta x
- Decisiones / cambios de diseño:
- Archivos creados/modificados:
- Siguiente paso:
```

## Estado inicial (2026-09-27)

- Hardware de desarrollo: AMD Ryzen 7 8840HS, Radeon 780M integrada (sin CUDA), 15 GB RAM.
  Python 3.9 instalado (se recomienda 3.11), Git 2.49, Docker 28.4. Ollama no instalado.
- Corpus: pendiente — lo construye el equipo en `CORPUS_RAW_DIR` siguiendo `GUIA_CORPUS.md`.
- Llave `OPENROUTER_API_KEY`: pendiente — el usuario la pondrá en `.env` (solo para el juez).
- Decisiones iniciales: Qwen3-8B (Apache-2.0) como decoder, bge-m3 (MIT) como
  encoder, bge-reranker-v2-m3 (Apache-2.0), FAISS `IndexFlatIP` + BM25 híbrido.

## Puntajes sobre la muestra

| Fecha | Run | Docs | Fragmentos | Cerradas /20 | Citas /20 | Abstención /10 | RAGAS /30 | Total | s/preg | Nota |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|

---

## 2026-09-27 — T01 Estructura y material oficial
- Estado: hecho
- Qué se hizo: copiados `data/`, `schema/`, `scripts/` del material oficial a la raíz; creado el árbol de paquetes (`src/{corpus,index,retrieval,generation/prompts,pipeline,eval}`, `interfaz/`, `tests/fixtures/`) con `__init__.py`; `LICENSE` Apache-2.0 (texto oficial de apache.org).
- Cómo se verificó: `python scripts/evaluate.py --submission "InformacionReto/Hackathon 2026/Ejemplo de entrega/submissions.jsonl" --split sample` → 1 error de validación (45 ítems faltantes, esperado), citas: 7 aciertos, 7 respaldados, 0 sin respaldo. `.gitignore` cubre `.env`, `build/`, `runs/`, `dist/`, `corpus_raw/`.
- Métricas: n/a
- Decisiones / cambios de diseño: ninguno. Nota: en esta máquina el evaluador necesita `PYTHONIOENCODING=utf-8` para imprimir tildes en consola Windows.
- Archivos creados/modificados: `data/*`, `schema/*`, `scripts/*` (copias), `LICENSE`, `src/**/__init__.py`, `interfaz/__init__.py`, `tests/__init__.py`, `PLAN.md`.
- Siguiente paso: T02 entorno (.venv con Python ≥ 3.10).

## 2026-09-27 — T02 Entorno
- Estado: hecho
- Qué se hizo: instalado `uv` (pip --user) → Python 3.11.16 gestionado por uv → `.venv`. Instaladas dependencias (torch CPU 2.14.0, sentence-transformers 6.1.0, faiss-cpu 1.15.1, bm25s, pymupdf, selectolax, bs4, python-docx, jsonschema, python-dotenv, httpx, gdown, fastapi, uvicorn, pytest). `requirements.txt` con versiones fijadas (índice CPU de PyTorch como extra). El juez sigue en `scripts/requirements-evaluador.txt` (no instalado aún; se instala en T23).
- Cómo se verificó: `.venv/Scripts/python.exe -m pytest -q` → 3 passed (versión de Python, imports, `citations.extract` del evaluador oficial).
- Decisiones: usar siempre `.venv/Scripts/python.exe` (Windows) / `.venv/bin/python` (Linux). `uv` mostró un aviso sobre el enlace de versión menor de Python; no afecta al venv.
- Archivos creados/modificados: `.venv/` (ignorado), `requirements.txt`, `tests/test_entorno.py`, `PLAN.md`.
- Siguiente paso: T03 configuración (`src/config.py`).

## 2026-09-27 — T03 Configuración
- Estado: hecho
- Qué se hizo: `src/config.py` con `Config` inmutable leída de `.env` + entorno (el entorno manda), conversión de tipos, rutas relativas a la raíz, `fuente_corpus` (resuelve `auto` → nube/local), `validar_final()` (temperatura 0, valores válidos) y `repr` que enmascara `OPENROUTER_API_KEY`, `DECODER_API_KEY` y `HF_TOKEN`.
- Cómo se verificó: `pytest -q` → 8 passed; `config.validar_final()` pasa con el `.env` actual; modo de corpus actual = local (sin enlace a la nube todavía).
- Archivos creados/modificados: `src/config.py`, `tests/test_config.py`, `PLAN.md`.
- Siguiente paso: T04 validador de `fuentes.csv`.

## HITO F0 listo — base del repositorio
- Qué funciona: estructura del proyecto, material oficial en la raíz (`data/`, `schema/`, `scripts/`), `LICENSE` Apache-2.0, entorno `.venv` con Python 3.11 y dependencias fijadas, configuración central desde `.env`.
- Cómo probarlo:
  - `python -m pip install uv && python -m uv venv --python 3.11 .venv`
  - `python -m uv pip install --python .venv/Scripts/python.exe -r requirements.txt`
  - `.venv/Scripts/python.exe -m pytest -q` (8 pruebas)
  - `python scripts/evaluate.py --submission "InformacionReto/Hackathon 2026/Ejemplo de entrega/submissions.jsonl" --split sample`
- Mensaje de commit sugerido: `F0: estructura del repo, material oficial, entorno Python 3.11 y configuración central`
