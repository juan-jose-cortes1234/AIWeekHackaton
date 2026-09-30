# Bitácora del corpus — <Nombre del equipo>

Bitácora exigida en el paso 5 del enunciado (5 puntos: inventario completo y
trazable 2; justificación frente a la composición del banco 1,5; corpus
reconstruible a partir de las URL declaradas 1,5).

Las tablas entre marcas `AUTO` las regenera `python -m src.corpus.manifest` a
partir de `fuentes.csv` y del corpus procesado; no las editen a mano. La prosa
(criterio, método, lectura de la curva) la escribe el equipo; los borradores
están marcados con `BORRADOR`.

---

## 1. Inventario

Un registro por documento incorporado. Coincide con `corpus_manifest.json`.

<!-- AUTO:inventario -->
_Aún no hay corpus procesado._
<!-- /AUTO:inventario -->

**Totales**

<!-- AUTO:totales -->
_Aún no hay corpus procesado._
<!-- /AUTO:totales -->

## 2. Criterio de selección

<!-- AUTO:cobertura -->
_Aún no hay corpus procesado._
<!-- /AUTO:cobertura -->

<!-- BORRADOR: justificar la selección frente a las diez áreas y las sub-tareas
del banco (enunciado §4.2). Puntos a cubrir: prioridad por peso de cada área y
por `items_del_banco` de seed_targets.json; códigos incorporados que el seed no
listaba (Código Civil, Comercio, Penal, CPACA…) y por qué; jurisprudencia
incorporada para las sub-tareas de precedente, sentido del fallo y ratio
decidendi. -->

Documentos descartados y el motivo del descarte:

<!-- BORRADOR: qué se consideró y no se incorporó, y por qué (derecho ambiental
e internacional fuera del banco; doctrina con derechos de autor; etc.). -->

## 3. Método de ingesta y limpieza

1. **Descarga.** Manual desde las fuentes oficiales declaradas en `fuentes.csv`
   (URL y fecha de consulta por documento).
2. **Extracción de texto.** HTML con BeautifulSoup (detección de UTF-8 /
   windows-1252, eliminación de navegación, scripts y pies); PDF con PyMuPDF,
   eliminando encabezados y números de página repetidos, y OCR con Tesseract
   solo en páginas sin capa de texto; DOCX con python-docx. Las normas publicadas
   en varias páginas se unen en orden.
3. **Normalización.** Unicode NFC, espacios y saltos de línea uniformes,
   eliminación de caracteres invisibles, unión de palabras partidas por guion.
4. **Segmentación.** Normas: un fragmento por artículo (incluye parágrafos,
   artículos con letra, bis, transitorios, numeración con guion y decretos
   únicos con numeración decimal); las notas de vigencia y jurisprudencia de la
   Secretaría del Senado quedan como fragmento aparte ligado al artículo; las
   concordancias se descartan. Sentencias: por secciones (antecedentes,
   consideraciones, resuelve…) en ventanas de ~300 palabras con 15 % de solape.
   Fragmentos de más de 300 palabras se parten repitiendo el encabezado.
5. **Extracción de metadatos.** Tipo de norma, número, año, artículo, órgano
   emisor, vigencia, áreas y sección; cada fragmento comienza con el nombre
   canónico de su norma (p. ej. “Ley 1150 de 2007, artículo 11.”), lo que
   garantiza la trazabilidad norma–artículo exigida en el paso 1.
6. **Indexación.** Encoder abierto `BAAI/bge-m3` (MIT, 1.024 dimensiones, entrada
   truncada a 512 tokens), vectores normalizados e índice exacto `faiss.IndexFlatIP`;
   caché de embeddings por hash del texto y manifiesto con sha256 de fragmentos e
   índice para congelarlo.
   Recuperación híbrida: BM25 (bm25s, tokenizador jurídico que conserva números de
   artículo y de sentencia) + denso, fusionados con RRF; router directo cuando la
   pregunta cita un artículo; reordenamiento con `BAAI/bge-reranker-v2-m3` (Apache-2.0).

Controles automáticos: 100 % de los fragmentos identifican su norma con el
mismo extractor de citas del evaluador oficial; cada pasaje es literal respecto
al documento procesado (offsets `inicio`/`fin`); guardia anti-fuga contra el
banco de preguntas.

Problemas encontrados y cómo se resolvieron:

<!-- BORRADOR: OCR defectuoso, artículos derogados, numeraciones inconsistentes… -->

## 4. Evolución del puntaje

Puntaje sobre las 50 preguntas de muestra en al menos tres momentos de la
semana, con el efecto atribuible a cada incorporación documental.

| Fecha | Documentos | Fragmentos | Cerradas /20 | Citación /20 | Abstención /10 | Total /50 | Qué cambió |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-09-29 | 186 | 41.384 | 12,00 | 15,51 | 7,79 | 35,30 | Corpus inicial completo (nivel 1 y 2 de la guía + 150 sentencias del seed). RAGAS 0,4456 (13,37/30) |

Lectura de la curva:

<!-- BORRADOR: qué incorporaciones movieron el puntaje y cuáles no. -->

## 5. Licencia

El corpus se publica bajo CC-BY-4.0. Los textos normativos colombianos son de
dominio público; la licencia cubre el trabajo de procesamiento, segmentación y
extracción de metadatos realizado por el equipo.
