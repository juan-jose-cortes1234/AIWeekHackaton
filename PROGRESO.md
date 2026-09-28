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
