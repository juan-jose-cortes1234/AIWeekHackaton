# Informe técnico — <Nombre del equipo>

**Hackathon 2026 · Universidad de los Andes**
**Integrantes:** <nombre 1> · <nombre 2> · <nombre 3>

<!-- BORRADOR generado a partir del código y de las mediciones registradas en
PROGRESO.md. Completar los marcadores <…> con las mediciones sobre la muestra y
exportar a informe/INFORME_TECNICO.pdf (máximo 3 páginas). -->

---

## 1. Arquitectura del sistema

Una pregunta recorre cinco etapas, todas deterministas y ejecutadas en proceso
con modelos abiertos descargados de Hugging Face (ningún modelo cerrado ni API
de terceros interviene; una lista blanca en la configuración lo impone):

1. **Ingesta (previa).** Cada documento del corpus (`fuentes.csv` + HTML/PDF/DOCX)
   se limpia, se segmenta **por artículo** (sentencias: por secciones) y cada
   fragmento se encabeza con el nombre canónico de su norma —«Ley 1150 de 2007,
   artículo 11.»—, verificado con el mismo extractor de citas del evaluador. Una
   guardia anti-fuga bloquea la indexación si detecta material del banco.
2. **Indexación (previa).** Embeddings `bge-m3` en un índice FAISS exacto y un
   índice BM25 con tokenizador jurídico; el índice se congela por sha256.
3. **Recuperación.** Router de artículos citados en la pregunta + BM25 + denso,
   fusionados con RRF, sesgo por área, diversidad por artículo y reordenamiento
   con `bge-reranker-v2-m3`; en selección múltiple cada opción es una consulta
   adicional. Salen 10 pasajes.
4. **Generación.** Qwen3-8B recibe los pasajes numerados `[P1]…[P10]` completos
   (si no caben en la ventana, se descartan pasajes enteros desde el final) y
   produce el JSON del formato, forzado con una gramática.
5. **Verificación.** Un post-filtro elimina toda cita que no figure en los 10
   pasajes, las referencias se renderizan desde los metadatos de los pasajes
   usados y se decide la abstención. La línea se valida contra el esquema oficial.

## 2. Selección de encoder y decoder

| Componente | Modelo | Motivo de la elección | Alternativas descartadas |
|---|---|---|---|
| Encoder | `BAAI/bge-m3` (MIT) | Multilingüe con buen desempeño en español, 1.024 dimensiones, sin prefijos | `multilingual-e5-large` (alternativa en lista blanca); `jina-embeddings-v3` por licencia CC-BY-NC |
| Decoder | `Qwen/Qwen3-8B` (Apache-2.0) | ≤ 8B, en la lista sugerida, buen español y salida estructurada fiable | `Llama-3.1-8B` (licencia comunitaria, no abierta en sentido estricto); `salamandra-7b-instruct` (alternativa en lista blanca) |
| Reranker | `BAAI/bge-reranker-v2-m3` (Apache-2.0) | Cross-encoder multilingüe coherente con el encoder | Sin reranker (se mide en `<experimento>`) |

**Configuración de inferencia.** Temperatura 0 (decodificación voraz, top-k 1),
semilla fija, modo sin razonamiento de Qwen3, ventana de 8.192 tokens. Backend
`llamacpp` con GGUF Q4_K_M en CPU y `transformers` bf16 en GPU. Tiempo medido en
CPU (Ryzen 7 8840HS): ~150 s por pregunta, 158 s con 10 pasajes completos
(4.188 tokens de prompt); en GPU: `<medido en la sala Turing>` s por pregunta.

## 3. Estrategia de recuperación

- **Segmentación:** un fragmento por artículo (con parágrafos); artículos de más
  de 300 palabras se parten repitiendo el encabezado; notas de vigencia del
  Senado como fragmento aparte; sentencias por secciones en ventanas de ~300
  palabras con 15 % de solape.
- **Índices:** FAISS `IndexFlatIP` (exacto) sobre vectores normalizados; BM25
  (`bm25s`) con tokenizador que conserva números de artículo y de sentencia.
- **Fusión:** RRF (k = 60) de las listas densa y léxica (50 candidatos cada
  una), + router directo por metadatos cuando la pregunta cita un artículo.
- **Top-k:** reranker sobre los 20 mejores; 10 pasajes a la entrega y al prompt.
- **Métrica guía:** acierto@10 de cuerpos normativos del fundamento de referencia
  sobre la muestra: `<x %>` (`python -m src.eval.recuperacion`).

## 4. Verificación de citas y abstención

**Citas.** El evaluador compara normas a nivel de cuerpo y castiga con el doble
cada cita que no figura en los primeros 10 pasajes. Por eso (i) cada pasaje
empieza con el nombre canónico de su norma; (ii) el post-filtro localiza cada
cita con las mismas expresiones regulares del evaluador y reemplaza las no
respaldadas por «la normativa aplicable» (o descarta la oración); (iii) las
leyes citadas sin año se completan cuando los pasajes lo resuelven de forma
única; (iv) `referencia_legal` y el «Fundamento normativo» de la justificación se
construyen desde los encabezados de los pasajes usados por el modelo y de los
pertinentes según el reranker, lo que además hace reproducibles las citas en la
verificación en vivo. Resultado: 0 citas sin respaldo según el evaluador.

**Abstención.** Con los pesos oficiales, abstenerse en selección múltiple nunca
conviene (responder aporta más incluso al azar), así que no se hace. En texto
libre se declara solo si no hay pasajes, si el modelo no produjo una respuesta
utilizable, o si la pertinencia máxima del reranker está bajo el umbral (0,05) y
la pregunta no cita una norma presente en el corpus. Se conservan los pasajes.

## 5. Resultados sobre las preguntas de muestra

| Componente | Puntos | Posibles |
|---|---:|---:|
| Exactitud en cerradas | `<x>` | 20 |
| Calidad de citación | `<x>` | 20 |
| Abstención calibrada | `<x>` | 10 |
| **Total automático sin RAGAS** | `<x>` | **50** |
| Corrección en texto libre (RAGAS) | `<x>` | 30 |

Análisis de los errores más frecuentes: `<a partir de runs/<tag>/trazas.jsonl:
normas ausentes del corpus, recuperación de un artículo vecino, opciones MC que
exigen conocimiento no normativo…>`

## 6. Limitaciones

1. **Dependencia del corpus:** si la norma aplicable no está en el corpus, el
   sistema no puede citarla con respaldo; el filtro evita inventarla pero la
   respuesta pierde fundamento. `<cobertura del seed: x %>`.
2. **Citas a nivel de cuerpo:** la verificación garantiza que la norma citada
   está en la evidencia, no que el artículo concreto sea el pertinente.
3. **Costo de cómputo:** en CPU una respuesta tarda ~2,5 min; el sistema requiere
   GPU para el banco completo.
4. **Segmentación dependiente del formato de la fuente:** PDF escaneados sin OCR
   o numeraciones atípicas pueden producir artículos mal cortados.
5. `<limitaciones observadas en la muestra>`
