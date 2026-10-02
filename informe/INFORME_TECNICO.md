# Informe técnico — Los PoliTICos

**Hackathon 2026 · Universidad de los Andes**
**Integrantes:** Juan José Cortés Villamil · Pablo Medina Forero · Miguel Santiago Roa Vallejo

---

## 1. Arquitectura del sistema

Una pregunta recorre cinco etapas deterministas, ejecutadas en proceso con modelos abiertos
descargados de Hugging Face. Ningún modelo cerrado ni API de terceros interviene; una lista blanca
de modelos abiertos en la configuración lo impone. El único servicio externo es el juez de RAGAS,
que usa el evaluador oficial.

1. **Ingesta.** 618 documentos oficiales (Constitución, códigos, leyes, decretos, resoluciones,
   circulares, sentencias y conceptos de DIAN, SIC y Supersociedades) se limpian y se segmentan
   **por artículo**; las sentencias, por secciones detectadas de forma estricta (antecedentes,
   consideraciones, resuelve, salvamentos). Cada fragmento empieza con el nombre canónico de su
   norma («Ley 1150 de 2007, artículo 11.»), verificado con el extractor de citas del evaluador.
   Una guardia anti-fuga bloquea la indexación si detecta material del banco de preguntas.
2. **Indexación.** 75.204 fragmentos: vectores `bge-m3` en FAISS exacto y BM25 con un tokenizador
   jurídico que conserva números de artículo y de sentencia. El índice se congela por sha256.
3. **Recuperación.** Router de artículos citados en la pregunta + BM25 + denso, fusionados con RRF,
   sesgo por área, topes de diversidad (por artículo y 4 por documento), reordenamiento con
   `bge-reranker-v2-m3` y un **cupo de 4 normas** entre los 10 pasajes para que los fragmentos de
   sentencia no desplacen a los artículos. En selección múltiple, 4 puestos son para la pregunta
   y el resto se reparte entre las opciones, cada una buscada con su texto más las palabras más
   raras de la pregunta.
4. **Generación.** El decoder recibe los 10 pasajes numerados `[P1]…[P10]` completos y produce el
   JSON del formato, forzado con una gramática derivada del esquema.
5. **Verificación.** Un post-filtro elimina toda cita que no figure en los 10 pasajes y las
   referencias se renderizan desde los encabezados de los pasajes. La línea se valida contra el
   esquema oficial.

## 2. Selección de encoder y decoder

| Componente | Modelo | Motivo | Alternativas |
|---|---|---|---|
| Encoder | `BAAI/bge-m3` (MIT) | Multilingüe, fuerte en español, 1.024 dimensiones (fragmentos de hasta 512 tokens) | `multilingual-e5-large` (en lista blanca); `jina-embeddings-v3` descartado por licencia CC-BY-NC |
| Decoder | `google/gemma-4-E4B-it` (Apache-2.0), GGUF Q8_0 | 7.996.156.490 parámetros en total (bajo el límite de 8B); igualó a Qwen3-8B en la muestra con mejores citas | `Qwen/Qwen3-8B` (Apache-2.0, GGUF Q4_K_M): versión anterior del sistema |
| Reranker | `BAAI/bge-reranker-v2-m3` (Apache-2.0) | Cross-encoder multilingüe, coherente con el encoder | Sin reranker |

**Inferencia.** Temperatura 0 (decodificación voraz), semilla fija, sin modo de razonamiento,
ventana de 8.192 tokens, `llama.cpp` en GPU. Tiempo por pregunta en una T4: 39 s en promedio
(selección múltiple 40 s, semiabiertas 35 s, abiertas 65 s). Para las 992 preguntas (~11 h en una
GPU) el banco se reparte por rangos entre varias máquinas (`run.py --rango INICIO FIN`). La
corrida es reproducible: dos ejecuciones en máquinas distintas produjeron respuestas idénticas.

## 3. Estrategia de recuperación

- **Segmentación:** un fragmento por artículo (con parágrafos); artículos de más de 300 palabras se
  parten repitiendo el encabezado; sentencias y conceptos en ventanas de ~300 palabras con 15 % de
  solape.
- **Fusión:** RRF (k = 60) de 50 candidatos densos y 50 léxicos; el reranker ordena los 20 mejores.
- **Selección múltiple:** evidencia representativa por opción, marcada en el prompt («recuperado
  para la opción B»).
- **Medida guía:** las normas del fundamento de referencia aparecen en la evidencia en 44 de 49
  casos (90 %), y en 38 de las 41 preguntas con fundamento citable hay al menos una.

## 4. Verificación de citas y abstención

**Citas.** El evaluador compara normas a nivel de cuerpo y castiga con el doble toda cita ausente
de los 10 pasajes. Por eso: (i) cada pasaje empieza con el nombre canónico de su norma; (ii) el
post-filtro localiza cada cita con las mismas expresiones regulares del evaluador y reemplaza las
no respaldadas por «la normativa aplicable»; (iii) las leyes citadas sin año se completan cuando
los pasajes lo resuelven; (iv) el «Fundamento normativo» se construye desde los encabezados de los
pasajes. Resultado: **0 citas sin respaldo** en todas las corridas.

**Abstención.** Con los pesos oficiales, abstenerse casi nunca conviene: vale 0 en RAGAS (30
puntos) y a lo sumo medio acierto en el componente de abstención (10 puntos). Por eso el sistema
no se abstiene en selección múltiple ni por baja pertinencia; solo cuando el modelo no produce una
respuesta utilizable.

## 5. Resultados sobre las preguntas de muestra

Evaluador oficial (`scripts/evaluate.py --ragas`), corrida `muestra_v10`, juez sin fallos:

| Componente | Puntos | Posibles |
|---|---:|---:|
| Exactitud en cerradas (9 de 15) | 12,00 | 20 |
| Calidad de citación (recall 0,796; 0 sin respaldo) | 15,92 | 20 |
| Abstención calibrada (0,767) | 7,67 | 10 |
| **Total automático sin RAGAS** | **35,59** | **50** |
| Corrección en texto libre — RAGAS (0,4335; referencia 0,451) | 13,00 | 30 |
| **Total automático** | **48,59** | **80** |

**Evolución.** Línea base 48,67 → mejor resultado 49,64 (corpus de 238 documentos, Qwen3-8B).
Cambios que aportaron: evidencia por opción en selección múltiple, cupo de normas (+3 citas
acertadas) y no abstenerse (+2 preguntas respondidas). Cambios que no aportaron y se retiraron:
el razonamiento de Qwen3 en selección múltiple (+1 acierto en una corrida y 0 en la siguiente, con
el doble de tiempo y menos citas) y la respuesta en abierto antes de elegir (+1 acierto con el
doble de latencia). Ampliar el corpus de 238 a 618 documentos no movió el texto libre de forma
apreciable. Lección metodológica: varias caídas aparentes de RAGAS eran respuestas sin veredicto
del juez por fallos de red, que el evaluador cuenta como cero.

**Errores en selección múltiple (6 de 15).** Son de tres tipos:
- **La norma está en el corpus pero no llega a la evidencia o no basta:** 748 (el art. 137 del
  CPACA enumera las cuatro opciones como causales de nulidad) y 647.
- **Falta información:** 528, porque el valor del salario mínimo no está en el corpus; 671, sobre
  convenios de doble imposición.
- **Claves discutibles:** 58, que pide la «Ley 1564 de 2002» (el Código General del Proceso es de
  2012), y 128, que exige «Fintech» cuando la norma solo nombra bancos y compañías de
  financiamiento.

## 6. Limitaciones

1. **Dependencia del corpus:** una norma ausente no se puede citar con respaldo; el filtro evita
   inventarla, pero la respuesta pierde fundamento.
2. **Citas a nivel de cuerpo:** la verificación garantiza que la norma citada está en la evidencia,
   no que el artículo concreto sea el pertinente.
3. **Razonamiento del modelo de 8B:** en selección múltiple, con la misma evidencia la letra elegida
   varía según cómo se presentan las opciones. La exactitud (0,60) sigue lejos de la referencia
   (0,905).
4. **Costo de cómputo:** ~39 s por pregunta en GPU T4 y ~3,5 min en CPU; el banco completo
   requiere varias GPU en paralelo.
5. **Doctrina no normativa:** las preguntas cuyo fundamento es doctrina o derecho extranjero (p. ej.
   el caso *Dow Chemical*) solo se responden con evidencia parcial.
