# Arquitectura — diseño técnico

Documento de referencia para el loop. Las decisiones marcadas **(medir)** son
hipótesis: se confirman o se descartan con el evaluador sobre la muestra y el
resultado se anota en `docs/EXPERIMENTOS.md`.

## 1. Estructura del repositorio

```
HackathonAIWeek/                  ← raíz del repo (git lo maneja el usuario)
├── CLAUDE.md  LOOP.md  PLAN.md  PROGRESO.md  GUIA_CORPUS.md
├── README.md  LICENSE  CORPUS.md  corpus_manifest.json   (entregables)
├── .env (NO versionado)  .env.example  .gitignore
├── requirements.txt  Dockerfile  run.sh  run.py
├── data/  schema/  scripts/      ← copia del material oficial (evaluate.py busca data/ junto a scripts/)
├── src/
│   ├── config.py                 ← única fuente de configuración (.env)
│   ├── corpus/                   ← fuentes.csv → texto limpio → artículos → chunks
│   ├── index/                    ← encoder, FAISS, BM25, manifest/hash
│   ├── retrieval/                ← híbrido, router de citas, reranker
│   ├── generation/               ← cliente decoder, prompts, parseo JSON, post-filtro de citas
│   ├── pipeline/                 ← main: preguntas → submissions.jsonl
│   └── eval/                     ← métricas de recuperación, reporte de brechas, wrappers de evaluate.py
├── interfaz/                     ← GUI (identidad visual Software Colombia)
├── tests/  (fixtures con texto marcado "TEXTO DE PRUEBA", nunca contenido real inventado)
├── docs/  ARQUITECTURA.md  EXPERIMENTOS.md  RUNBOOK_SABADO.md  INFORME_TECNICO.md
├── build/  (ignorado)  corpus/<doc_id>.txt  indice/{index.faiss,bm25/,chunks.jsonl,index_manifest.json}
└── runs/   (ignorado)  <fecha>_<tag>/{submissions.jsonl, trazas.jsonl, reporte.json}
```

### 1.1 De dónde sale el corpus: dos modos

| Modo | Cuándo | Fuente | Qué hace |
|---|---|---|---|
| **nube** (por defecto en `run.sh`, Docker y el sábado) | reproducción, jurado, verificación en vivo | `CORPUS_ZIP_URL` | descarga el zip oficial, verifica `CORPUS_ZIP_SHA256`, lo descomprime en `build/` y usa el índice tal cual. **No reindexa.** |
| **local** (solo desarrollo) | mientras el equipo construye el corpus | `CORPUS_RAW_DIR` + `fuentes.csv` | ingesta → índice → genera `dist/corpus_<equipo>.zip`, que el equipo sube a la nube |

Flujo: el equipo arma el corpus crudo → modo local produce el zip → el equipo lo
sube (Drive/OneDrive/Dropbox/Zenodo) → pega el enlace en `.env` (`CORPUS_ZIP_URL`)
y el hash que imprimió el empaquetador (`CORPUS_ZIP_SHA256`) → desde ahí todo
consume **solo** la nube. Conectarlo = llenar esas dos variables; nada de código.

Reglas del módulo `src/corpus/nube.py`:
- `CORPUS_SOURCE=auto|nube|local`. `auto`: usa la nube si `CORPUS_ZIP_URL` tiene
  valor; si no, local; si no hay ninguno, error claro que explica cómo configurarlo.
- Acepta enlaces de compartir y los convierte a descarga directa: Google Drive
  (`/file/d/<id>/` → descarga con confirmación para archivos grandes, p. ej. `gdown`),
  OneDrive/SharePoint (añadir `download=1`), Dropbox (`dl=1`), Zenodo y URL directas.
- Descarga en streaming con reanudación y barra de progreso; caché en
  `build/descargas/`; si el zip ya está y el sha256 coincide, no descarga de nuevo.
- Si el sha256 no coincide: error y no se usa (el índice del sábado está congelado).
- Valida la estructura oficial del zip (`LICENSE`, `corpus_manifest.json`,
  `corpus/`, `indice/index.faiss`, `indice/chunks.jsonl`, `index_manifest.json`) y que
  `index_manifest.json` declare el mismo encoder que `.env`; si no, error.
- Prueba sin red: un zip de fixture servido desde un servidor HTTP local en la prueba.

`CORPUS_RAW_DIR` (en `.env`) apunta a la carpeta donde el equipo deja los
documentos crudos — puede ser una carpeta sincronizada de OneDrive. Ver `GUIA_CORPUS.md`.

## 2. Ingesta (paso 1 del enunciado)

Entrada: `CORPUS_RAW_DIR/fuentes.csv` + archivos crudos (`.html/.htm`, `.pdf`, `.docx`, `.txt`).

1. **Validar** `fuentes.csv` (acepta `,` o `;`; UTF-8 o UTF-8-BOM): `doc_id` único
   y en formato `snake_case`, archivo existente, `tipo` válido, `url` presente,
   `areas` ⊂ las 10 áreas oficiales (`scripts/common.py::AREAS`, admitir slugs).
2. **Extraer texto**: HTML con `selectolax`/`BeautifulSoup` (detectar encoding
   `windows-1252`/`latin-1` de la Secretaría del Senado; unir páginas `_pr001…`
   si vienen en varios archivos); PDF con `pymupdf` y OCR (`pytesseract`) solo si
   la página no tiene capa de texto; DOCX con `python-docx`.
3. **Normalizar**: NFC, espacios, guiones partidos, quitar menús/pies de página,
   conservar tildes (el evaluador las normaliza por su cuenta).
4. **Segmentar**:
   - Normas: por **artículo** (regex tolerante: `ART[IÍ]CULO\s+\d+[A-Z]?(o|°|º)?\.?`,
     `ART\.`, `bis`, transitorios, parágrafos dentro del artículo). Artículos
     muy largos (> ~450 tokens del encoder) se parten en sub-fragmentos que
     **repiten el encabezado**. Notas de vigencia/jurisprudencia del Senado:
     fragmento aparte, tipo `nota`, ligado al artículo.
   - Sentencias: por secciones (antecedentes, problema jurídico, consideraciones,
     decisión/RESUELVE) y dentro de ellas ventanas de ~300 palabras con 15 % de
     solape; el `RESUELVE` y la síntesis siempre como fragmentos propios.
5. **Encabezado canónico** (lo más importante del pipeline): cada fragmento
   empieza con el nombre de su norma en una forma que `citations.extract`
   reconoce, p. ej.:
   - `Constitución Política de Colombia, artículo 88.`
   - `Código General del Proceso (Ley 1564 de 2012), artículo 6.`
   - `Código Civil, artículo 1820.` / `Estatuto Tributario (Decreto 624 de 1989), artículo 240.`
   - `Ley 1150 de 2007, artículo 11.` / `Decreto 2153 de 1992, artículo 45.`
   - `Decisión 486 de la Comisión de la Comunidad Andina, artículo 134.`
   - `Sentencia C-355 de 2006 de la Corte Constitucional. [Consideraciones]`
   **Prueba obligatoria**: para el 100 % de los fragmentos,
   `citations.bodies(citations.extract(texto))` contiene el cuerpo esperado del
   documento. Si un `tipo` no produce un cuerpo reconocible, se reporta.
6. **Escribir** `build/corpus/<doc_id>.txt` (bloques en orden, cada uno con su
   encabezado, separados por línea en blanco) y `build/indice/chunks.jsonl`
   con: `chunk_id, doc_id, inicio, fin, texto, tipo_norma, numero, anio, articulo,
   organo, vigencia, areas, seccion, cuerpo_canonico`. `texto == corpus[inicio:fin]`
   (prueba de literalidad).
7. **Manifiesto**: `corpus_manifest.json` (campos del ejemplo oficial + `sha256`,
   `n_articulos`, `n_fragmentos`) y regeneración automática de las tablas de
   `CORPUS.md` (inventario, totales, cobertura por área).

## 3. Indexación (paso 2)

- Encoder `ENCODER_MODEL` vía `sentence-transformers`; vectores normalizados;
  prefijos `query:`/`passage:` si el modelo es E5; truncado a `ENCODER_MAX_LENGTH`.
- FAISS `IndexFlatIP` (exacto). IDs = posición en `chunks.jsonl`.
- BM25 (`bm25s`) con tokenizador español: minúsculas, sin tildes, stopwords,
  **conservar números** y tokens tipo `c-355`, `1150`, `art`.
- `index_manifest.json`: modelo, dimensión, n° fragmentos, sha256 de
  `chunks.jsonl` y de `index.faiss`, fecha. `build_index` es idempotente: si el
  hash del corpus no cambió, no recalcula (el embedding en CPU es caro).
- Caché de embeddings por `sha256(texto)` para no recalcular al añadir documentos.

## 4. Recuperación

Por pregunta (y por opción en MC):

1. **Router de citas explícitas**: si la pregunta menciona una norma
   (`citations.extract` sobre la pregunta + regex de “artículo N del …”),
   se recuperan directamente esos artículos por metadatos (puntaje máximo).
2. **Híbrido**: top-50 denso + top-50 BM25 → fusión RRF (k=60) con pesos (medir).
3. **Sesgo por área**: la pregunta trae `area`; ligero boost a documentos cuya
   lista `areas` la contiene (medir; no filtrar duro).
4. **Reranker** `bge-reranker-v2-m3` sobre los 30–40 mejores (medir costo/beneficio en CPU y GPU).
5. **Diversidad**: máximo 3 fragmentos del mismo artículo; se prefieren
   fragmentos de cuerpos distintos para ampliar el respaldo.
6. Resultado final: top-10 ordenados → `pasajes_recuperados` (con `inicio`,
   `fin`, `score` redondeado a 4 decimales). Desempates por `chunk_id`.
7. **Segunda pasada** solo si la evidencia es débil (score máximo bajo o ningún
   cuerpo del área): reformulación **determinista** (plantillas + nombre del
   cuerpo normativo probable según el área) — nada de LLM cerrado. Opcional:
   reformulación con el mismo decoder abierto si el presupuesto de tiempo lo permite.

## 5. Generación (paso 3)

- Cliente único `generation/llm.py`, **todo en proceso y con pesos de Hugging
  Face**; no hay APIs, servidores HTTP ni proveedores externos (decisión del
  equipo: ningún camino de configuración puede terminar en un modelo cerrado):
  - `llamacpp`: `llama-cpp-python` con el GGUF oficial `Qwen/Qwen3-8B-GGUF`
    (`Qwen3-8B-Q4_K_M.gguf`, ~5 GB), descargado con `huggingface_hub`. Corre en
    CPU (portátil, contenedor limpio) y en GPU si la rueda tiene CUDA.
  - `transformers`: `Qwen/Qwen3-8B` con transformers (bf16 ~16 GB: requiere GPU;
    en el portátil de 15 GB no cabe). Backend para la sala Turing / Colab.
  - Ambos deben producir la misma salida estructurada; la elección final se fija
    antes del sábado y no se cambia después de generar la entrega.
- **Lista blanca** (`src/config.py::MODELOS_ABIERTOS`): `validar_final()` rechaza
  cualquier decoder, encoder o reranker que no esté en ella.
- Parámetros fijos: `temperature=0`, `top_p=1`, `seed=DECODER_SEED`,
  `max_tokens` por formato, contexto fijo. Qwen3: **modo sin razonamiento**
  (`enable_thinking=False` / `/no_think`) salvo que un experimento demuestre
  ganancia dentro del presupuesto de tiempo.
- Salida JSON forzada (JSON schema / gramática del backend) + parser tolerante
  + un reintento con mensaje de corrección.
- Caché de generaciones en `build/cache/gen/` con clave
  `sha256(modelo+prompt+parámetros)`; bandera `--no-cache` para la verificación en vivo.
- Prompts en español en `src/generation/prompts/` (archivos de texto, versionados):
  - Evidencia numerada `[P1]…[P10]`, cada una con su encabezado de norma.
  - Instrucción: responder **solo** con la evidencia; citar siempre como
    “artículo N de la Ley X de AAAA” / “artículo N del Código …”; si la
    evidencia no alcanza, decirlo.
  - MC: devolver letra + justificación que cite la norma + una razón por opción descartada.
  - Semiabierta: 3–5 oraciones, ≤ 150 palabras, **la respuesta directa en la
    primera oración**; `palabras_clave` 3–6 términos; `referencia_legal`.
  - Abierta: `marco_normativo`, `analisis` (5–8 oraciones: hechos → norma → aplicación),
    `jurisprudencia` (solo sentencias presentes en la evidencia; si no hay,
    decirlo en una frase), `conclusion`.
- Post-proceso de longitud: recortar/validar oraciones y palabras.

**RAGAS answer correctness** = F1 de afirmaciones contra la respuesta esperada
(juez LLM) ponderado con similitud semántica (encoder e5-large). Premia
respuestas **precisas, directas y sin relleno**: cada afirmación extra no
sustentada baja la precisión. Evitar hedging, repetir la pregunta o listar
generalidades.

## 6. Citas (paso 4) — post-filtro determinista

1. `respaldadas = ⋃ citations.extract(p.texto) for p in pasajes[:10]`.
2. Para cada cita que `citations.extract` encuentra en el texto generado: si su
   cuerpo no está en `bodies(respaldadas)`, **eliminar la mención** (regex sobre
   el span) o, si no es posible, la oración; si la oración era imprescindible,
   reemplazarla por la versión con la norma del pasaje usado.
3. Normalizar “Ley N” sin año → “Ley N de AAAA” cuando el pasaje lo resuelve de forma única.
4. `referencia_legal` (semiabierta) y la línea final “Fundamento normativo: …”
   de la `justificacion` (MC) se **renderizan desde los metadatos** de los
   pasajes que el modelo marcó como usados, más las normas de los pasajes
   pertinentes (reranker ≥ umbral). Así las citas son reproducibles aunque la
   redacción varíe en la verificación en vivo. **(medir)** cuántos cuerpos
   incluir: más cuerpos respaldados sube el recall sin castigo, pero deben ser
   pertinentes (no volcar el top-10 entero a ciegas).
5. Prueba: sobre cualquier salida del pipeline, `citas_sin_respaldo == 0`.

## 7. Abstención

Cuentas por ítem (aproximadas, con los pesos oficiales):

- **MC**: responder aporta `p·(20/289 + 10/N)`; abstenerse aporta `0,5·10/N`.
  Con N≈850 ítems en calibración, responder conviene si `p ≳ 0,08`. Con 4
  opciones `p ≥ 0,25` siempre ⇒ **nunca abstenerse en MC**.
- **Texto libre**: abstenerse pierde RAGAS (30 pts sobre 250 ítems) y el recall
  de citas; solo gana 0,5 en calibración frente a 0 si se habría fallado.
  ⇒ Abstenerse **solo** si no se recuperó ningún pasaje pertinente (reranker
  bajo umbral en todos y ningún cuerpo del área). Umbral calibrado con la muestra.
- Al abstenerse: campos de contenido `""`, `abstencion: true`, y **se conservan
  los pasajes** recuperados (como en el ejemplo oficial, ítem 218).

## 8. Presupuesto de tiempo y hardware

- Sábado: 992 preguntas en ~6 h ⇒ **≤ 20 s por pregunta** de punta a punta con margen.
- Equipo de desarrollo actual: sin GPU dedicada (Radeon 780M, 15 GB RAM).
  Un 8B cuantizado en CPU no cumple el presupuesto. Plan:
  - Desarrollo diario: backend `llamacpp` con `Qwen3-8B-Q4_K_M.gguf` en CPU
    sobre subconjuntos pequeños (lento, sirve para validar el flujo).
  - Mediciones y ejecución final: GPU (sala Turing o Colab) con el backend
    `transformers` (o `llamacpp` compilado con CUDA), mismos pesos de Hugging Face.
- `runs/<tag>/tiempos.json`: p50/p95 por etapa (recuperación, rerank, generación).
- Reanudable: el pipeline salta ids ya presentes en la salida parcial.

## 9. Determinismo y verificación en vivo

El jurado regenera 2–3 preguntas y compara **normas citadas y pasajes**.
- Recuperación 100 % determinista (índice congelado, mismo encoder y dispositivo
  para consultas, desempates por id, scores redondeados).
- Citas derivadas de los pasajes (sección 6) ⇒ estables aunque cambie una palabra.
- `python -m src.pipeline.main --ids 51,290 --no-cache` regenera ítems sueltos y
  compara contra `submissions.jsonl` (script `src/eval/verificar.py`).
- Generación: sin batching variable en la corrida final o con la misma
  configuración de concurrencia que en la verificación.

## 10. Interfaz

`interfaz/`: FastAPI + HTML/JS estático (o Streamlit si se prefiere velocidad).
Consulta de extremo a extremo; muestra respuesta, **pasajes recuperados** con su
score y enlace a la fuente, y **normas citadas** marcadas como respaldadas.
Identidad visual de Software Colombia: logo cúbico turquesa/teal sobre fondo
oscuro o blanco, acentos azules (ver portada y contraportada de `enunciado.pdf`);
confirmar paleta y tipografía desde su sitio oficial antes de fijarla.
Comando: `python -m interfaz.app` → `http://localhost:8000`.
