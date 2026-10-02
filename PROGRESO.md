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
| 2026-09-29 | muestra_colab (T4) | 186 | 41.384 | 12,00 | 15,51 | 7,79 | 13,37 | 48,67/80 | 34,9 | Línea base |
| 2026-09-30 | muestra_t22 (T4) | 186 | 41.336 | 12,00 | 15,10 | 7,67 | 12,62 | 47,39/80 | 31,7 | C-01..C-05: neutro/levemente peor |
| 2026-10-01 | muestra_v2 (T4) | 238 | 45.201 | 12,00 | 15,92 | 7,91 | 13,81 | **49,64/80** | 33,4 | Corpus v2 (+52 fuentes) + C-06 (MC elegir primero) |
| 2026-10-01 | muestra_v3 (Kaggle T4) | 338 | 68.603 | 12,00 | 15,10 | 7,67 | 11,45 | 46,22/80 | 29,4 | Corpus v3 (+100 leyes y decretos) + C-07 (consulta por opción) |
| 2026-10-01 | muestra_v4 (Kaggle T4) | 338 | 68.603 | 13,33 | 13,88 | 7,67 | 5,23* | 40,11/80* | 39,7 | C-09 (razonamiento en MC) + C-10 (tope de complementarias). *El juez no dio veredicto en 21 de 33 |
| 2026-10-01 | muestra_v6 (Kaggle T4) | 338 | 68.603 | 13,33 | 14,29 | 7,67 | 11,03* | 46,32/80* | — | C-11 (abiertas ≤ 200 palabras; no se acortaron por el postproceso). *7 de 33 sin veredicto del juez |
| 2026-10-01 | muestra_v7 (Colab T4) | 338 | 68.603 | 13,33 | 14,29 | 7,67 | 13,28 | 48,57/80 | — | Igual que v6 + C-12; **juez con 0 fallos** (Colab) |
| 2026-10-02 | muestra_v8 (Kaggle T4) | 618 | 75.204 | 12,00 | 14,29 | 7,44 | 13,07* | 46,80/80 | — | Corpus v4 (+280 conceptos, resoluciones y circulares). *1 de 33 sin veredicto |

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

## 2026-09-27 — T04 Validador de fuentes
- Estado: hecho
- Qué se hizo: `src/oficial.py` (acceso único a `scripts/citations.py` y `scripts/common.py` del evaluador oficial); `src/corpus/fuentes.py` (lectura con `,`/`;` y BOM, validación por fila: columnas, doc_id único y en snake_case, tipo, numero/anio según tipo, formato de sentencia `C-355`, archivo existente, url http(s), fecha ISO, áreas por nombre oficial o slug, vigencia); CLI `python -m src.corpus.validar [--dir]`. Plantilla para el equipo: `docs/fuentes.ejemplo.csv`.
- Cómo se verificó: `pytest -q` → 15 passed. `python -m src.corpus.validar` sin corpus → mensaje con instrucciones, código 0.
- Decisiones: códigos (`tipo=codigo`) sin numero/anio solo generan aviso, no error.
- Archivos creados/modificados: `src/oficial.py`, `src/corpus/fuentes.py`, `src/corpus/validar.py`, `tests/test_fuentes.py`, `docs/fuentes.ejemplo.csv`, `PLAN.md` (bloqueo corpus).
- Siguiente paso: T05 extractores (HTML/PDF/DOCX/TXT).

## 2026-09-27 — T05 Extractores
- Estado: hecho
- Qué se hizo: `src/corpus/extraer.py`. HTML con BeautifulSoup (UTF-8 o windows-1252, quita script/style/nav/header/footer/form, respeta bloques y `<br>`); PDF con pymupdf (quita encabezados/pies repetidos en ≥ 60 % de páginas y números de página, une guiones de fin de línea, OCR con pytesseract solo si está instalado, si no avisa); DOCX con párrafos y tablas; TXT con detección de codificación. Una carpeta se procesa uniendo sus archivos en orden alfabético (páginas `_prNNN` del Senado). Un archivo dañado genera aviso, no detiene la ingesta.
- Cómo se verificó: `pytest -q` → 23 passed (8 nuevas con HTML cp1252, carpeta multipágina, PDF con y sin texto, DOCX, TXT, archivo dañado).
- Decisiones: OCR es opcional (tesseract no está instalado en esta máquina ni en requirements); el equipo debe preferir HTML sobre PDF escaneado (ya dicho en GUIA_CORPUS §4).
- Archivos creados/modificados: `src/corpus/extraer.py`, `tests/test_extraer.py`, `PLAN.md`.
- Siguiente paso: T06 segmentador por artículo y por secciones de sentencia.

## 2026-09-27 — T06 Segmentador
- Estado: hecho
- Qué se hizo: `src/corpus/segmentar.py`. Normas: un segmento por artículo con regex tolerante (`1o.`, `11A`, `5 bis`, `ART.`, `240-1` del ET, `2.2.1.1.1` de decretos únicos, transitorios, `12º.-`), sin cortar en referencias como “Artículo 5 de la Ley…”; notas del Senado (vigencia, jurisprudencia, legislación anterior) como segmento `nota` ligado al artículo; concordancias descartadas; repeticiones de un número de artículo (texto anterior citado) van a la nota; encabezados LIBRO/TÍTULO/CAPÍTULO como `seccion` de contexto; preámbulo aparte. Sentencias/conceptos: secciones (síntesis, antecedentes, consideraciones, problema jurídico, decisión, RESUELVE, salvamentos…) y ventanas de ~300 palabras con 15 % de solape respetando párrafos. Documentos sin artículos caen a ventanas.
- Cómo se verificó: `pytest -q` → 40 passed (17 nuevas).
- Decisiones: la partición por longitud del encoder y el encabezado canónico quedan para T07 (`src/corpus/fragmentar.py`). Validar con documentos reales del Senado cuando llegue el corpus (formatos de nota pueden variar).
- Archivos creados/modificados: `src/corpus/segmentar.py`, `tests/test_segmentar.py`, `PLAN.md`.
- Siguiente paso: T07 encabezado canónico, fragmentos, `build/corpus/*.txt` y `chunks.jsonl` con literalidad.

## 2026-09-27 — T07 Encabezado canónico, fragmentos y literalidad
- Estado: hecho
- Qué se hizo: `src/corpus/fragmentar.py` (nombre canónico por tipo: Constitución, códigos con alias “Código General del Proceso (Ley 1564 de 2012)”, “Estatuto Tributario (Decreto 624 de 1989)”, leyes/decretos “Ley N de AAAA”, sentencias “Sentencia C-355 de 2006 de la Corte Constitucional”, Decisión 486; encabezados por artículo, transitorio, nota, preámbulo y sección; partición de segmentos > 300 palabras en ventanas con “(parte k de n)” y encabezado repetido). `src/corpus/build.py` (`python -m src.corpus.build`): escribe `build/corpus/<doc_id>.txt`, `build/indice/chunks.jsonl` (chunk_id, offsets, metadatos, cuerpos reconocidos) y `build/corpus/_resumen.json` (sha256, n_articulos, n_fragmentos, avisos); avisa si un documento no produce cita reconocible. Fixture compartido `tests/conftest.py` con 6 documentos TEXTO DE PRUEBA.
- Cómo se verificó: `pytest -q` → 52 passed. Pruebas clave: (a) 100 % de fragmentos con el cuerpo de su documento según `scripts/citations.py`; (b) `txt[inicio:fin] == texto` en todos; nombres canónicos de 9 tipos reconocidos por el evaluador.
- Decisiones: MAX_PALABRAS = 300 por fragmento (≈ 450 tokens de bge-m3, cabe en 512 con el encabezado). El `.txt` procesado es la secuencia de fragmentos (con solapes repetidos), así los offsets son literales.
- Archivos creados/modificados: `src/corpus/fragmentar.py`, `src/corpus/build.py`, `tests/conftest.py`, `tests/test_build.py`, `GUIA_CORPUS.md` (nota sobre códigos), `PLAN.md`.
- Siguiente paso: T08 guardia anti-fuga.

## 2026-09-27 — T08 Guardia anti-fuga
- Estado: hecho
- Qué se hizo: `src/corpus/fuga.py` (`python -m src.corpus.fuga`). Grave (bloquea): archivos del corpus crudo con marcas de banco (`respuesta_esperada`, `legal_basis`, `respuesta_correcta`), `CORPUS_RAW_DIR` dentro de `data/`, fragmentos con ≥ 3 8-gramas de una pregunta o ≥ 50 % de los 8-gramas de una respuesta esperada. Menor: se lista para revisión humana (típicamente la respuesta cita literal una norma). Integrado en `python -m src.corpus.build`: escribe `build/corpus/_fuga.json` y sale con código 1 si hay graves.
- Cómo se verificó: `pytest -q` → 58 passed (corpus de prueba limpio contra la muestra real; pregunta copiada, respuesta copiada y banco dentro del crudo detectados; coincidencia menor no bloquea).
- Decisiones: umbrales de 8-gramas (3 para preguntas, 50 % para respuestas) para no castigar citas literales legítimas de normas. T10 debe negarse a indexar si `_fuga.json` tiene graves.
- Archivos creados/modificados: `src/corpus/fuga.py`, `src/corpus/build.py`, `tests/test_fuga.py`, `tests/test_build.py`, `PLAN.md`.
- Siguiente paso: T09 manifiesto y bitácora (cierra F1).

## 2026-09-27 — T09 Manifiesto y bitácora
- Estado: hecho
- Qué se hizo: `src/corpus/manifest.py` (`python -m src.corpus.manifest`): escribe `corpus_manifest.json` en la raíz (campos oficiales + tipo, vigencia, n_articulos, n_fragmentos, metodo_ingesta, sha256; licencia CC-BY-4.0; enlace de la nube desde `.env`) y regenera los bloques AUTO de `CORPUS.md` (inventario, totales, cobertura por área con ítems del banco y cobertura estimada del seed). `CORPUS.md` creado en la raíz con la estructura oficial, método de ingesta ya redactado según lo implementado y borradores marcados para la prosa del equipo. `build.py` ahora registra formatos de origen por documento.
- Cómo se verificó: `pytest -q` → 60 passed (manifiesto con campos oficiales y sha256, tablas generadas, idempotencia, cobertura del seed). Sin corpus real, el CLI informa que falta correr el build.
- Archivos creados/modificados: `src/corpus/manifest.py`, `src/corpus/build.py`, `CORPUS.md`, `tests/test_manifest.py`, `PLAN.md`.
- Siguiente paso: F2, T10 encoder + FAISS.

## HITO F1 listo — ingesta y normalización
- Qué funciona: validación de `fuentes.csv`, extracción HTML/PDF/DOCX/TXT, segmentación por artículo y por sección de sentencia, encabezado canónico reconocido por el evaluador en el 100 % de los fragmentos, offsets literales, guardia anti-fuga que bloquea el build, manifiesto y tablas de la bitácora.
- Cómo probarlo (cuando exista el corpus en `CORPUS_RAW_DIR`):
  - `.venv/Scripts/python.exe -m src.corpus.validar`
  - `.venv/Scripts/python.exe -m src.corpus.build`
  - `.venv/Scripts/python.exe -m src.corpus.manifest`
  - Sin corpus: `.venv/Scripts/python.exe -m pytest -q` (60 pruebas con corpus de prueba).
- Mensaje de commit sugerido: `F1: ingesta del corpus (validación, extracción, segmentación por artículo, encabezado canónico, anti-fuga, manifiesto)`

## 2026-09-27 — T10 Encoder + FAISS
- Estado: hecho
- Qué se hizo: `src/index/encoder.py` (sentence-transformers, vectores normalizados float32, prefijos `query:`/`passage:` solo para E5, caché persistente de embeddings por sha256 del texto en `build/cache/emb/`); `src/index/build.py` (`python -m src.index.build [--forzar]`): `IndexFlatIP`, `index_manifest.json` (modelo, dimensión, n, sha256 de chunks.jsonl e index.faiss, fecha, tiempo), idempotente, se niega a indexar si `_fuga.json` tiene graves.
- Cómo se verificó: `pytest -q` → 65 passed (encoder falso determinista: recuperación exacta del fragmento, idempotencia, caché persistente, bloqueo por fuga, prefijos E5). Medición real de bge-m3 descargado (~4,3 GB en caché HF):
  - carga del modelo: 14 s · dimensión 1024
  - **CPU (Ryzen 7 8840HS): 687 s por 1.000 fragmentos de ~300 palabras (0,69 s/fragmento)**
  - consulta: ~31 ms
- Riesgo: un corpus de 20–40 mil fragmentos tardaría 4–8 h en CPU. Mitigaciones: (1) construir el índice en GPU (Colab / sala Turing) y traer `build/` (FAISS es portable; la caché evita recalcular); (2) incorporar documentos por tandas (la caché hace incremental cada reconstrucción); (3) si hace falta, `ENCODER_MAX_LENGTH=384` o fragmentos más cortos. Para la ejecución del sábado, codificar consultas en el mismo tipo de dispositivo con que se midió la muestra.
- Archivos creados/modificados: `src/index/encoder.py`, `src/index/build.py`, `tests/test_index.py`, `CORPUS.md` (método: indexación), `PLAN.md`.
- Siguiente paso: T11 BM25 con tokenizador jurídico.

## 2026-09-27 — T11 BM25
- Estado: hecho
- Qué se hizo: `src/index/lexico.py`: tokenizador jurídico (normaliza como el evaluador, conserva números, `c-355`, `sl3385`→`sl-3385`, `240-1`, `2.2.1.1.1`, `1o.`→`1`; stopwords; stemming Snowball español) e `IndiceBM25` (bm25s) con construir/guardar/cargar, puntajes sobre todo el corpus y top-k con desempate estable por id. `python -m src.index.build` ahora construye FAISS **y** BM25 (`INDEX_DIR/bm25/`); también `python -m src.index.lexico` por separado.
- Cómo se verificó: `pytest -q` → 69 passed (identificadores conservados, plural/singular unificados, “artículo 1820” vs “artículo 1796” distinguidos, persistencia idéntica, consulta vacía, desempate).
- Nota: Snowball no unifica “sociedad/sociedades” (socied/sociedad); limitación conocida del stemmer, la mitiga la búsqueda densa.
- Archivos creados/modificados: `src/index/lexico.py`, `src/index/build.py`, `tests/test_lexico.py`, `PLAN.md`.
- Siguiente paso: T12 recuperador híbrido.

## 2026-09-27 — T12 Recuperador híbrido (+ corrección: sin modelos falsos)
- Estado: hecho
- Qué se hizo: `src/retrieval/hibrido.py` (`Recuperador`): router de citas explícitas por metadatos (artículo + cuerpo normativo del documento, incluidos alias como Ley 1150 de 2007 o CGP), denso (FAISS) + BM25 por cada consulta (pregunta y consultas extra, p. ej. opciones de MC) fusionados con RRF ponderado, boosts por área y por norma mencionada, diversidad (máx. 3 fragmentos por artículo/sección), desempates por id y scores redondeados; `Pasaje.a_entrega()` con la forma del esquema oficial. Verifica que el índice se construyó con el mismo encoder. CLI `python -m src.retrieval.buscar "pregunta" [--area] [-k]`. Parámetros en `config.py` / `.env.example` (CANDIDATOS, RRF_K, PESO_DENSO, PESO_BM25, BOOST_AREA, BOOST_CUERPO, MAX_POR_ARTICULO).
- Corrección pedida por el usuario: eliminados los encoders falsos de las pruebas; todas usan el bge-m3 real (fixture de sesión `encoder_real`). Regla añadida a `CLAUDE.md` y `LOOP.md`: nada de modelos falsos/mocks; si un modelo o servidor no está, la tarea queda `[B]`.
- Bug encontrado y corregido: `CacheEmbeddings` fijaba su carpeta al importar, y las pruebas escribían en la caché real `build/cache/`; ahora se resuelve en tiempo de llamada. Se borró la caché contaminada.
- Cómo se verificó: `pytest -q` → 76 passed en ~60 s (router por artículo y por alias, determinismo, diversidad, pasajes literales reconocidos por el evaluador, consultas extra, rechazo de encoder distinto). `build/` queda intacto tras las pruebas.
- Archivos creados/modificados: `src/retrieval/hibrido.py`, `src/retrieval/buscar.py`, `src/config.py`, `.env.example`, `src/index/encoder.py`, `tests/conftest.py`, `tests/test_index.py`, `tests/test_hibrido.py`, `tests/falsos.py` (eliminado), `CLAUDE.md`, `LOOP.md`, `PLAN.md`.
- Siguiente paso: T13 métricas de recuperación y reporte de brechas.

## 2026-09-27 — T13 Métricas de recuperación y brechas
- Estado: hecho
- Qué se hizo: `src/eval/recuperacion.py` (`python -m src.eval.recuperacion`): por ítem citable, acierto@10 (algún pasaje trae un cuerpo del `legal_basis`) y recall de cuerpos@10, por área, con detalle de faltantes; en MC usa las opciones como consultas extra; guarda `runs/<fecha>_recuperacion/reporte.json`. `src/eval/brechas.py` (`python -m src.eval.brechas`): genera `docs/BRECHAS.md` con las normas del seed que faltan ordenadas por `items_del_banco` y las normas citadas en la muestra que faltan. Fixture de sesión `indice_prueba` (mini-corpus indexado con bge-m3 real) compartido por las pruebas.
- Cómo se verificó: `pytest -q` → 78 passed. `docs/BRECHAS.md` generado ya (sin corpus: todo figura como faltante, sirve de lista de trabajo del equipo).
- Archivos creados/modificados: `src/eval/recuperacion.py`, `src/eval/brechas.py`, `tests/test_eval_recuperacion.py`, `tests/conftest.py`, `tests/test_hibrido.py`, `docs/BRECHAS.md`, `PLAN.md`.
- Siguiente paso: T14 reranker bge-reranker-v2-m3 (real).

## 2026-09-27 — T14 Reranker
- Estado: hecho (la comparación de recall con/sin reranker queda `[B]` hasta tener corpus real)
- Qué se hizo: `src/retrieval/reranker.py` (CrossEncoder `BAAI/bge-reranker-v2-m3`, pertinencia en [0,1]); integrado en `Recuperador`: reordena los `RERANK_CANDIDATOS` (20 por defecto) mejores de la fusión RRF, el router sigue primero, desempate por id, `score_rerank` en cada pasaje. Se activa/desactiva con `USE_RERANKER`. Pruebas con el reranker real (fixture de sesión `reranker_real`).
- Cómo se verificó: `pytest -q` → 81 passed (~4 min, modelos reales en CPU).
- Medición real: carga ~2 min la primera vez (descarga ~2,2 GB), **~15 s por 30 pares en CPU** (≈ 0,5 s por candidato). Con 20 candidatos ≈ 10 s por pregunta en CPU: no cabe en el presupuesto del sábado sin GPU (≈ 20 s por pregunta en total, incluida la generación). En GPU es < 1 s. Decisión: por defecto activado (el sábado corre en GPU); para desarrollo en CPU se puede usar `USE_RERANKER=0` o `RERANK_CANDIDATOS=8`.
- Archivos creados/modificados: `src/retrieval/reranker.py`, `src/retrieval/hibrido.py`, `src/config.py`, `.env.example`, `tests/conftest.py`, `tests/test_reranker.py`, `CORPUS.md`, `PLAN.md`.
- Siguiente paso: F3, T15 cliente del decoder (Qwen3-8B real; requiere servidor Ollama o equivalente).

## HITO F2 listo — índice y recuperación
- Qué funciona: embeddings bge-m3 con caché incremental, FAISS exacto con manifiesto/sha256 (congelable), BM25 jurídico, recuperador híbrido determinista (router de artículos citados, RRF, boosts, diversidad), reranker bge-reranker-v2-m3, métrica de recuperación sobre la muestra y reporte de brechas (`docs/BRECHAS.md`). Todo probado con los modelos reales, sin dobles.
- Cómo probarlo (con corpus en `CORPUS_RAW_DIR`):
  - `.venv/Scripts/python.exe -m src.corpus.build`
  - `.venv/Scripts/python.exe -m src.index.build`
  - `.venv/Scripts/python.exe -m src.retrieval.buscar "¿Cuál es el plazo para liquidar un contrato estatal?" --area administrativo`
  - `.venv/Scripts/python.exe -m src.eval.recuperacion`
  - `.venv/Scripts/python.exe -m src.eval.brechas`
  - Sin corpus: `.venv/Scripts/python.exe -m pytest -q` (81 pruebas, ~4 min).
- Riesgos anotados: embedding en CPU ≈ 11,5 min/1.000 fragmentos; reranker en CPU ≈ 0,5 s/candidato ⇒ construir el índice y correr el sábado en GPU.
- Mensaje de commit sugerido: `F2: índice bge-m3 + FAISS, BM25 jurídico, recuperador híbrido con reranker, métricas de recuperación y brechas`

## 2026-09-27 — Decisión: sin `openai_compat`, decoder en proceso desde Hugging Face
- Pedido del usuario: quitar el backend `openai_compat` (aunque solo era un protocolo HTTP para servir modelos abiertos, abría la puerta a apuntar por error a un modelo cerrado) y no depender de Ollama.
- Qué se hizo: `src/config.py` sin `decoder_base_url`/`decoder_api_key`/`decoder_timeout_s`; backends válidos `llamacpp` (GGUF `Qwen/Qwen3-8B-GGUF`, `Qwen3-8B-Q4_K_M.gguf`) y `transformers` (`Qwen/Qwen3-8B`); nuevos `DECODER_GGUF_REPO`, `DECODER_GGUF_FILE`, `DECODER_DEVICE`, `DECODER_THREADS`. **Lista blanca `MODELOS_ABIERTOS`** (decoder, encoder, reranker) verificada por `validar_final()`: rechaza GPT, Gemini, jina-v3, Cohere, `openai_compat`… `.env` y `.env.example` actualizados (solo el bloque del decoder; la llave del juez no se tocó). `CLAUDE.md`, `docs/ARQUITECTURA.md` §5 y §8, `PLAN.md` T15 y T24 actualizados.
- Cómo se verificó: `pytest -q tests/test_config.py` → 11 passed (acepta los modelos por defecto; rechaza 5 configuraciones cerradas).
- Archivos creados/modificados: `src/config.py`, `.env`, `.env.example`, `tests/test_config.py`, `CLAUDE.md`, `docs/ARQUITECTURA.md`, `PLAN.md`.

## 2026-09-27 — T15 Cliente del decoder (Qwen3-8B real, en proceso)
- Estado: hecho (backend `transformers` implementado pero sin verificar: necesita GPU; se valida en la sala Turing)
- Qué se hizo: `src/generation/llm.py` (`LLM`): valida la lista blanca antes de cargar; backend `llamacpp` (descarga `Qwen/Qwen3-8B-GGUF/Qwen3-8B-Q4_K_M.gguf` con `huggingface_hub`, JSON forzado con `response_format` + schema), backend `transformers` (`Qwen/Qwen3-8B`, bf16, `enable_thinking=False`, voraz); temperatura 0, top_k 1, semilla fija, `/no_think`; parser JSON tolerante + un reintento; caché de generaciones en `build/cache/gen/` con clave sha256 (modelo, mensajes, esquema, parámetros) y `usar_cache=False` para la verificación en vivo. `python -m src.generation.ping [--sin-cache]`. `llama-cpp-python==0.3.35` (rueda precompilada CPU) y `huggingface_hub` en `requirements.txt`.
- Cómo se verificó: `pytest -q tests/test_llm.py` → 8 passed con el modelo real (JSON válido, respuesta correcta a una MC trivial, **misma salida en dos generaciones sin caché**, caché, rechazo de modelo fuera de la lista blanca, parser). `ping`: carga 11 s, JSON correcto.
- **Medición real en CPU (Ryzen 7 8840HS, Q4_K_M):** prompt de 10 pasajes = 4.188 tokens + 63 de salida → **130 s por pregunta**. ⇒ 992 preguntas ≈ 36 h en CPU: el sábado **requiere GPU** (o varias máquinas en paralelo).
- Para probar en la sala Turing (GPU NVIDIA): `pip install -r requirements.txt` y luego una de dos:
  - `DECODER_BACKEND=transformers`, `DECODER_DEVICE=cuda` (bf16, ~16 GB de VRAM), o
  - reinstalar llama-cpp-python con CUDA: `pip install llama-cpp-python==0.3.35 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 --force-reinstall --no-deps` y `DECODER_DEVICE=cuda`.
  - Medir con `python -m src.generation.ping --sin-cache` y con el pipeline completo cuando exista (T19).
- Archivos creados/modificados: `src/generation/llm.py`, `src/generation/ping.py`, `tests/test_llm.py`, `requirements.txt`, `PLAN.md`.
- Siguiente paso: T16 prompts por formato y constructor de contexto.

## 2026-09-28 — T16 Prompts por formato y constructor de contexto
- Estado: hecho
- Qué se hizo: `src/generation/prompts/{sistema,multiple_choice,semi_open,open_ended}.txt` (solo instrucciones, sin ejemplos de contenido jurídico: usar solo la evidencia, citar con nombre completo y año, primera oración directa, longitudes del enunciado, `pasajes_usados`). `src/generation/contexto.py`: evidencia `[P1]…[Pn]` con encabezado intacto y cuerpo recortado (`PASAJES_PROMPT=10`, `PALABRAS_POR_PASAJE=180`, para bajar el costo del prompt), JSON schema por formato con las claves del evaluador + `pasajes_usados` (enum de letras en MC; `descarte_opciones` con las letras), `MAX_TOKENS` por formato. `src/generation/responder.py`: recuperar (en MC, pregunta + cada opción como consultas extra) → mensajes → generar.
- Bug encontrado: `maxLength` en el schema genera una gramática de un nivel por carácter y llama.cpp falla (access violation). Se quitó; la longitud se controla con `MAX_TOKENS` y el post-proceso (T17).
- Cómo se verificó: `pytest -q tests/test_contexto.py` → 7 passed; incluye una respuesta **real de punta a punta** (bge-m3 + reranker + Qwen3-8B) sobre el mini-corpus: recupera el artículo 1820 del Código Civil primero y responde la opción correcta con JSON válido.
- Archivos creados/modificados: `src/generation/prompts/*.txt`, `src/generation/contexto.py`, `src/generation/responder.py`, `src/config.py`, `.env`, `.env.example`, `tests/test_contexto.py`, `PLAN.md`.
- Siguiente paso: T17 post-filtro de citas y render determinista de referencias.

## 2026-09-28 — Decisión: flujo final sin recorte de pasajes
- Medición en CPU (mismo prompt de 10 pasajes): completos (4.188 tokens) **158 s**; recortados a 180 palabras (2.708 tokens) **102 s**. En CPU ninguno cabe en el sábado (≈ 44 h vs ≈ 28 h para 992); en GPU la diferencia es marginal.
- Decisión del usuario: el flujo final usa **pasajes completos** (`PALABRAS_POR_PASAJE=0`, nuevo valor por defecto); el recorte queda solo como perilla para pruebas en CPU.
- Archivos modificados: `src/config.py`, `src/generation/contexto.py`, `.env`, `.env.example`, `tests/test_contexto.py`.

## 2026-09-28 — T17 Post-filtro de citas y render de referencias
- Estado: hecho
- Qué se hizo: `src/generation/citas.py`. (1) `completar_anios`: “Ley 1150” → “Ley 1150 de 2007” si los pasajes resuelven el año de forma única. (2) `localizar`: spans de cada cita usando las mismas expresiones regulares de `scripts/citations.py` sobre una normalización que conserva offsets; `filtrar`: reemplaza por “la normativa aplicable” cada cita no respaldada por los 10 primeros pasajes (incluye “el artículo N del…” y “la Sentencia…” previos), y si aun así queda algo sin respaldo descarta la oración. (3) `referencias`: render desde el encabezado canónico de los pasajes usados por el modelo + los pertinentes (rerank ≥ `UMBRAL_CITA`=0,5 o router), sin repetir, máx. `MAX_REFERENCIAS`=6. (4) `postprocesar` por formato: MC añade “Fundamento normativo: …” a la justificación y quita la letra elegida de `descarte_opciones`; semiabierta: `referencia_legal` renderizada, respuesta ≤ 5 oraciones y ≤ 150 palabras, 3–6 palabras clave; abierta: añade al marco las normas usadas que no estén ya citadas, análisis ≤ 8 oraciones. `pasajes_usados` no pasa a la entrega.
- Cómo se verificó: `pytest -q tests/test_citas.py` → 9 passed, **calificando con el evaluador oficial** (`evaluate.answer_text`, `citas_respaldadas`, `citations.score`): `citas_sin_respaldo == 0` en los 3 formatos con salidas que traían normas inventadas; `localizar` extrae exactamente los mismos cuerpos que el evaluador; el texto filtrado conserva el contenido y se lee bien.
- Incidente: al editar regex con un heredoc de bash se escribieron caracteres de retroceso (0x08) en lugar de `\b`; detectado por el resultado y corregido. Lección: editar regex con la herramienta Edit, no con heredocs.
- Archivos creados/modificados: `src/generation/citas.py`, `tests/test_citas.py`, `src/config.py`, `.env.example`, `PLAN.md`.
- Siguiente paso: T18 abstención.

## 2026-09-28 — T18 Abstención
- Estado: hecho (umbral a calibrar con la muestra cuando haya corpus: T22)
- Qué se hizo: `src/generation/abstencion.py`. `decidir()`: MC nunca; texto libre se abstiene si no hay pasajes, si el modelo no produjo campos utilizables, o si la pertinencia máxima (reranker; si está apagado, similitud densa) está bajo `UMBRAL_ABSTENCION`=0,05 (`UMBRAL_ABSTENCION_DENSO`=0,35); nunca si el router encontró un artículo citado en la pregunta. `registro_abstencion()`: campos vacíos, `abstencion: true`, pasajes conservados (como el ítem 218 del ejemplo oficial).
- Cómo se verificó: `pytest -q tests/test_abstencion.py` → 6 passed; el registro valida contra `schema/submission.schema.json`; con el recuperador real, una pregunta ajena al mini-corpus provoca abstención en semiabierta y no en MC, y una pregunta cubierta no se abstiene.
- Archivos creados/modificados: `src/generation/abstencion.py`, `tests/test_abstencion.py`, `src/config.py`, `.env.example`, `PLAN.md`.
- Siguiente paso: T19 pipeline principal (prototipo de punta a punta para medir en Turing).

## 2026-09-28 — T19 Pipeline principal (prototipo de punta a punta)
- Estado: hecho
- Qué se hizo: `src/pipeline/main.py` (`python -m src.pipeline.main --split sample|test [--input] [--out] [--tag] [--ids] [--limite] [--no-cache] [--desde-cero]`): por ítem recuperar → generar → post-filtro de citas → abstención → validación contra `schema/submission.schema.json` (una línea inválida nunca se escribe: se sustituye por respaldo determinista en MC o abstención en texto libre) → escritura inmediata con flush (reanudable: salta ids ya presentes). Respaldo MC si el modelo no da letra: opción más pertinente según el reranker. Trazas por ítem (`trazas.jsonl`: pasajes y scores, pasajes leídos/usados, citas eliminadas, referencias, tokens, tiempos) y `tiempos.json` (media, p50, p95 por etapa).
- Bug real encontrado por la prueba: con pasajes completos el prompt puede superar la ventana de contexto y llama.cpp lanza excepción (tumbaría la corrida del sábado). Solución: `LLM.contar_tokens` + `responder.mensajes_que_caben`, que quita pasajes **enteros desde el final** (menos pertinentes) hasta que prompt + salida quepan; `pasajes_recuperados` siempre lleva los 10 completos. Coherente con la decisión de no recortar pasajes.
- Enunciado revisado (pregunta del usuario): no exige pasar pasajes completos al decoder (B.4, B.1, §4.4: diseño del prompt es decisión del equipo); lo obligatorio es que toda norma citada esté en `pasajes_recuperados` de la entrega (paso 4), lo que se cumple siempre.
- Cómo se verificó: `pytest -q tests/test_pipeline.py` → 2 passed con bge-m3 + reranker + Qwen3-8B reales sobre el mini-corpus: 3 líneas válidas según el esquema oficial; MC correcta; semiabierta con `referencia_legal` “Ley 1150 de 2007, artículo 11”; pregunta ajena → abstención; **0 citas sin respaldo según el evaluador oficial**; reanudación sin regenerar; recorte por contexto verificado.
- Tiempos en CPU (incluye reranker y generación): 158,9 s / 157,4 s / 140,8 s por pregunta.
- Archivos creados/modificados: `src/pipeline/main.py`, `src/generation/llm.py`, `src/generation/responder.py`, `tests/test_pipeline.py`, `PLAN.md`.
- Siguiente paso: T19b corpus desde la nube; luego T20 comando único (cierra F3).
- **Prototipo listo para Turing:** con índice construido, `python -m src.pipeline.main --split sample --limite 5` y revisar `runs/<tag>/tiempos.json`.

## 2026-09-28 — T19b Corpus desde la nube
- Estado: hecho (el enlace real queda `[B]` hasta que el equipo publique el zip)
- Qué se hizo: `src/corpus/nube.py` (`python -m src.corpus.nube [--forzar]`): convierte enlaces de compartir (Google Drive vía gdown; OneDrive/SharePoint `download=1`; Dropbox `dl=1`; Zenodo `download=1`; directas), descarga en streaming con reanudación y barra de progreso, detecta si el enlace devuelve una página de inicio de sesión en vez del zip, verifica `CORPUS_ZIP_SHA256` (si no coincide, se niega: índice congelado), valida la estructura oficial (LICENSE, manifiesto, corpus/*.txt, índice FAISS, chunks, manifiesto del índice, BM25) y que el encoder del índice sea el de `.env`, y extrae a `CORPUS_OUT_DIR`/`INDEX_DIR` (acepta carpeta raíz dentro del zip; bloquea rutas `..`). Marca `.origen_nube.json` para no repetir la descarga.
- Cómo se verificó: `pytest -q tests/test_nube.py` → 6 passed: ida y vuelta con un zip del índice real del mini-corpus servido por HTTP local ⇒ **mismos pasajes y scores** que el índice original; hash incorrecto rechazado; zip incompleto rechazado; enlace vacío con mensaje claro; enlace que devuelve HTML rechazado; conversión de enlaces. `python -m src.corpus.nube` sin enlace → mensaje de cómo configurarlo.
- Archivos creados/modificados: `src/corpus/nube.py`, `tests/test_nube.py`, `PLAN.md`.
- Siguiente paso: T20 comando único y Dockerfile (cierra F3).

## 2026-09-28 — T20 Comando único (EN CURSO, pausado por el usuario)
- Estado: parcial
- Qué se hizo: `run.py` (dependencias → corpus nube/local con validar, build, anti-fuga, manifiesto e índice → pipeline → evaluador oficial, con `--ragas` solo si hay llave y dependencias del juez; opciones `--split`, `--limite`, `--tag`, `--sin-ragas`, `--no-cache`), `run.sh` (venv fuera de Docker, `EN_CONTENEDOR` dentro), `Dockerfile` (python:3.11-slim, `CORPUS_SOURCE=nube`, `--env-file .env`), `.dockerignore` (excluye `.env`, build, runs, corpus crudo…).
- Falta: (1) prueba de humo de `bash run.sh --limite 1 --sin-ragas` con el mini-corpus en una carpeta temporal (el usuario pausó antes de correrla); (2) `docker build` — Docker Desktop no estaba abierto (`[B]`: abrir Docker Desktop).
- Archivos creados: `run.py`, `run.sh`, `Dockerfile`, `.dockerignore`, `PLAN.md`.
- Siguiente paso: correr la prueba de humo del comando único; luego `docker build`.

## 2026-09-28 — T20 Comando único (cierre)
- Estado: hecho (salvo `docker build`: `[B]` hasta abrir Docker Desktop)
- Cómo se verificó: `bash run.sh --limite 1 --sin-ragas` en una carpeta temporal con el mini-corpus (`CORPUS_SOURCE=local`): dependencias OK → validar → build + anti-fuga → manifiesto → índice FAISS + BM25 → pipeline (1 pregunta de la muestra, id 51) → `scripts/evaluate.py` corrió y emitió el reporte: la MC respondida fue **correcta** y con **0 citas sin respaldo** (el resto cuenta como fallo por ser una corrida de 1 ítem sobre el mini-corpus).
- Incidente: el paso de manifiesto escribe `corpus_manifest.json` y las tablas AUTO de `CORPUS.md` en la raíz; la prueba con el mini-corpus los ensució. Se restauraron (tablas vacías, manifiesto borrado) y se borró `runs/smoke_t20`. Con el corpus real ese comportamiento es el deseado. Nota para pruebas de humo futuras: correrlas en una copia del repo.
- Archivos: `run.py`, `run.sh`, `Dockerfile`, `.dockerignore`, `PLAN.md`.

## HITO F3 listo — generación, citas, abstención, pipeline y comando único
- Qué funciona: Qwen3-8B en proceso desde Hugging Face (lista blanca de modelos abiertos, temperatura 0, determinista), prompts por formato con evidencia completa y salvaguarda de ventana de contexto, post-filtro de citas (0 sin respaldo según el evaluador oficial), referencias renderizadas desde metadatos, abstención (nunca en MC), pipeline reanudable con trazas y tiempos, corpus desde la nube (zip verificado por sha256) y comando único `bash run.sh` / `python run.py` + `Dockerfile`.
- Cómo probarlo:
  - `.venv/Scripts/python.exe -m pytest -q` (suite completa con modelos reales; tarda varios minutos en CPU)
  - Con índice construido: `python -m src.pipeline.main --split sample --limite 5`
  - Comando único: `bash run.sh` (usa `CORPUS_ZIP_URL` si existe; si no, `CORPUS_RAW_DIR`)
- Pendiente humano: corpus real, enlace de la nube, llave del juez, GPU (Turing) y abrir Docker Desktop.
- Mensaje de commit sugerido: `F3: decoder Qwen3-8B, prompts, filtro de citas, abstención, pipeline, corpus desde la nube y comando único`

## 2026-09-28 — T25 Interfaz gráfica
- Estado: hecho (paleta de Software Colombia aproximada; confirmar con su guía de marca)
- Qué se hizo: `interfaz/app.py` (FastAPI; `python -m interfaz.app` → http://localhost:8000). `POST /api/recuperar` (evidencia rápida) y `POST /api/consulta` (mismo `responder_item` del pipeline de la entrega: recuperación + reranker + Qwen3-8B + filtro de citas + abstención), `GET /api/estado`; modelos cargados en la primera consulta; una generación a la vez. Frontend estático `interfaz/static/{index.html,styles.css,app.js}`: pregunta, formato (con opciones A–D para MC), área, “regenerar sin caché”; muestra la evidencia mientras se genera; respuesta por campos del formato; **normas citadas marcadas como respaldadas (con enlace al pasaje) o sin respaldo**; pasajes con encabezado, pertinencia del reranker, origen (router/denso/bm25), offsets y enlace a la fuente; tiempos y citas eliminadas. Identidad: turquesa del cubo de Software Colombia, fondo negro y franjas azules diagonales de la portada del enunciado; Playfair Display + Roboto.
- Cómo se verificó: `pytest -q tests/test_interfaz.py` → 4 passed con modelos reales (página y estáticos, estado, recuperación con el artículo 1820 primero, 422 en MC sin opciones, consulta completa con todas las citas respaldadas). Revisión visual en el navegador con una demo del mini-corpus: se corrigieron (1) las franjas que tapaban el título en pantallas angostas y (2) la tarjeta de resultados visible antes de consultar (`[hidden]` anulado por `display: grid`).
- Rúbrica §6.2 (10 pts): consulta de extremo a extremo (4) ✔; pasajes y normas citadas por respuesta (3) ✔; identidad visual (3) ✔ aproximada.
- Archivos creados: `interfaz/app.py`, `interfaz/static/*`, `tests/test_interfaz.py`, `PLAN.md`.
- Siguiente paso: T26 README.

## 2026-09-28 — T26 README
- Estado: hecho (con marcadores `<…>` para lo que depende del equipo: nombre, integrantes, enlace/tamaño/sha256 del zip, fecha de vigencia, puntajes y tiempos medidos, limitaciones observadas)
- Qué se hizo: `README.md` según la plantilla oficial `README_EQUIPO.md`: sección obligatoria `## Corpus e índice` (tabla, sha256, contenido del zip, vigencia), reproducción con comando único (`bash run.sh` / `python run.py`, Docker), requisitos de hardware con la medición real en CPU, tabla de comandos por etapa, arquitectura (diagrama + tabla de componentes con motivos), estructura del repo, tabla de resultados, interfaz, limitaciones, nota de transparencia sobre el uso de un asistente de programación y licencias.
- Cómo se verificó: todos los comandos listados existen como módulos (`python -m …`) implementados en F0–F5; revisión contra la checklist de `entregables/sabado/README.md`.
- Archivos: `README.md`, `PLAN.md`.
- Siguiente paso: T27 empaquetado del corpus.

## 2026-09-28 — T27 Empaquetado del corpus
- Estado: hecho (el zip real se genera cuando exista el corpus indexado)
- Qué se hizo: `src/corpus/empaquetar.py` (`python -m src.corpus.empaquetar [--out]`) → `dist/corpus_<equipo>.zip` con `LICENSE` (texto legal completo de CC-BY-4.0 descargado de creativecommons.org a `docs/LICENSE-CORPUS-CC-BY-4.0.txt`), `corpus_manifest.json`, `corpus/*.txt` e `indice/` (FAISS, chunks, manifiesto, BM25). **Zip determinista** (entradas ordenadas, fechas fijas): mismo contenido ⇒ mismo sha256. Se niega a publicar si falta algo, si la guardia anti-fuga reportó graves o si el índice está desactualizado respecto a `chunks.jsonl`. Imprime el sha256 y las líneas exactas para `.env` y el README.
- Cómo se verificó: `pytest -q tests/test_empaquetar.py` → 4 passed (estructura oficial validada por `nube.validar_zip`, determinismo, nombre por equipo, ida y vuelta empaquetar → extraer → mismos pasajes, rechazo de índice desactualizado). CLI sin índice → mensaje claro.
- Archivos: `src/corpus/empaquetar.py`, `docs/LICENSE-CORPUS-CC-BY-4.0.txt`, `tests/test_empaquetar.py`, `PLAN.md`.
- Siguiente paso: T28 borradores del informe técnico y del reporte de avance.

## 2026-09-28 — T28 Borradores de informes
- Estado: hecho (borradores; los números de la muestra se completan cuando exista el corpus)
- Qué se hizo: `informe/INFORME_TECNICO.md` (estructura oficial de `entregables/sabado/INFORME_TECNICO.md`, en `informe/` como pide la estructura del repo: arquitectura en 5 etapas, selección de modelos con motivos y alternativas descartadas, configuración de inferencia con los tiempos medidos, estrategia de recuperación, verificación de citas y abstención, tabla de resultados y limitaciones) y `docs/REPORTE_AVANCE.md` (estructura oficial del viernes, con instrucciones de envío, arquitectura y riesgos con mitigaciones). Marcadores `<…>` para puntajes, estado del corpus y tiempos en GPU.
- Cómo se verificó: contenido contrastado con el código y con las mediciones de `PROGRESO.md`; el informe tiene ~970 palabras (holgado para 3 páginas en PDF, deja espacio para resultados y análisis de errores); el reporte ~390 (1 página).
- Archivos: `informe/INFORME_TECNICO.md`, `docs/REPORTE_AVANCE.md`, `PLAN.md`.
- Siguiente paso: T29 runbook del sábado y verificador para la verificación en vivo.

## 2026-09-28 — T29 Runbook del sábado + herramientas de verificación
- Estado: hecho
- Qué se hizo: `docs/RUNBOOK_SABADO.md` (preparación hasta el viernes con índice congelado y proyección de tiempos; recepción de preguntas; ejecución reanudable; plan B con varias máquinas; validación; checklist oficial de cierre; verificación en vivo; problemas frecuentes). `src/eval/verificar.py` (`python -m src.eval.verificar --ids … --split test`): regenera sin caché y compara pasajes (doc_id, inicio, fin), normas citadas, abstención y letra con `submissions.jsonl`. `src/eval/validar_entrega.py`: esquema oficial, ids completos y sin duplicados, formato coherente, pasajes presentes, ≤ 10 pasajes. Pipeline más robusto: (1) una excepción en un ítem ya no tumba la corrida (respuesta de respaldo válida y error en la traza); (2) `--particion k/n` para repartir entre máquinas.
- Cómo se verificó: `pytest -q tests/test_verificar.py` → 3 passed (simulacro real: generar y regenerar sin caché ⇒ COINCIDE; comparación detecta cambios de normas y pasajes pero no de redacción; validación de entrega). `pytest -k "particion or falla" tests/test_pipeline.py` → 2 passed (particiones cubren todo sin solaparse; una pregunta que excede la ventana del modelo provoca una excepción real de llama.cpp y la corrida sigue con la siguiente). `validar_entrega` sobre el ejemplo oficial detecta los 45 faltantes.
- Archivos: `docs/RUNBOOK_SABADO.md`, `src/eval/verificar.py`, `src/eval/validar_entrega.py`, `src/pipeline/main.py`, `tests/test_verificar.py`, `tests/test_pipeline.py`, `PLAN.md`.
- Siguiente paso: T30 ensayo general.

## 2026-09-28 — T30 Ensayo general (Docker, contenedor limpio)
- Estado: hecho (con el mini-corpus de prueba; repetir con el corpus real y en GPU antes del viernes)
- Qué se hizo:
  1. Copia limpia del repo en una carpeta temporal (sin `.git`, `.venv`, `build`, `.env`) → flujo del equipo completo: `validar` → `build` (+ anti-fuga) → `manifest` → `index.build` → `empaquetar` ⇒ zip oficial (16 fragmentos, sha256 `e72c92ca…`) en 54 s.
  2. `docker build -t hackathon-rag .` ⇒ imagen de 2,34 GB, sin errores (valida `Dockerfile` y `requirements.txt` en Linux limpio).
  3. Zip servido por HTTP local como “nube”; `docker run … hackathon-rag bash run.sh --limite 2 --sin-ragas` con `CORPUS_ZIP_URL`/`CORPUS_ZIP_SHA256` y la caché de Hugging Face montada, **configuración completa con reranker**.
- Resultado (14:26:38 → 14:37:34, 11 min): dependencias OK; zip descargado y sha256 verificado; 2 preguntas respondidas (265 s y 231 s), 0 errores de esquema; evaluador oficial: 1 de 2 MC correcta, **2 aciertos de citación, 0 citas sin respaldo**; único error de validación = 48 ítems no corridos (esperado).
- Hallazgos: (1) Docker Desktop tenía 7,9 GB de RAM y los tres modelos requieren ~10 GB ⇒ el usuario subió WSL2 a 12 GB con `.wslconfig`; requisito **≥ 12 GB** documentado en el README. (2) En CPU dentro de Docker ~250 s por pregunta ⇒ las 50 de muestra ~3,5 h: documentado; conviene preguntar al organizador qué hardware usa la verificación de reproducibilidad.
- Archivos: `README.md` (requisitos de hardware), `PLAN.md`.

## HITO F5 listo — entregables
- Qué funciona: interfaz gráfica (T25), README (T26), empaquetado determinista del corpus (T27), borradores del informe técnico y del reporte (T28), runbook del sábado con verificador y validador de entrega, pipeline tolerante a fallos y con particiones (T29), ensayo general en Docker con configuración completa (T30).
- Quedan en manos del equipo (bloqueos en `PLAN.md`): corpus real → T21/T22; llave del juez → T23; medición en GPU → T24; publicar el zip (`CORPUS_ZIP_URL`).
- Mensaje de commit sugerido: `F5: interfaz, README, empaquetado del corpus, informes, runbook del sábado, verificación en vivo y ensayo en Docker`

## 2026-09-29 — Corpus real: validación, construcción y verificación de autenticidad
- Corpus crudo del equipo en `./corpus_raw` (186 documentos: 79 normas, 107 sentencias + 1 PDF de respaldo; 94 MB; HTML/HTM, 15 PDF, 1 DOCX, 1 TXT de OCR).
- `python -m src.corpus.validar` → 186 válidos, 0 errores (1 aviso: Código Civil sin número/año).
- `python -m src.corpus.build` → **186 documentos, 41.382 fragmentos** (23.972 artículos, 15.489 secciones de sentencias, 1.571 notas de vigencia, 350 preámbulos). Mediana 227 palabras por fragmento, máximo 360 ⇒ 10 pasajes ≈ 3.400 tokens típico, ≈ 5.100 peor caso (ventana 8.192).
- **Nivel 1 completo y bien segmentado**: Constitución 446 artículos (con transitorios), Código Civil 2.684, CGP 628, Código de Comercio 2.032, Código Penal 598, CPP 583, CPACA 321, CST 493, CPT 149, ET 1.277, Estatuto del Consumidor 75, Decisión 486 280, Código de Infancia 216. Ninguna norma con 0 o muy pocos artículos. 2.324 artículos largos partidos en partes.
- Decisión 351 de 1993: el extractor de citas del evaluador no la reconoce (solo conoce la Decisión 486); sirve como evidencia, sus citas no puntúan. Limitación del evaluador.
- **Guardia anti-fuga reajustada** (`src/corpus/fuga.py`): la regla anterior bloqueaba la Constitución, el Código Civil y sentencias del seed oficial porque la muestra las cita literalmente (preguntas de "reproducción literal", problema jurídico copiado de la SU-455/2020). Nueva regla: grave solo si un fragmento contiene pregunta y respuesta del mismo ítem, o enunciados de ≥ 3 preguntas distintas (firma de banco), o archivos con formato de banco; lo demás se lista para revisión. Resultado: 0 graves, 1.367 coincidencias menores. Pruebas actualizadas.
- **Autenticidad** (comparación por 8-gramas de cada archivo contra su URL oficial de `fuentes.csv`): **184/186 coinciden al 100 %** en ambas direcciones. SP-1945/2019: el PDF oficial es un escaneo sin texto; el `.txt` es OCR local (errores típicos de OCR, no generado por un modelo) — legítimo. SC-8453/2016: el `.docx` es fiel (142/143 párrafos en el `.doc` oficial, termina en las firmas).
- **Bug corregido en `src/corpus/extraer.py`**: los `.docx` perdían las notas al pie (python-docx no las lee); ahora se extraen de `footnotes.xml`/`endnotes.xml` (SC-8453: +22 notas, 10.137 → 10.590 palabras). Prueba nueva.
- Codificación: 93 `.htm` de la relatoría están en windows-1252 (se ven con � al abrirlos en un editor/navegador que asume UTF-8); el extractor los lee bien. En el corpus procesado solo 4 caracteres dañados en 2 documentos (irrelevante).
- Archivos: `src/corpus/fuga.py`, `src/corpus/extraer.py`, `tests/test_fuga.py`, `tests/test_extraer.py`.
- Siguiente paso: `python -m src.corpus.manifest` e índice (`python -m src.index.build`, en GPU: ~41 mil fragmentos ≈ 8 h en CPU).

## 2026-09-29 — T21 Línea base + T23 RAGAS (Colab, GPU T4)
- Corrida: `notebooks/muestra_en_colab.ipynb` (bge-m3 + reranker en GPU, Qwen3-8B Q4_K_M con llama.cpp CUDA), 50 preguntas, 0 errores de esquema. Resultados en `runs/muestra_colab/`.
- **Puntaje (evaluador oficial):** cerradas 9/15 = 0,600 → **12,00/20** · citas recall ponderado 0,776, **0 citas sin respaldo** (38 aciertos, todos respaldados) → **15,51/20** · abstención 0,779 → **7,79/10** · RAGAS answer correctness **0,4456** (referencia GPT-5.4: 0,451) → **13,37/30** · **total 48,67/80** (35,30/50 sin juez).
- **Tiempos en T4:** recuperación 1,9 s; generación media 33,0 s (p50 27,3; p95 64,6; máx 163) ⇒ **~35 s por pregunta ⇒ 992 ≈ 9,6 h en una T4**: el sábado hacen falta ≥ 2 GPU en paralelo (`--particion`) o acelerar la generación.
- **Análisis:** texto libre: 26/28 recuperan alguna norma del fundamento. MC: en 5 de las 6 falladas la norma de referencia **sí** estaba en los pasajes (58, 128, 528, 647, 748) ⇒ el cuello de botella es el razonamiento/elección, no la recuperación; la 671 es “Doctrina”. Abstenciones: 513 (fundamento en un PDF de la OMPI, fuera del corpus) y 697 (caso Dow Chemical, fuera del corpus) son razonables; **247 se abstuvo porque el modelo no produjo una respuesta utilizable** (probable JSON truncado por `MAX_TOKENS` en abierta) ⇒ revisar.
- Incidentes resueltos en Colab: JAX preinstalado reservaba el 75 % de la VRAM (bm25s lo importa) y Qwen no cabía ⇒ `src/config.py` fuerza JAX/TF a CPU; mensaje de error claro al fallar la carga en GPU; la celda del pipeline imprime el código de salida.
- Siguientes (T22): (1) caso 247 (salida truncada en abiertas); (2) MC: prompt que analice cada opción contra la evidencia y/o modo razonamiento solo en MC si el tiempo lo permite; (3) límite de fragmentos por documento (una sentencia ocupaba 5 de 10 puestos); (4) velocidad de generación.

## 2026-09-30 — T22a Abiertas sin truncar
- Estado: hecho (medición en la muestra pendiente de T22e). Detalle antes/ahora en `docs/CAMBIOS.md` C-01.
- Cómo se verificó: `pytest -q tests/test_llm.py tests/test_citas.py tests/test_abstencion.py` → 31 passed (incluye salida real de Qwen3-8B cortada y rescatada sin reintento).
- Archivos: `src/generation/{llm,contexto,citas,abstencion}.py`, `src/generation/prompts/open_ended.txt`, tests.
- Siguiente paso: T22b tope de 4 fragmentos por documento.

## 2026-09-30 — T22b Tope por documento
- Estado: hecho. Detalle y medición en `docs/CAMBIOS.md` C-02 (recall neutro 87,8 %; acaparamiento 24 → 9 preguntas, todas con mención explícita).
- Verificación: `pytest -q tests/test_hibrido.py tests/test_eval_recuperacion.py` → 10 passed; medición real con `src.eval.recuperacion` (CPU, índice completo).
- Siguiente paso: T22c evidencia por opción en selección múltiple.

## 2026-09-30 — T22c Evidencia por opción en MC (loop detenido a pedido del usuario)
- Estado: hecho (implementado y probado); medición de recuperación en `docs/CAMBIOS.md` C-03: neutra en la norma de referencia (13/15), la 748 aún sin el art. 137 del CPACA; efecto en exactitud pendiente de Colab.
- Loop detenido por el usuario (reunión). Siguiente al relanzar: T22d (secciones de sentencias), luego T22e (una sola ida a Colab).

## 2026-09-30 — Guía de ejecución e índice incremental en Colab
- `docs/COMO_EJECUTAR.md`: paso a paso para el equipo (instalación, configuración, corpus, índice en Colab o local, muestra, evaluación, interfaz, comando único, experimentos en ramas, problemas frecuentes). Enlazada desde `README.md` y `docs/MAPA_DEL_PROYECTO.md`.
- `src/index/paquete_colab.py`: el paquete del índice incluye la caché de embeddings (`--sin-cache` para desactivarla) ⇒ Colab solo calcula fragmentos nuevos o modificados. `notebooks/indice_en_colab.ipynb` reescrito: trae el paquete desde Drive (175 MB), fuerza JAX a CPU, imprime código de salida y guarda el resultado en Drive.

## 2026-09-30 — T22d Detección de secciones (detector + pruebas)
- Estado: hecho. Detalle en `docs/CAMBIOS.md` C-04. `pytest` segmentador 35 passed; corpus 25 passed.
- Siguiente paso: T22e (reconstruir corpus, chequeo automático de secciones, paquete único para Colab).

## 2026-09-30 — T22e Una sola ida a Colab (preparada)
- Corpus reconstruido en local con el detector nuevo: 186 documentos, **41.336 fragmentos** (antes 41.384); guardia anti-fuga sin graves; `corpus_manifest.json` y `CORPUS.md` regenerados.
- Chequeo automático nuevo `python -m src.corpus.secciones [--todas]`: encontró 3 problemas más del detector (subtítulo "7.1. Decisión" en la SU-455, "CONSIDERACIONES DE LA CORTE CONSTITUCIONAL" no reconocido, título "ACLARACIÓN DE / VOTO…" partido en la C-355) ⇒ corregidos. Resultado: las 3 sentencias de control OK; 64 → 26 sentencias con avisos (solo etiquetas faltantes). Detalle y tabla antes/ahora en `docs/CAMBIOS.md` C-04.
- Incidente: el build se caía en la consola de Windows al imprimir "→" antes de la guardia anti-fuga ⇒ `src/config.py` pone la consola en UTF-8 (C-05).
- `src/index/paquete_colab.py --modo muestra`: ya no lleva el índice; lleva código, `data/`, `schema/`, `chunks.jsonl`, caché de embeddings y `_fuga.json`. `dist/paquete_colab_muestra.zip` = 174,9 MB, sin `.env`. 10.496 fragmentos por recalcular (~13 min en T4).
- `notebooks/muestra_en_colab.ipynb`: índice en GPU → ping del decoder → 50 preguntas (`runs/muestra_t22`, no pisa la línea base) → evaluador sin juez y con RAGAS → un zip `muestra_t22.zip` con índice + caché + resultados.
- Pruebas: segmentador + secciones 42 passed; extractor, fuga, config y citas 36 passed.
- Siguiente paso (usuario): commit, subir el zip a Drive y correr el cuaderno. Al volver: registrar puntajes en C-01..C-05, PROGRESO, CORPUS.md §4 y REPORTE_AVANCE.

## 2026-09-30 — Resultados de la corrida T22e en Colab (`runs/muestra_t22`)
- Archivos del cuaderno ubicados: índice (`index.faiss`, manifiesto, `bm25/`) en `build/indice/`, caché en `build/cache/emb/`, resultados en `runs/muestra_t22/`. Verificado: `sha256_chunks` del manifiesto = hash del `chunks.jsonl` local; `src.index.build` → "reutilizado (sin cambios)". Colab calculó 10.496 embeddings en 1.001 s.
- **Puntaje:** cerradas 9/15 → 12,00 (=) · citas 15,10 (−0,41) · abstención 7,67 (−0,12) · RAGAS 0,4208 → 12,62 (−0,75) · **total 47,39/80** (línea base 48,67). 0 errores de esquema, 0 citas sin respaldo. **31,7 s por pregunta** (antes 34,9; p95 61 s, máx 81 s, antes 163 s).
- **Pregunta por pregunta:** MC 748 **arreglada** (D → A, objetivo de C-03), pero la 290 **se dañó** (C → A): con el análisis previo, el modelo citó bien que [P1] fija 4 meses y aun así marcó C como "la contradice" y eligió A. 58, 528, 647 y 671 siguen mal (cambian de letra equivocada). 247 **ya no se abstiene** (C-01): responde y acierta la norma (Ley 472 de 1998). Citas: se pierden la 748 (ahora sin la norma de referencia) y la 879 (cita solo el Código Civil, no el CGP); se gana la 247. Longitud de respuestas abiertas igual (semiabiertas 76 → 77 palabras).
- **RAGAS:** −0,025 sin atribución posible (el reporte no trae puntaje por pregunta). Puede ser ruido del juez: no hay medición de su variabilidad.
- Lectura: C-01 (247) y C-03 (748) hicieron lo que debían en sus casos; el formato "analizar antes de elegir" de C-03 cuesta otro caso (290). Neto: **neutro con leve baja**, dentro de lo que podría ser ruido.

## 2026-09-30 — C-06 Selección múltiple: elegir primero (experimento preparado)
- `MC_ANALISIS_PREVIO=0` por defecto: letra → justificación → descartes, con la evidencia por opción de C-03. Detalle en `docs/CAMBIOS.md` C-06.
- Prueba local en CPU (`runs/mc_elegir_local`): **290 → C y 748 → A, ambas correctas** (con C-03 solo acertaba la 748; en la línea base, solo la 290). ~287 s por MC en CPU.
- `src/eval/combinar.py` (+2 pruebas) y `IDS` en el cuaderno: Colab responde solo las 15 MC; se combinan en local con `runs/muestra_t22` y se evalúan sin juez.
- Paquete `dist/paquete_colab_muestra.zip` regenerado (215,4 MB, sin `.env`). Siguiente: corrida de las 15 MC en Colab.

## 2026-09-30 — Corpus v2: 52 fuentes nuevas
- Revisión de las 59 filas nuevas de `fuentes_v2.csv`: todas de fuentes admitidas por el enunciado §5 (relatorías de la Corte Constitucional, Corte Suprema y Consejo de Estado; normograma DIAN; SIC). Texto extraído revisado en los 18 conceptos DIAN/SIC: documentos oficiales completos, con su número; datos personales anonimizados por la entidad. Sin duplicados (por tipo/número/año ni por bytes).
- Incorporación: 41 archivos copiados de `jurisprudencia_v2/` y `normas_v2/` a sus rutas en `corpus_raw` (sin tocar los existentes; los demás archivos de las carpetas `_v2` son copias de lo que ya había, con `.htm` renombrado a `.html`); 59 filas añadidas tal cual a `fuentes.csv` (respaldo previo en el temporal de la sesión).
- Ajustes acordados con el usuario: número de 13 sentencias CSJ `SP2287-2024` → `SP-2287` (formato que reconoce el evaluador); Resolución DIAN `000165` → `165` (con ceros el evaluador no la reconoce como cita); 7 sentencias del Consejo de Estado (identificadas por radicado, no citables por el evaluador) **apartadas** en `corpus_raw/fuentes_pendientes.csv` con sus archivos en disco.
- Build: 238 documentos (+52), **45.201 fragmentos** (+3.865), guardia anti-fuga sin graves, validador 0 errores. Los 18 conceptos DIAN/SIC y el concepto del Consejo de Estado no son citables por el evaluador (sirven como evidencia). Secciones: 138 sentencias, 35 con avisos (9 nuevas, sobre todo CSJ sin "RESUELVE": etiquetas faltantes, no equivocadas).
- `dist/paquete_colab.zip` (217,5 MB) para `notebooks/indice_en_colab.ipynb`: 3.865 embeddings por calcular (~6 min en T4).
- Corrida completa pedida por el usuario (corpus v2 + C-06): cuaderno de la muestra con `TAG = "muestra_v2"`, `IDS = ""` (50 preguntas + RAGAS); `dist/paquete_colab_muestra.zip` regenerado (217,5 MB, 45.201 fragmentos, sin `.env`). La comparación contra `muestra_t22` mezcla dos cambios (corpus y formato MC); el efecto aislado de C-06 se puede separar después con `IDS` sobre el corpus anterior si hace falta.

## 2026-10-01 — Corrida completa `runs/muestra_v2` (corpus v2 + C-06, Colab T4)
- Ubicación: resultados en `runs/muestra_v2/`. El índice que devolvió es idéntico al local (`sha256_faiss` 8910bf…, misma caché); los archivos BM25 difieren en bytes porque bm25s numera el vocabulario en distinto orden en cada construcción, pero los puntajes son idénticos (50/50 preguntas, diferencia 0, mismo top-50). Carpeta duplicada eliminada.
- **Puntaje: 49,64/80** (mejor hasta ahora; línea base 48,67, t22 47,39): cerradas 9/15 → 12,00 · citas 39 aciertos → 15,92 (0 sin respaldo) · abstención 7,91 · RAGAS 0,4605 → 13,81. 50 respondidas, 0 errores de esquema; 33,4 s por pregunta (p95 44 s, máx 71 s).
- **MC 9/15, pero no las mismas 9:** recupera la 290 (vuelve a C, como en la línea base) y mantiene la 748 (A), pero pierde la 487 (A → D) con **la misma evidencia** que en t22 (10 pasajes idénticos, art. 1820 del Código Civil en P2): la pierde el formato "elegir primero", no el corpus. Cada formato acierta y falla casos distintos ⇒ la elección del modelo en MC es inestable (±1 pregunta).
- **Corpus nuevo:** documentos v2 en la evidencia de 22 de 50 preguntas. Citas: gana la 60 (0/2 → 1/2) y recupera la 879; la 247 pasa de 38 normas citadas a 4.

## 2026-10-01 — Corpus v3: 100 leyes y decretos nuevos
- `corpus_raw/fuentes.csv` llegó dañado por Excel (abierto con `;` como separador): codificación mezclada (190 líneas UTF-8, 156 cp1252), `;`/`;;` añadidos al final y 49 filas partidas en su `;` interno y entre comillas. Reparado deshaciendo exactamente esa transformación (leer cada línea con `;`, volver a unir sus partes con `;`, quitar separadores vacíos): las 186 filas originales coinciden campo por campo con el respaldo. Copia del archivo dañado en el temporal de la sesión.
- Las filas del 30-sep volvieron a su versión de `fuentes_v2.csv`: se reaplicaron los ajustes acordados (13 números CSJ, Resolución DIAN `165`, 7 sentencias del Consejo de Estado apartadas en `fuentes_pendientes.csv`).
- 100 fuentes nuevas (80 leyes, 20 decretos): Función Pública (94), Bogotá Jurídica (3), Colpensiones (2), MinTIC (1); sin duplicados; todas con su número en el encabezado y artículos detectados. Incluye decretos únicos reglamentarios grandes (2555/2010: 3.091 fragmentos; 780/2016: 2.811; 1074/2015: 2.509; 1071/2015: 2.263).
- Build: **338 documentos, 68.603 fragmentos (+23.402)**, validador 0 errores, guardia anti-fuga sin graves. `dist/paquete_colab_muestra.zip` (239,1 MB) con `TAG = "muestra_v3"`: 23.402 embeddings por calcular (~30 min en T4) + 50 preguntas + RAGAS.
- C-07 (MC: consulta por opción = opción + palabras clave raras de la pregunta) implementado; 34 pruebas pasan (incluida generación real). Paquete regenerado: la corrida `muestra_v3` mide juntos corpus v3 + C-07.
- Colab sin GPU ("Cannot connect to GPU backend", probable cuota agotada): `notebooks/muestra_en_kaggle.ipynb`, mismo flujo que el de Colab con Dataset de Kaggle en lugar de Drive, Secrets de Kaggle para la llave, una sola T4 (`CUDA_VISIBLE_DEVICES=0`) y descarga desde Output. Documentado en `docs/COMO_EJECUTAR.md`.
- `src.pipeline.main --rango INICIO FIN` (posiciones 1-based en el archivo, ambos extremos incluidos; valida rangos inválidos) + prueba; variable `RANGO` en los cuadernos de Colab y Kaggle (corrida parcial ⇒ se evalúa en local); runbook del sábado §D con el reparto por rangos. Kaggle: corregido el enlace de descarga (la celda estaba en `proyecto/`).

## 2026-10-01 — Corrida `runs/muestra_v3` (corpus v3 + C-07, Kaggle T4)
- Instalada: índice de Kaggle = fragmentos locales (`sha256_chunks` 8f0ca4…, 68.603; 23.402 embeddings calculados); `src.index.build` → reutilizado. Resultados en `runs/muestra_v3/`.
- **Puntaje: 46,22/80 (peor que v2, 49,64)**: cerradas 9/15 (=) · citas 37 → 15,10 (−0,82) · abstención 7,67 · **RAGAS 0,3815 → 11,45 (−2,36)**. 50 respondidas, 0 errores de esquema, 29,4 s por pregunta.
- MC (C-07): gana la 58 (B → A) y pierde la 748 (A → D): 9/15 de nuevo.
- Documentos v3 en la evidencia de 19 de 35 preguntas de texto libre, casi siempre decretos únicos reglamentarios (1074/2015, 2555/2010, 1069/2015, 1072/2015) y en 1073 hasta 5 de 10 pasajes. Pero las normas de referencia siguen en la evidencia casi igual (v2 44/49, v3 42/49; solo pierde la 1073) ⇒ la caída no es de recuperación de la norma correcta, sino de lo que el modelo escribe con evidencia más ruidosa, o variación del juez (no medida; el reporte no da RAGAS por pregunta).
- Decisión pendiente con el usuario: medir RAGAS por pregunta (v2 vs v3, y v2 dos veces para el ruido del juez) antes de decidir qué hacer con los decretos únicos.
- C-08 (MC: responder en abierto sin opciones y luego elegir; `MC_MODO=abierta`) implementado: 48 pruebas pasan (contexto, pipeline, híbrido, citas, config; incluye generación real con los dos pasos). Paquete regenerado (329,3 MB, 68.603 fragmentos, sin `.env`); cuadernos con `TAG = "mc_abierta"`, `RANGO = "1 15"`. Se evalúa combinando con las 35 de texto libre de `muestra_v3`.

## 2026-10-01 — Resultado C-08 (MC "abierta y luego opción"), `runs/mc_abierta`
- Kaggle T4, 15 MC (`RANGO 1 15`), índice idéntico al local (mismo `sha256_faiss`, 0 embeddings); carpeta duplicada eliminada. Combinada con las 35 de texto libre de `muestra_v3` → `runs/mc_abierta_50`.
- **MC 10/15** (antes siempre 9): gana la 487 sin perder ninguna frente a v3. Sin juez **36,75/50** (v3 34,77; v2 35,83). Con el RAGAS de v3 (11,45, mismas respuestas de texto) el total estimado es 48,20/80. Elegir por similitud del encoder: 4/15 (descartado). 51,9 s por MC.
- Siguiente: decidir corpus (v2 vs v3) con RAGAS por pregunta; combinar C-08 con el corpus que gane.
- MC vuelve a una sola llamada (`MC_MODO=directo`, decisión del usuario: C-08 +1/15 con casi el doble de latencia). C-09 (modo de razonamiento de Qwen3 en MC, tope `MC_RAZONAMIENTO_TOKENS=1024`) implementado; reglas del reto revisadas: no lo prohíben (temperatura 0, determinista; límite práctico ~22 s/pregunta). Prueba local 528 (`runs/c09_local`): JSON válido, razonamiento correcto sobre los umbrales del art. 25 CGP pero sin el valor del SMLMV en la evidencia ⇒ sigue en "mayor"; el razonamiento agotó los 1.024 tokens (en inglés). Paquete regenerado; cuadernos `TAG = "mc_razonamiento"`, `RANGO = "1 15"`.
- Para que el equipo pruebe otros decoders: `/no_think` y el razonamiento C-09 solo se aplican si el modelo es Qwen3 (`LLM.es_qwen3`); celda 4 de los cuadernos con `DECODER_GGUF_REPO`/`DECODER_GGUF_FILE`; `docs/COMO_EJECUTAR.md` §10 (lista blanca, GGUF, licencia ≤ 8B). `src.index.paquete_colab --con-indice` incluye el índice ya construido si corresponde a los fragmentos (zip de 611 MB para compartir por Drive y para que la celda 4 lo reutilice). Guía §4–5 reescritas (compartir índice, `TAG`/`RANGO`/`IDS`, Colab y Kaggle, evaluación de corridas parciales).
- Comando único para las GPUs de Turing: `run.py`/`run.sh` aceptan `--rango INICIO FIN`, `--gpu` (encoder, reranker y decoder en CUDA) e `--indice-existente` (usa el índice de `build/` verificado por sha256, sin reconstruir el corpus; garantiza el mismo índice congelado en todas las máquinas); corrida parcial ⇒ no evalúa y explica cómo unir. Guía §11 (preparar la máquina con CUDA, extraer solo `build/` del zip, ensayo, el comando, reparto en 4 máquinas, unir y validar) y runbook §D actualizados. Sin pruebas corridas (el usuario pide que se le pregunte antes).
- C-10 (máximo 2 pasajes de las 100 fuentes v3, lista en `config/documentos_complementarios.txt`) implementado + prueba (sin correr); `config/` agregado a los paquetes de Colab/Kaggle; cuadernos `TAG = "muestra_v4"` (las 50). Paquete con índice regenerado.
- Verificación (autorizada por el usuario): `python run.py --split sample --indice-existente --rango 1 1 --tag ensayo_local` → índice verificado, 1 respuesta sin errores de esquema, evaluación omitida por ser parcial (432 s en CPU con razonamiento); `pytest tests/test_pipeline.py` → 5 passed. README con las opciones nuevas de `run.py`.
- `pytest tests/test_hibrido.py -k "complementarios or tope_por_documento"` → 2 passed (tope de complementarias con su excepción por mención; tope por documento sin cambios).
- Corregido en los dos cuadernos: el `\n` del `print` de la celda 6 había quedado como salto de línea real (cadena sin cerrar ⇒ SyntaxError en toda la celda). Validada la sintaxis de todas las celdas de código de ambos cuadernos.

## 2026-10-01 — Corrida `runs/muestra_v4` y corrección del diagnóstico de v3
- Instalada (índice y caché idénticos a los locales; carpeta duplicada eliminada).
- **RAGAS 0,1744 no es real:** el juez (z-ai/glm-5.3-flash vía OpenRouter) no devolvió veredicto en **21 de 33** respuestas, y el evaluador las cuenta como cero (el reporte lo avisa). 27 de las 35 respuestas de texto libre son idénticas a v3.
- **Corrección: la caída de v3 tampoco era real.** v3 tuvo 6 sin veredicto (base, t22 y v2: 0). Promedio sobre las respuestas con veredicto: base 0,487 · v2 0,488 · **v3 0,495** · v4 0,509. La conclusión "los decretos únicos empeoran RAGAS" (que motivó C-10) era errónea: no se revisó `n_fallidos` del reporte.
- Deterministas: cerradas **10/15** (C-09 gana 487 y 528, pierde 58) · citas 37 → 34 (pierden 358, 879, una de 253; las MC con razonamiento citan menos normas en la justificación) · abstención 7,67.
- Tiempos: MC 63,3 s por pregunta con razonamiento (v3 ~30 s), semiabiertas 26,7 s, abiertas 48,2 s.
- Pendiente: volver a calificar con RAGAS (solo el juez, sin generar) v3 y v4 cuando OpenRouter responda; decidir C-09 (+1 MC por ~+33 s por MC) y C-10 (motivado por un diagnóstico errado).
- Cuadernos: las celdas de índice, ping, pipeline y evaluación empiezan con `%cd` a la carpeta del proyecto (la celda de descarga deja la sesión en /kaggle/working y reejecutar la de RAGAS fallaba con 'No such file').
- C-11 (abiertas ≤ 200 palabras) en el prompt; cuadernos `TAG = "muestra_v5"` (las 50; igual que v4 salvo C-11). Paquete con índice regenerado. Sin pruebas corridas.
- `paquete_colab` escribe `PAQUETE.txt` (fecha y huella del código) y los cuadernos lo imprimen en la celda 2: la v5 corrió con el paquete viejo (Kaggle ancla la versión del dataset) y salió idéntica a v4 (50/50 respuestas iguales ⇒ reproducibilidad confirmada; RAGAS de las calificadas 0,510, 5 sin veredicto). Cuadernos `TAG = "muestra_v6"`.
- Cuaderno de Kaggle: con varios paquetes en Input usa el más reciente según `PAQUETE.txt` y lista los encontrados (antes tomaba el primero: la corrida usó un dataset viejo `paquete-colab-muestra-v3`).
- `runs/muestra_v6` (paquete 9141cc86a064, verificado): solo cambian las 4 abiertas; no se acortan porque el postproceso agrega "Normas aplicables" (hasta 6) al marco. Juez: 7 de 33 sin veredicto (red); calificadas 0,495. Encontrado y corregido C-12: el filtro de citas corrompía el texto con citas solapadas (679). Prueba agregada, sin correr.
- `pytest tests/test_citas.py` → 11 passed (incluye la de citas solapadas, C-12).
- `src/eval/evaluar.py`: ejecuta `scripts/evaluate.py` sin copiarlo ni modificarlo (runpy, mismos argumentos) y solo le pasa a RAGAS un `run_config` (4 llamadas simultáneas, 600 s por ítem, 10 reintentos). Comprobado: sin `--ragas`, reporte idéntico al oficial sobre `muestra_v6`. La parte con juez no se puede probar en local (sin RAGAS ni llave). Celda 8b en los cuadernos y guía §5.4. Paquete regenerado.
- Cuaderno de Colab: si RUTA_ZIP no existe, usa la copia más reciente de paquete_colab_muestra*.zip en Mi unidad (Drive renombra a '(1).zip'); TAG = "muestra_v7". Patrón detectado: todas las corridas evaluadas en Colab tuvieron 0 fallos del juez y todas las de Kaggle tuvieron fallos (6, 21, 7, 5, 7) ⇒ probable red de Kaggle.
- Colab cambió de imagen (Python 3.13, sin libcudart.so.12): la celda 3c de ambos cuadernos instala las librerías CUDA 12 por pip y fija LD_LIBRARY_PATH si faltan; guía §9 con el síntoma.
- Cuadernos: `%cd` no admite comentario en la misma línea (Colab lo tomaba como parte de la ruta); comentarios movidos a la línea anterior.

## 2026-10-01 — `runs/muestra_v7` (Colab) y corpus v4 (+280 fuentes)
- La corrida de Colab se guardó con TAG `muestra_v6` (cuaderno viejo); instalada como `runs/muestra_v7`. Paquete 16e58ab8a6b5 (incluye C-12). **0 respuestas sin veredicto del juez** ⇒ confirmado: los fallos eran de la red de Kaggle (todas las evaluaciones en Colab: 0; todas en Kaggle: 5–21).
- Respuestas idénticas a la v6 de Kaggle salvo la 679 (C-12): reproducibilidad entre máquinas.
- **Comparación limpia con v2 (ambas con 0 fallos): v2 49,64 vs v7 48,57.** v7 gana cerradas (+1,33, C-09) y pierde citas (39 → 35, −1,63: justificaciones de MC con razonamiento citan menos; C-10) y RAGAS (0,461 → 0,443, −0,53). Decisión sobre C-09/C-10 pendiente.
- `fuentes.csv` llegó otra vez dañado por Excel (codificación mixta, `;` finales, 106 filas entre comillas): reparado con el mismo método (625 filas; los 338 documentos actuales idénticos en título, tipo y URL al manifiesto); reaplicados los ajustes acordados (13 números CSJ, Resolución DIAN 165, 7 sentencias del Consejo de Estado a `fuentes_pendientes.csv`). Las 280 filas nuevas apuntaban a `doctrina/x.html` y `normas/x.html` cuando los archivos están en `doctrina/dian/`, `doctrina/sic/`, `normas/dian/`, `normas/sic/`: rutas corregidas por nombre exacto (único en disco). Validador: 618 documentos, 0 errores.
- 280 fuentes nuevas: 243 conceptos (DIAN, SIC, Supersociedades), 26 resoluciones, 11 circulares; normograma DIAN 192, Supersociedades 58, SIC 29, Bogotá Jurídica 1. Sin duplicados por contenido; texto real (los "404" eran el Decreto 4048 de 2008). ~1,46 millones de palabras.
- Build corpus v4: **618 documentos, 75.204 fragmentos (+6.601)**, guardia anti-fuga sin graves, secciones OK, manifiesto y CORPUS.md regenerados. No citables: 262 conceptos (esperado) y las 5 partes de la Circular Única de la SIC (sin número; es la Circular Externa 10 de 2001: decisión del equipo). Resoluciones y demás circulares, citables.
- `dist/paquete_colab.zip` (331,8 MB, 6.600 embeddings por calcular) para `notebooks/indice_en_colab.ipynb`, que ahora busca el zip en Drive si cambió de nombre e imprime `PAQUETE.txt`. Las 280 fuentes nuevas no están en `config/documentos_complementarios.txt` (son principales).
- Circular Única de la SIC (5 títulos): `numero=10`, `anio=2001` (es la Circular Externa 10 de 2001) ⇒ citable; encabezado "… (Circular 10 de 2001)". Corpus reconstruido (618 documentos, 75.204 fragmentos). Tope de complementarias sin cambios (decisión del usuario: probar primero el corpus solo). `dist/paquete_colab_muestra.zip` sin índice (el cuaderno lo construye: ~7.000 embeddings), cuadernos `TAG = "muestra_v8"`. Se retira `dist/paquete_colab.zip` (quedaba con la circular sin número).

## 2026-10-02 — `runs/muestra_v8` (corpus v4, Kaggle)
- Índice de Kaggle = fragmentos locales (`sha256_chunks` e8f893…, 75.204; 6.600 embeddings en 561 s); instalado en `build/indice/` y `build/cache/emb/`; `src.index.build` → reutilizado.
- **46,80/80** (v7, mismo sistema con el corpus anterior: 48,57): cerradas 9/15 (gana 58 → C? no: 58 B→C sigue mal; pierde 528 C→D) · citas 35 (= v7; gana 1073, pierde 247) · abstención 7,44 (247 ya no trae su norma) · RAGAS 0,4357 con 1 sin veredicto (calificadas 0,4765 vs 0,4696 de v7).
- El razonamiento en MC (C-09) sigue activo: 15/15 con razonamiento. Con corpus v4 vuelve a 9/15 (la 528 que ganaba se pierde): ganancia inestable.
- `dist/paquete_colab_muestra.zip` con `--con-indice` (666,5 MB, índice + caché + fragmentos) para compartir por OneDrive.
- C-09 y C-10 apagados por defecto (decisión del usuario); cuadernos `TAG = "muestra_v9"`; paquete con índice regenerado.
- C-13 (sin abstención por baja pertinencia en texto libre) + pruebas de abstención actualizadas (sin correr). Paquete v9 regenerado: C-09 off, C-10 off, C-13 on.
- C-14 (cupo de 4 normas entre los 10) implementado + prueba (sin correr). v9 = corpus v4 + C-09 off + C-10 off + C-13 + C-14. Paquete regenerado.
- Resultado v9 registrado (citas 38, sin juez 35,18). C-15: decoder Gemma 4 E4B (ggml-org GGUF Q8_0; Apache-2.0; 7.996.156.490 parámetros; gemma4 soportado por la llama.cpp instalada). El .env local del usuario aún fija Qwen (no se toca: contiene la llave). Cuadernos TAG muestra_v10. Paquete regenerado.
- Prueba local de Gemma 4 E4B (Q8_0, CPU, `runs/gemma_local`, pregunta 748, con autorización): carga y plantilla de chat OK, JSON válido, respuesta en español, 209 s (160 s de generación, 277 tokens). Eligió D (correcta A), como Qwen. La evidencia ya traía 8 normas (el cupo de C-14 no cambia nada aquí), pero no el art. 137 del CPACA: la búsqueda no lo encuentra entre los candidatos.
- `notebooks/muestra_en_colab_sin_juez.ipynb`: copia del cuaderno de Colab sin las celdas del juez (llave, RAGAS y RAGAS espaciado), para el compañero; conserva la evaluación oficial sin juez. TAG muestra_v10.
- A pedido del usuario: eliminados `notebooks/muestra_en_colab_sin_juez.ipynb`, la celda 8b (juez espaciado) de los cuadernos y `src/eval/evaluar.py`; solo se usa `scripts/evaluate.py`. Guía §5.4 ajustada.
- muestra_v10 (Gemma 4 E4B, Colab, juez sin fallos): 48,59/80 (cerradas 9/15 12,00 · citas 39 15,92 · abstención 7,67 · RAGAS 0,4335 13,00); 39 s por pregunta en T4; normas de referencia en la evidencia 44/49. Informe técnico actualizado con el sistema actual y exportado a informe/INFORME_TECNICO.pdf (2 páginas; faltan nombres). README: decoder Gemma y puntajes. Zip oficial de corpus e índice con src.corpus.empaquetar.
- Integrantes en informe, reporte y README. Reporte de avance actualizado al 2-oct (mejor 49,64 y actual 48,59; 618 documentos; Gemma) y exportado a docs/REPORTE_AVANCE.pdf (1 página); informe PDF regenerado (2 páginas). Falta el nombre del equipo.
- Nombre del equipo: Los PoliTICos (reporte, informe, README); PDF regenerados.
- C-16: revertido C-11 (el análisis de 3–4 oraciones incumplía el mínimo de 5 del enunciado; no hay tope de palabras para abiertas). Cuadernos TAG muestra_v11; paquete con índice regenerado.
- C-17 (prompt MC flexible + sistema propio de MC) para la v11 junto con C-16. Paquete regenerado.
- C-17 ajustado: sin regla de conocimiento propio ni sistema propio de MC; la elección sale solo de la evidencia. Paquete regenerado.
- Regla 2 de C-17 = preferir la opción más completa no contradicha por la evidencia (pedido del usuario). Paquete regenerado.
- Corpus v5 (2026-10-02): 11 documentos oficiales nuevos, ubicados y verificados por un agente y descargados con autorización del usuario: Ley 1473 de 2011 (versión del Senado, 17 artículos; la de Función Pública llegaba solo al art. 5), Ley 1692 de 2013 (el listado decía "2017"), sentencias C-468/24, SU-016/20 y SU-277/25 (citadas en la muestra), decretos del salario mínimo de 2023 a 2025 (2613/2022, 2292/2023, 1572/2024) y resoluciones DIAN de la UVT de 2024 a 2026 (187/2023, 193/2024, 238/2025). Ya estaban (erratas del listado): Ley 1563/2012, Ley 964/2005, Res. DIAN 1264/2022. Decreto 46 de 2024 → número `046` (como lo cita el listado). Excluidos por decisión del usuario: Decreto 2737/1989, Acuerdo 02/2015, T-488/11 y los no verificables.
- Build: 629 documentos, 75.910 fragmentos (730 embeddings nuevos), anti-fuga sin graves, todos los nuevos citables; brechas: seed 544/559, muestra 0 faltantes. Paquete de muestra sin índice (lo construye el cuaderno). El índice local queda desactualizado hasta recibir el zip de Colab.
- Configuración de Pablo (configuracionPablo11de15/): mismo código salvo formateador de chat de Gemma 4 sin razonamiento (llm.py), Gemma Q4_0, tope de 2 complementarias, sin cupo de normas, prompt MC original y umbral de abstención 0,05; corpus de 338 documentos. Su paquete no trae resultados (es la entrada). Incorporado su formateador (C-18), adaptado para activarse por arquitectura `gemma4`; se mantiene Q8_0.
- Ampliación de Pablo: 21 documentos nuevos verificados (número y año en el texto, articulado, sha igual a su nota, sin duplicados): 15 leyes de convenios tributarios (Cancillería), decretos del salario mínimo 2026 (1469/2025, suspendido provisionalmente, y 159/2026 transitorio) y auxilio de transporte 2023–2026. Ya estaban 8; excluidos Decreto 875/2008 y 2737/1989 (decisión del usuario). Validador: 650 documentos.
- Corpus v6: 650 documentos, 77.014 fragmentos; anti-fuga sin graves; los 21 nuevos citables; muestra sin normas faltantes. Paquete 11:56, huella 4c1a571382e6 (C-16, C-17, C-18, corpus v6), sin índice.
- `runs/muestra_v11` (paquete de las 10:05: C-16 + C-17, Gemma Q8 sin formateador, corpus 618): 49,58/80, MC 10/15 (gana 528, sin pérdidas), citas 38, RAGAS 0,4276, juez sin fallos. Índice de esa corrida no instalado (más viejo que los fragmentos locales). Siguiente: correr el paquete de las 11:56 (huella 4c1a571382e6: + formateador de Gemma C-18 y corpus de 650).

## 2026-10-02 — `runs/muestra_v12` (paquete 11:56: C-16, C-17, C-18, corpus de 650) — NUEVO MEJOR
- **53,09/80** (antes 49,64), juez sin fallos: cerradas **11/15** (14,67; gana la 748) · citas 40 (16,33; recall 0,816) · abstención 8,37 · RAGAS 0,4572 (13,72). Normas de referencia en la evidencia 46/49. 40 s por pregunta en T4 (MC 40, semiabiertas 34, abiertas 76).
- Índice de Colab = fragmentos locales (77.014; 1.834 embeddings nuevos); instalado y verificado (reutilizado).
- Actualizados con v12: informe técnico (PDF de 3 páginas), README, reporte de avance (PDF de 1 página). Zip oficial de corpus e índice regenerado con `src.corpus.empaquetar` (sha nuevo para el README y .env).
- CORPUS.md definitivo (criterio, descartes, problemas y lectura de la curva; tabla de evolución con 618 y 650 documentos y la corrección de la caída de RAGAS de v3). README: limitaciones completas. Pendiente: enlace público del zip del corpus.
- `src.corpus.empaquetar` incluye `fuentes.csv` en el zip publicable. `dist/corpus_equipo.zip` regenerado: 368,5 MB, sha256 47313ac08a2687406bdeb7e9684f6c08eb087739004bbf78cd6ae2d7a4b393a9; estructura validada con `src.corpus.nube.validar_zip`.
- README, sección Corpus e índice: enlace a la carpeta de OneDrive indicada por el usuario (contiene corpus_equipo.zip), 368,5 MB, sha 47313ac0…, vigencia hasta el 2-nov-2026. Advertido: el enlace exige iniciar sesión (redirige a login.microsoftonline.com) y es de carpeta; el usuario gestionará el acceso del jurado.
- Reporte de avance: agregado el enlace del repositorio (https://github.com/juan-jose-cortes1234/AIWeekHackaton); PDF de 1 página regenerado.
- C-19 (abstención por evidencia insuficiente, umbral 0,025; corrige C-13 frente al requisito mínimo del Paso 4) y C-20 (tope de 500 palabras en abiertas). Reporte de avance con los 4 ajustes de la revisión externa (abstención, RAGAS matizado, plan de 6 equipos con riesgos, preguntas 58 y 128 como posibles inconsistencias) en 1 página; informe (3 págs.) y README actualizados. Paquete con índice regenerado.
- Informe y reporte: resultados presentados como del sistema de entrega (umbral 0,025), respaldado por la verificación sobre las trazas de v12 (ninguna respuesta cambia). PDF: reporte 1 pág., informe 3 págs.
