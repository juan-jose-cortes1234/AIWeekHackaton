# Los PoliTICos — Hackathon 2026

**Integrantes:** Juan José Cortés Villamil · Pablo Medina Forero · Miguel Santiago Roa Vallejo
**Universidad de los Andes** — AI Week 2026

Sistema de respuesta a preguntas de derecho colombiano con un modelo abierto de
tamaño reducido y un corpus jurídico propio. Cada respuesta se fundamenta en
pasajes recuperados del corpus; toda norma citada figura en esos pasajes.

## Corpus e índice

<!-- OBLIGATORIO. El jurado descarga desde aquí. Verificar el enlace desde una
     sesión privada del navegador antes de las 15:00. -->

| Recurso | Enlace | Tamaño | Licencia |
|---|---|---|---|
| Corpus procesado e índice vectorial | `<URL pública del zip>` | `<tamaño>` | CC-BY-4.0 |

- sha256 del zip: `<CORPUS_ZIP_SHA256>`
- El comprimido contiene `LICENSE`, `corpus_manifest.json`, `corpus/` con los
  documentos procesados (un `.txt` por norma, fragmentos con encabezado canónico)
  e `indice/` con el índice FAISS, el índice BM25, `chunks.jsonl` (fragmentos con
  `doc_id`, offsets y metadatos) e `index_manifest.json` (modelo, dimensión y hashes).
- El enlace permanece activo hasta el `<fecha, treinta días después del evento>`.
- Bitácora del corpus: [`CORPUS.md`](CORPUS.md) · manifiesto: [`corpus_manifest.json`](corpus_manifest.json).

## Reproducción

> Guía paso a paso para el equipo (instalación, corpus, índice en Colab, muestra, experimentos): [`docs/COMO_EJECUTAR.md`](docs/COMO_EJECUTAR.md).

Un único comando descarga el corpus e índice publicados (o los reconstruye desde
el corpus crudo), genera las respuestas y las califica con el evaluador oficial.

```bash
cp .env.example .env        # completar CORPUS_ZIP_URL y CORPUS_ZIP_SHA256
bash run.sh                 # equivalente: python run.py --split sample
```

En contenedor limpio:

```bash
docker build -t hackathon-rag .
docker run --rm --env-file .env -v hf-cache:/root/.cache/huggingface hackathon-rag
```

`run.sh` / `run.py` ejecuta, en orden:

1. Instala las dependencias si faltan (`requirements.txt`).
2. Obtiene corpus e índice: con `CORPUS_ZIP_URL` descarga el zip publicado,
   verifica su sha256 y valida la estructura (`python -m src.corpus.nube`); sin él,
   construye desde `CORPUS_RAW_DIR` (validación de `fuentes.csv`, extracción,
   segmentación, guardia anti-fuga, manifiesto e índice).
3. Corre el pipeline sobre las preguntas de muestra (`python -m src.pipeline.main`).
4. Califica con `scripts/evaluate.py` (con `--ragas` si hay `OPENROUTER_API_KEY`
   y `pip install -r scripts/requirements-evaluador.txt`).

Opciones útiles: `--limite N` (solo N preguntas), `--rango INICIO FIN` (preguntas en esas
posiciones, para repartir entre máquinas), `--gpu` (todo en CUDA), `--indice-existente` (usar el
índice ya descomprimido en `build/`, verificado por sha256, sin reconstruir), `--tag NOMBRE`,
`--sin-ragas`, `--no-cache`, `--split test` (entrega final). Ejemplo en una GPU:
`python run.py --split test --gpu --indice-existente --rango 1 248 --tag sabado_1`
(detalle en [`docs/COMO_EJECUTAR.md`](docs/COMO_EJECUTAR.md) §11).

**Requisitos de hardware.**

- **Memoria: ≥ 12 GB de RAM** disponibles para el proceso o el contenedor (encoder,
  reranker y decoder cargados a la vez ≈ 10 GB). En Docker Desktop sobre Windows,
  el límite por defecto de WSL2 puede ser menor: se ajusta con `memory=12GB` en
  `%USERPROFILE%\.wslconfig` y `wsl --shutdown`.
- **Disco:** ~2,4 GB de imagen + ~12 GB de modelos de Hugging Face (montar la caché
  como volumen para no descargarlos en cada ejecución).
- **Tiempo en CPU** (medido en Ryzen 7 8840HS, 16 hilos): ~150 s por pregunta
  directamente en Python y ~250 s dentro de Docker (dominado por la lectura del
  prompt en el decoder). Las 50 preguntas de muestra tardan ~3,5 h en un contenedor
  solo con CPU; con GPU T4, ~39 s por pregunta.
- La ejecución de las 992 preguntas se hace en GPU: backend `transformers`
  (`DECODER_BACKEND=transformers`, `DECODER_DEVICE=cuda`) o llama.cpp con CUDA.

Python ≥ 3.10 (probado con 3.11).

**Tiempo estimado sobre las 50 preguntas de muestra:** ~33 min en una GPU T4 (39 s por pregunta, corrida `muestra_v10`).

### Comandos por etapa

| Etapa | Comando |
|---|---|
| Validar el corpus crudo | `python -m src.corpus.validar` |
| Construir corpus procesado (+ anti-fuga) | `python -m src.corpus.build` |
| Manifiesto y tablas de `CORPUS.md` | `python -m src.corpus.manifest` |
| Índice FAISS + BM25 | `python -m src.index.build` |
| Corpus e índice desde la nube | `python -m src.corpus.nube` |
| Probar la recuperación | `python -m src.retrieval.buscar "pregunta" --area laboral` |
| Calidad de recuperación sobre la muestra | `python -m src.eval.recuperacion` |
| Normas que faltan en el corpus | `python -m src.eval.brechas` → `docs/BRECHAS.md` |
| Probar el decoder | `python -m src.generation.ping` |
| Generar respuestas | `python -m src.pipeline.main --split sample` |
| Entrega final | `python -m src.pipeline.main --split test --out submissions.jsonl` |
| Pruebas | `python -m pytest -q` |

## Arquitectura

```
pregunta ──► router de citas explícitas ─┐
          ├► BM25 (tokenizador jurídico) ─┼─► fusión RRF ─► reranker ─► top-10 pasajes
          └► denso (bge-m3 + FAISS) ──────┘   (+ área)     (bge-v2-m3)       │
                                                                             ▼
   submissions.jsonl ◄── abstención ◄── filtro de citas ◄── Gemma 4 E4B (JSON forzado, T=0)
```

| Componente | Elección | Motivo |
|---|---|---|
| Encoder | `BAAI/bge-m3` (MIT), 1.024 dim, 512 tokens | Multilingüe, fuerte en español; licencia abierta |
| Decoder | `google/gemma-4-E4B-it` (Apache-2.0, 7.996.156.490 parámetros), GGUF Q8_0 con llama.cpp; sin modo de razonamiento | ≤ 8B; en la muestra igualó a Qwen3-8B (versión anterior, sigue en la lista blanca) con mejores citas |
| Segmentación | Un fragmento por artículo (≤ 300 palabras; los largos se parten repitiendo el encabezado); sentencias por secciones en ventanas de ~300 palabras | El artículo es la unidad de sentido (enunciado B.2) |
| Trazabilidad | Cada fragmento empieza con el nombre canónico de su norma (“Ley 1150 de 2007, artículo 11.”), verificado con el extractor de citas del evaluador | Sin eso las citas no cuentan como respaldadas |
| Recuperación | Router de artículos citados en la pregunta + BM25 + denso con RRF, sesgo por área, diversidad por artículo; en MC, cada opción como consulta adicional | Los embeddings confunden números de artículo; BM25 no (B.3) |
| Reordenamiento | `BAAI/bge-reranker-v2-m3` (Apache-2.0) sobre los 20 mejores | Precisión del cross-encoder sobre candidatos |
| Citas | Post-filtro determinista con las expresiones del evaluador: se eliminan las citas no presentes en los 10 pasajes; referencias renderizadas desde los metadatos de los pasajes | Cero citas sin respaldo; reproducible en la verificación en vivo |
| Mecanismo de abstención | Nunca en selección múltiple; en texto libre solo sin evidencia pertinente (reranker bajo el umbral y sin artículo citado) o sin respuesta utilizable | Con los pesos oficiales, abstenerse casi nunca conviene |
| Determinismo | Temperatura 0, semilla fija, desempates por id, índice congelado por sha256 | Verificación en vivo |

Solo se admiten modelos de licencia abierta: `src/config.py` mantiene una lista
blanca (`MODELOS_ABIERTOS`) y el sistema se niega a arrancar con cualquier otro.
Todo corre en proceso con pesos de Hugging Face; no hay llamadas a APIs de modelos.
La llave de OpenRouter la usa exclusivamente el evaluador oficial (juez de RAGAS).

### Estructura del repositorio

```
src/corpus/       ingesta: fuentes.csv → texto → artículos → fragmentos; anti-fuga; manifiesto; nube
src/index/        encoder, FAISS, BM25
src/retrieval/    recuperador híbrido y reranker
src/generation/   decoder, prompts, filtro de citas, abstención
src/pipeline/     preguntas → submissions.jsonl
src/eval/         métricas de recuperación y brechas del corpus
interfaz/         interfaz gráfica (FastAPI + HTML)
scripts/ data/ schema/   material oficial (evaluador, muestra, esquema)
tests/            pruebas con los modelos reales
```

## Resultados sobre las preguntas de muestra

| Componente | Puntos | Posibles |
|---|---:|---:|
| Exactitud en cerradas | 12,00 | 20 |
| Corrección en texto libre (RAGAS) | 13,00 | 30 |
| Calidad de citación | 15,92 | 20 |
| Abstención calibrada | 7,67 | 10 |
| **Total automático** | **48,59** | **80** |

Evolución del puntaje según el corpus: ver [`CORPUS.md`](CORPUS.md) §4.

## Interfaz gráfica

```bash
python -m interfaz.app          # http://localhost:8000
```

Permite formular una pregunta (semiabierta, abierta o de selección múltiple con
sus opciones), muestra primero la evidencia recuperada y luego la respuesta, con
cada norma citada marcada como respaldada (enlazada al pasaje) o sin respaldo, y
los pasajes con su pertinencia, origen y enlace a la fuente. Diseño inspirado en
la identidad visual de Software Colombia.

## Limitaciones conocidas

1. **Hardware:** en CPU una respuesta tarda ~2,5 minutos; la ejecución completa
   requiere GPU.
2. **Cobertura del corpus:** una norma ausente del corpus no se puede citar con
   respaldo; `docs/BRECHAS.md` lista las faltantes conocidas. `<completar>`
3. **Segmentación:** el corte por artículo depende del formato de la fuente
   (HTML del Senado, SUIN, PDF); documentos escaneados requieren OCR.
4. **Citas a nivel de cuerpo:** el filtro garantiza que toda norma citada esté en
   la evidencia, no que el artículo específico sea el pertinente.
5. `<completar con lo observado en la muestra>`

## Uso de herramientas de IA en el desarrollo

El código se desarrolló con apoyo de un asistente de programación. Ningún modelo
cerrado forma parte del sistema: no genera respuestas, no reformula consultas, no
reordena resultados ni produjo contenido del corpus.

## Licencia

Código bajo Apache-2.0 ([`LICENSE`](LICENSE)). Corpus procesado bajo CC-BY-4.0
(los textos normativos colombianos son de dominio público).
