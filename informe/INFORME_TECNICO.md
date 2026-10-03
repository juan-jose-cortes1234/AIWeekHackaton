# Informe técnico — Los PoliTICos

**Hackathon 2026 · Universidad de los Andes**
**Integrantes:** Juan José Cortés Villamil · Pablo Medina Forero · Miguel Santiago Roa Vallejo

---

## 1. Arquitectura del sistema

Una pregunta recorre cinco etapas deterministas, ejecutadas en proceso con modelos abiertos
descargados de Hugging Face. Ningún modelo cerrado ni API de terceros interviene; una lista blanca
de modelos abiertos en la configuración lo impone. El único servicio externo es el juez de RAGAS,
que usa el evaluador oficial.

1. **Ingesta.** 728 documentos oficiales (Constitución, códigos, leyes —incluidos 16 convenios
   para evitar la doble imposición—, decretos, resoluciones, circulares, sentencias y conceptos de
   DIAN, SIC y Supersociedades) se limpian y se segmentan **por artículo** y **por secciones** en
   sentencias y conceptos (en sentencias, detectadas de forma estricta: antecedentes,
   consideraciones, resuelve, salvamentos), con subdivisión de textos extensos e inclusión de
   preámbulos y notas de vigencia. Cada fragmento empieza con el nombre canónico de su
   norma («Ley 1150 de 2007, artículo 11.»), verificado con el extractor de citas del evaluador.
   Una guardia anti-fuga bloquea la indexación si detecta material del banco de preguntas.
2. **Indexación.** 86.963 fragmentos (49.286 de artículos, 30.622 de secciones, 1.374 de preámbulos y
   5.681 de notas): vectores `bge-m3` en FAISS exacto y BM25 con un tokenizador
   jurídico que conserva números de artículo y de sentencia. El índice se construye una sola vez,
   se congela por sha256 y se distribuye idéntico a todas las máquinas de la ejecución.
3. **Recuperación.** Router de artículos citados en la pregunta + BM25 + denso, fusionados con RRF,
   sesgo por área, topes de diversidad (por artículo y 4 por documento), reordenamiento con
   `bge-reranker-v2-m3` y un **cupo de 4 normas** entre los 10 pasajes para que los fragmentos de
   sentencia no desplacen a los artículos. En selección múltiple, 4 puestos son para la pregunta
   y el resto se reparte entre las opciones, cada una buscada con su texto más las palabras más
   raras de la pregunta.
4. **Generación.** El decoder recibe los 10 pasajes numerados `[P1]…[P10]` completos, con la
   plantilla de chat propia del modelo, y produce el JSON del formato, forzado con una gramática
   derivada del esquema. En selección múltiple, cada alternativa se **verifica por separado**:
   una llamada independiente por opción la clasifica como *respaldada*, *contradicha* o con
   *evidencia insuficiente*, con citas textuales que se comprueban literalmente contra el pasaje
   (una cita alterada degrada la conclusión). Una quinta llamada compara los cuatro informes
   comprobados y elige; así se distingue «no encontré respaldo» de «es incorrecta» y el modelo no
   justifica a posteriori una letra ya elegida. El prompt tolera errores de digitación en números y
   años y maneja opciones combinadas («(a) y (b)», «Todas las anteriores»).
5. **Verificación.** Un post-filtro elimina toda cita que no figure en los 10 pasajes y las
   referencias se renderizan desde los encabezados de los pasajes. La línea se valida contra el
   esquema oficial.

## 2. Selección de encoder y decoder

| Componente | Modelo | Motivo | Alternativas |
|---|---|---|---|
| Encoder | `BAAI/bge-m3` (MIT) | Multilingüe, fuerte en español, 1.024 dimensiones (fragmentos de hasta 512 tokens) | `multilingual-e5-large` (en lista blanca); `jina-embeddings-v3` descartado por licencia CC-BY-NC |
| Decoder | `google/gemma-4-E4B-it` (Apache-2.0), GGUF Q8_0, con su plantilla de chat y sin canal de razonamiento | 7.996.156.490 parámetros en total (bajo el límite de 8B); con su plantilla propia superó a Qwen3-8B en la muestra | `Qwen/Qwen3-8B` (Apache-2.0, GGUF Q4_K_M): versión anterior del sistema |
| Reranker | `BAAI/bge-reranker-v2-m3` (Apache-2.0) | Cross-encoder multilingüe, coherente con el encoder | Sin reranker |

**Inferencia.** Temperatura 0 (decodificación voraz), semilla fija, sin modo de razonamiento,
ventana de 8.192 tokens, `llama.cpp` en GPU. Tiempo por pregunta con una llamada: ~40 s en una
T4 y ~10 s en una RTX 4090; la verificación de alternativas usa cinco llamadas por pregunta de
selección múltiple (290 de las 992). El banco se reparte por rangos (`run.py --rango INICIO FIN`)
entre tres equipos con RTX 4090 de la sala Turing y sesiones de Colab y Kaggle, todos con el mismo
índice (verificado por sha256). En Turing, `llama.cpp` se compiló en cada máquina para su
procesador: la rueda precompilada usaba instrucciones AVX-512 que esos procesadores no tienen.
La corrida es reproducible: dos ejecuciones en máquinas distintas produjeron respuestas idénticas.

## 3. Estrategia de recuperación

- **Segmentación:** un fragmento por artículo (con parágrafos); artículos de más de 300 palabras se
  parten repitiendo el encabezado; sentencias y conceptos por secciones, en ventanas de ~300 palabras
  con 15 % de solape; preámbulos y notas de vigencia como fragmentos propios ligados a su norma.
- **Fusión:** RRF (k = 60) de 50 candidatos densos y 50 léxicos; el reranker ordena los 20 mejores.
- **Selección múltiple:** evidencia representativa por opción, marcada en el prompt («recuperado
  para la opción B»).
- **Medida guía:** las normas del fundamento de referencia aparecen en la evidencia en 46 de 49
  casos (94 %), y en 40 de las 41 preguntas con fundamento citable hay al menos una.

## 4. Verificación de citas y abstención

**Citas.** El evaluador compara normas a nivel de cuerpo y castiga con el doble toda cita ausente
de los 10 pasajes. Por eso: (i) cada pasaje empieza con el nombre canónico de su norma; (ii) el
post-filtro localiza cada cita con las mismas expresiones regulares del evaluador y reemplaza las
no respaldadas por «la normativa aplicable»; (iii) las leyes citadas sin año se completan cuando
los pasajes lo resuelven; (iv) el «Fundamento normativo» se construye desde los encabezados de los
pasajes. Resultado: **0 citas sin respaldo** en todas las corridas.

**Abstención.** El sistema registra `abstencion: true` en texto libre cuando el corpus no da
fundamento suficiente —ningún pasaje supera 0,025 de pertinencia según el reranker y la pregunta
no cita una norma presente en el corpus— o cuando el modelo no produce una respuesta utilizable.
El umbral es bajo a propósito: con los pesos oficiales, una respuesta fundamentada vale más que la
abstención. En selección múltiple siempre se elige una opción, porque responder aporta más que
abstenerse incluso al azar. Las respuestas respetan los límites del enunciado: semiabiertas de 3 a
5 oraciones y máximo 150 palabras; análisis de las abiertas de 5 a 8 oraciones, con un tope total
de 500 palabras.

## 5. Resultados sobre las preguntas de muestra

Evaluador oficial (`scripts/evaluate.py --ragas`), corrida `muestra_v12` (corpus de 650
documentos, selección múltiple con elección directa), con el umbral de abstención de 0,025 del
sistema de entrega y juez sin fallos. Ninguna pregunta de la muestra queda por debajo del umbral
(pertinencia mínima 0,034), por lo que no hubo abstenciones:

| Componente | Puntos | Posibles |
|---|---:|---:|
| Exactitud en cerradas (11 de 15) | 14,67 | 20 |
| Calidad de citación (recall 0,816; 0 sin respaldo) | 16,33 | 20 |
| Abstención calibrada (0,837) | 8,37 | 10 |
| **Total automático sin RAGAS** | **39,37** | **50** |
| Corrección en texto libre — RAGAS (0,4572; referencia 0,451) | 13,72 | 30 |
| **Total automático** | **53,09** | **80** |

**Evolución.** Línea base 48,67 (Qwen3-8B, 186 documentos) → 49,64 (238 documentos) → **53,09**
(Gemma 4 E4B, 650 documentos). Cambios que aportaron: evidencia por opción en selección múltiple,
cupo de normas (+3 citas acertadas), no abstenerse (+2 preguntas respondidas), las reglas de
elección del prompt de selección múltiple (+1) y la plantilla de chat propia de Gemma 4 junto con
la ampliación del corpus (+1 en selección múltiple, +2 citas, RAGAS 0,428 → 0,457). Cambios que no aportaron y se retiraron:
el razonamiento de Qwen3 en selección múltiple (+1 acierto en una corrida y 0 en la siguiente, con
el doble de tiempo y menos citas) y la respuesta en abierto antes de elegir (+1 acierto con el
doble de latencia). Lección metodológica: varias caídas aparentes de RAGAS eran respuestas sin veredicto
del juez por fallos de red, que el evaluador cuenta como cero.

**Verificación de alternativas (sistema final).** Sobre las mismas 15 preguntas cerradas, la
verificación independiente de cada opción acertó **12 de 15** (frente a 11 con elección directa),
lo que equivale a 16,00 de 20 puntos en exactitud. Solo se midió la exactitud: la verificación
también reescribe la justificación de las cerradas (de donde se extraen sus citas), y ese efecto no
se volvió a medir; semiabiertas y abiertas no cambian.

**Errores en selección múltiple con elección directa (4 de 15).** 647 (la ayuda como efecto personal del matrimonio:
la evidencia son sentencias y no el art. 176 del Código Civil), 671 (reglas de desempate de
residencia en convenios de doble imposición: doctrina) y dos claves discutibles: la 58, que pide la «Ley 1564 de 2002» (el Código General del Proceso es de 2012), y la 128, que exige «Fintech» cuando la norma solo nombra bancos y compañías de
  financiamiento.

## 6. Limitaciones

1. **Dependencia del corpus:** una norma ausente no se puede citar con respaldo; el filtro evita
   inventarla, pero la respuesta pierde fundamento.
2. **Citas a nivel de cuerpo:** la verificación garantiza que la norma citada está en la evidencia,
   no que el artículo concreto sea el pertinente.
3. **Razonamiento del modelo de 8B:** en selección múltiple, con la misma evidencia la letra elegida
   varía según cómo se presentan las opciones. La exactitud (0,80 con la verificación de
   alternativas) sigue lejos de la referencia (0,905).
4. **Costo de cómputo:** ~40 s por pregunta en GPU T4, ~10 s en RTX 4090 y ~3,5 min en CPU; la
   verificación multiplica por cinco las llamadas en selección múltiple. El banco completo requiere
   varias GPU en paralelo.
5. **Doctrina no normativa:** las preguntas cuyo fundamento es doctrina o derecho extranjero (p. ej.
   el caso *Dow Chemical*) solo se responden con evidencia parcial. Las orientaciones internacionales
   incorporadas (ONU, OCDE, RIPD) sirven como evidencia, pero el evaluador no las reconoce como cita.
6. **Corpus final sin medición completa:** el 3 de octubre se incorporaron 78 fuentes oficiales
   más (documentadas en `CORPUS.md`), identificadas a partir de las normas que nombran los
   enunciados del banco; el sistema final no se volvió a evaluar completo sobre la muestra con ese
   corpus.
