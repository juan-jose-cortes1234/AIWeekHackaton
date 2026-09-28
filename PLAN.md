# PLAN — backlog ordenado del loop

Estados: `[ ]` pendiente · `[~]` en curso · `[x]` hecho · `[B]` bloqueado por humanos (ver sección Bloqueos).
Regla: el loop toma **la primera tarea `[ ]` cuyas dependencias estén `[x]`**.
Una tarea demasiado grande para una iteración se divide aquí mismo en subtareas `Txx.a`, `Txx.b`.

Fechas clave: viernes 2 oct 2026 17:00 (reporte de avance con puntaje de muestra) ·
sábado 3 oct 9:00–15:00 (ejecución ciega de 992 + interfaz) · 15:00 verificación en vivo.

---

## F0 — Base del repositorio

- [x] **T01 Estructura y material oficial.** (Sin git: el repositorio lo crea el usuario.) Copiar `InformacionReto/Hackathon 2026/{data,schema,scripts}` a la raíz; crear árbol de `docs/ARQUITECTURA.md §1`; `.gitignore` (ya existe, completarlo); `LICENSE` (Apache-2.0 para código).
  *Acepta:* `python scripts/evaluate.py --submission "InformacionReto/Hackathon 2026/Ejemplo de entrega/submissions.jsonl" --split sample` corre (con el error esperado de 45 faltantes) y el reporte muestra 7 aciertos de citación; `.gitignore` cubre `.env`, `build/`, `runs/` y `corpus_raw/`.
- [x] **T02 Entorno.** `.venv` con Python ≥ 3.10 (intentar `uv python install 3.11`; si no, `py` disponible; si solo existe 3.9, dejar `[B]` con instrucción de instalación y seguir con 3.9 sin usar sintaxis ≥ 3.10). `requirements.txt` fijado (faiss-cpu, sentence-transformers, bm25s, pymupdf, selectolax o bs4, python-docx, jsonschema, python-dotenv, httpx, pytest, fastapi, uvicorn). `requirements-evaluador.txt` aparte.
  *Acepta:* `pytest -q` corre (aunque haya 0 pruebas); `python -c "import faiss, sentence_transformers"` funciona.
- [x] **T03 Configuración.** `src/config.py` lee `.env` (con `python-dotenv`), valores por defecto seguros, valida `DECODER_TEMPERATURE == 0` en modo final y nunca imprime secretos. Prueba de que `repr(config)` enmascara llaves.
  *Acepta:* prueba unitaria pasa.

## F1 — Ingesta y normalización (paso 1)

- [x] **T04 Validador de fuentes.** `python -m src.corpus.validar` lee `CORPUS_RAW_DIR/fuentes.csv` (formato en `GUIA_CORPUS.md §3`) y reporta errores legibles por fila. Si la carpeta está vacía o no existe: mensaje claro, código de salida 0 y marca `[B] corpus` en Bloqueos (el resto del loop sigue con fixtures).
  *Acepta:* pruebas con CSV de fixture (`,` y `;`, BOM, filas malas).
- [x] **T05 Extractores.** HTML (encoding Senado/SUIN, limpieza de navegación, unión de páginas `_prNNN`), PDF (pymupdf + OCR opcional si `pytesseract` y `tesseract` existen), DOCX, TXT.
  *Acepta:* pruebas con fixtures mínimos creados por el loop marcados `TEXTO DE PRUEBA`.
- [x] **T06 Segmentador por artículo** para normas + por secciones/ventanas para sentencias, con metadatos (tipo, número, año, artículo, órgano, vigencia, áreas, sección).
  *Acepta:* pruebas de regex con variantes (`ARTÍCULO 1o.`, `ARTICULO 11A.`, `Artículo 5 bis`, `ART. 20.`, transitorios, parágrafos) y de sentencias.
- [x] **T07 Encabezado canónico + literalidad.** Genera `build/corpus/<doc_id>.txt` y `build/indice/chunks.jsonl`. Pruebas: (a) 100 % de fragmentos con cuerpo reconocido por `scripts/citations.py`; (b) `texto == corpus[inicio:fin]`.
  *Acepta:* `python -m src.corpus.build` sobre fixtures produce ambos archivos y las pruebas pasan.
- [x] **T08 Guardia anti-fuga.** Prueba que falla si algún fragmento comparte un 8-grama normalizado con cualquier `pregunta` o `respuesta_esperada` de `data/sample_50.jsonl` (salvo que el 8-grama también sea texto normativo literal: listar coincidencias para revisión humana, no borrar nada solo) y si algún archivo de `data/` está dentro de `CORPUS_RAW_DIR`.
- [x] **T09 Manifiesto y bitácora.** `python -m src.corpus.manifest` escribe `corpus_manifest.json` (campos oficiales + sha256, n_articulos, n_fragmentos) y regenera las tablas marcadas de `CORPUS.md` (inventario, totales, cobertura por área con ítems del banco). La prosa de `CORPUS.md` (criterio, método) la escribe el equipo; el loop deja borradores marcados `<!-- BORRADOR -->`.

## F2 — Índice y recuperación (paso 2)

- [x] **T10 Encoder + FAISS.** `python -m src.index.build`: embeddings con caché por hash, `IndexFlatIP`, `index_manifest.json`, idempotente. Medir tiempo por 1.000 fragmentos en CPU y anotarlo en `PROGRESO.md`.
- [x] **T11 BM25** con tokenizador jurídico español (conserva números y `c-355`). Persistido junto al índice.
- [x] **T12 Recuperador híbrido** (router de citas explícitas + RRF + boost por área + diversidad + desempate estable). `python -m src.retrieval.buscar "pregunta"` imprime top-10.
- [x] **T13 Métricas de recuperación y brechas.** `python -m src.eval.recuperacion --split sample`: por ítem, ¿algún pasaje del top-10 contiene un cuerpo del `legal_basis`? (recall@10 de cuerpos, por área). `python -m src.eval.brechas`: lista cuerpos de `legal_basis` de la muestra y de `seed_targets.json` que **no existen en el corpus**, ordenados por `items_del_banco`, y lo escribe en `docs/BRECHAS.md` para el equipo. (Usa la muestra solo para medir, nunca para indexar.)
- [x] **T14 Reranker** `bge-reranker-v2-m3` opcional (`USE_RERANKER`). Medir recall@10 y latencia con/sin.

## F3 — Generación, citas y abstención (pasos 3 y 4)

- [x] **T15 Cliente del decoder** en proceso desde Hugging Face, sin servidores ni APIs: backend `llamacpp` (`llama-cpp-python` + `Qwen/Qwen3-8B-GGUF` / `Qwen3-8B-Q4_K_M.gguf` descargado con `huggingface_hub`) y backend `transformers` (`Qwen/Qwen3-8B`, para GPU). Temperatura 0, semilla fija, Qwen3 sin razonamiento (`enable_thinking=False`), salida JSON forzada (gramática/JSON schema en llamacpp; parser + reintento en transformers), caché de generaciones, `validar_final()` con la lista blanca antes de cargar. `python -m src.generation.ping` carga el modelo real y genera un JSON corto. Si `llama-cpp-python` no instala en Windows (requiere rueda precompilada o compilador), anotar `[B] decoder` con instrucciones concretas.
- [x] **T16 Prompts por formato** (`src/generation/prompts/*.txt`) y constructor de contexto `[P1]…[P10]`. MC con recuperación por opción (pregunta + texto de la opción) fusionada.
- [x] **T17 Post-filtro de citas** (ARQUITECTURA §6) + render determinista de `referencia_legal` / “Fundamento normativo”. Prueba: `citas_sin_respaldo == 0` sobre salidas simuladas con citas inventadas.
- [x] **T18 Abstención** (ARQUITECTURA §7) con umbral configurable; nunca en MC.
- [x] **T19 Pipeline principal.** `python -m src.pipeline.main --split sample|test --input <jsonl> --out submissions.jsonl [--ids ...] [--no-cache]`: valida contra `schema/submission.schema.json`, `latencia_ms`, reanudable, trazas en `runs/<tag>/trazas.jsonl`.
- [x] **T19b Corpus desde la nube** (`src/corpus/nube.py`, ARQUITECTURA §1.1): `python -m src.corpus.nube` descarga `CORPUS_ZIP_URL`, verifica `CORPUS_ZIP_SHA256`, valida la estructura y descomprime en `build/`. Conversión de enlaces Drive/OneDrive/Dropbox/Zenodo. Mientras no exista el enlace, queda probado con un zip de fixture en un servidor HTTP local y se anota `[B] enlace nube` en Bloqueos.
  *Acepta:* prueba con fixture pasa; con `CORPUS_ZIP_URL` vacío, mensaje claro de cómo configurarlo.
- [x] **T20 Comando único.** `run.sh` y `run.py`: (1) instala dependencias si faltan, (2) obtiene el corpus e índice según `CORPUS_SOURCE` (por defecto la nube vía T19b; modo local solo para desarrollo), (3) corre el pipeline sobre la muestra, (4) corre `scripts/evaluate.py` (con `--ragas` solo si hay llave). `Dockerfile` que ejecuta `bash run.sh`. Probar `docker build` localmente.

## F4 — Medición e iteración (hasta el viernes)

- [ ] **T21 Línea base** sin `--ragas`: correr la muestra completa, guardar `runs/<fecha>_base/reporte.json`, anotar puntajes en `PROGRESO.md` y en la tabla de evolución de `CORPUS.md`.
- [ ] **T22 Experimentos** (uno por iteración, registrados en `docs/EXPERIMENTOS.md` con hipótesis, cambio, resultado y decisión): pesos RRF, k, reranker, boost de área, nº de cuerpos en `referencia_legal`, prompt MC por opción, longitud de respuestas, umbral de abstención, bge-m3 vs e5-large. Mantener la mejor configuración en `.env.example`/`config.py`. **No sobreajustar a 50 ítems**: preferir cambios con justificación general.
- [ ] **T23 RAGAS.** Cuando `OPENROUTER_API_KEY` exista: `python scripts/evaluate.py ... --ragas` sobre la mejor configuración (máximo 1 corrida con juez por día salvo que el usuario pida más). Si la llave falta: `[B] llave`.
- [ ] **T24 Latencia y plan de hardware.** Medir p50/p95 en el hardware disponible; proyectar 992 ítems; documentar en `docs/RUNBOOK_SABADO.md` la configuración GPU (sala Turing/Colab con backend `transformers` o `llamacpp` CUDA) y un plan B.

## F5 — Entregables

- [ ] **T25 Interfaz gráfica** (`interfaz/`): pregunta libre + selector de formato/área, respuesta, pasajes con score y enlace, normas citadas marcadas respaldadas/no; identidad Software Colombia. Prueba de humo con `httpx`.
- [ ] **T26 README.md** según `InformacionReto/Hackathon 2026/entregables/sabado/README_EQUIPO.md` (arquitectura, reproducción, hardware, resultados, limitaciones, sección `## Corpus e índice`).
- [ ] **T27 Empaquetado del corpus.** `python -m src.corpus.empaquetar` → `dist/corpus_<equipo>.zip` con `LICENSE` (CC-BY-4.0 para el trabajo de procesamiento), `corpus_manifest.json`, `corpus/`, `indice/`; imprime sha256 y las dos líneas exactas para pegar en `.env` (`CORPUS_ZIP_URL=` vacío para que el equipo lo complete y `CORPUS_ZIP_SHA256=<hash>`). Subirlo a la nube lo hace el equipo. Prueba de ida y vuelta: empaquetar → servir local → T19b lo descarga → mismo resultado de recuperación.
- [ ] **T28 Borradores de informes**: `docs/INFORME_TECNICO.md` (≤ 3 páginas) y `docs/REPORTE_AVANCE.md` (1 página) con números reales de `runs/`. La exportación a PDF la hace el equipo.
- [ ] **T29 Runbook del sábado** (`docs/RUNBOOK_SABADO.md`): congelar índice, lanzar 992 con reanudación, monitoreo, validar esquema, `src/eval/verificar.py` para la verificación en vivo, checklist oficial de `entregables/sabado/README.md`.
- [ ] **T30 Ensayo general**: simular el sábado con la muestra desde cero en Docker con el comando único; cronometrar; corregir lo que falle.

---

## Bloqueos (requieren acción humana)

- [B] 2026-09-28 T20 docker: Docker Desktop no está abierto. Abrirlo y correr `docker build -t hackathon-rag .` (luego `docker run --rm --env-file .env -v hf-cache:/root/.cache/huggingface hackathon-rag`, que necesita `CORPUS_ZIP_URL`).
- [B] 2026-09-28 T19b enlace nube: falta el zip publicado. Generarlo con `python -m src.corpus.empaquetar` (T27), subirlo con acceso público y pegar `CORPUS_ZIP_URL` y `CORPUS_ZIP_SHA256` en `.env`; luego `python -m src.corpus.nube`.
- [B] 2026-09-27 T14 medición: comparar recall@10 con y sin reranker (`python -m src.eval.recuperacion` con `USE_RERANKER=1` y `0`) requiere el corpus real.
- [B] 2026-09-27 T04 corpus: `CORPUS_RAW_DIR` (./corpus_raw) aún no existe. Crear la carpeta con `fuentes.csv` (plantilla en `docs/fuentes.ejemplo.csv`) y los documentos según `GUIA_CORPUS.md §3`; apuntar `CORPUS_RAW_DIR` en `.env`. Mientras tanto el loop sigue con fixtures.

<!-- El loop añade aquí entradas con: fecha, tarea, qué falta, instrucción concreta. Ejemplo:
- [B] 2026-09-28 T04 corpus: CORPUS_RAW_DIR vacío. Llenar según GUIA_CORPUS.md §3.
-->
