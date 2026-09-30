### ¿Tu solución es predecible?

**La respuesta corta es: La intuición general la tendrán algunos, pero la ejecución que propones NO es predecible para el 90% de los concursantes.**

*   **Lo que sí es predecible:** Pensar en "descomponer la pregunta" o usar *Chain-of-Thought* (CoT) es un concepto conocido en NLP. Varios equipos intentarán pedirle al modelo "piensa paso a paso".
*   **Por qué tu propuesta concreta NO es predecible:** La mayoría de los estudiantes abordará las preguntas abiertas pidiéndole al LLM que redacte libremente como "un abogado experto". Casi nadie estructurará la descomposición como un **checklist cerrado de subsunción judicial** (Premisa Mayor $\rightarrow$ Hechos $\rightarrow$ Excepciones $\rightarrow$ Fallo binario). 
*   Además, la gran mayoría de los que intenten descomponer preguntas cometerán el error de hacer **múltiples llamadas HTTP/LLM en bucle** y se estrellarán el sábado contra el muro del tiempo (992 preguntas en 6 horas $\approx$ 21 s por pregunta). Hacerlo en **un solo pase estructurado** es una ventaja táctica que muy pocos verán.

---

### Ideas de Mejora: Las Predecibles vs. Las Difíciles de Pensar

Para ganar una hackathon como esta, debes saber qué va a hacer la masa (para no quedarte atrás) y qué trucos de ingeniería matemática y legal te pondrán en el podio.

---

### 1. Las ideas predecibles (lo que harán casi todos los equipos)

1.  **Chunking ingenuo por número de caracteres (500 o 1.000 caracteres):**
    *   *El error común:* Usar el `RecursiveCharacterTextSplitter` de LangChain. En derecho esto es letal: si partes un artículo por la mitad, dejas el supuesto de hecho en un fragmento y la consecuencia o excepción en el siguiente.
    *   *Lo que ya tiene tu sistema:* Segmentación **estricta por artículo** (la unidad de sentido normativo).
2.  **Prompting de "Actúa como jurista elocuente":**
    *   *El error común:* Prompts que piden prosa sofisticada. El benchmark oficial ya demostró que la elocuencia tiene **correlación negativa ($\rho = -0.46$) con el acierto**: el modelo suena convincente pero inventa normas que no existen.
3.  **Descargar solo las normas de `seed_targets.json`:**
    *   *El error común:* Creer que el archivo semilla es el temario completo. Quien solo descargue lo del seed se quedará sin el Código Civil, el Código Penal, el Código de Comercio o el CPACA, que representan más de 400 preguntas del banco.
4.  **RAG estándar de una sola pasada (pregunta $\rightarrow$ embeddings $\rightarrow$ LLM):**
    *   *El error común:* Lanzar la pregunta tal cual contra la base de datos vectorial sin pre-procesamiento ni reranking.

---

### 2. Las ideas difíciles de pensar (ventajas competitivas reales)

Estas son las técnicas de ingeniería de precisión que explotan las reglas matemáticas del evaluador oficial:

#### A. La "Inyección Canónica Inversa" de Citas (Puntaje de Citas Gratis)
*   **El problema:** En las preguntas semiabiertas y abiertas, si el LLM olvida escribir el año de la ley o escribe "el código procesal" en lugar de "Código General del Proceso", el evaluador no le otorga el punto de citación.
*   **La jugada maestra:** No dependas de la memoria del LLM para el campo `referencia_legal` o `marco_normativo`. Como tu recuperador híbrido ya sabe exactamente qué artículos recuperó en los pasajes `[P1]...[P3]` (con su encabezado canónico perfecto: `"Ley 1564 de 2012, artículo 391"`):
    *   Puedes **inyectar programáticamente** esos encabezados en el campo `referencia_legal` mediante código Python post-generación.
    *   Resultado: El recall de citas sube automáticamente al máximo y la tasa de citas no respaldadas es **exactamente 0**, protegiéndote de la penalización doble.

#### B. Multi-Query por Opciones en Preguntas Cerradas
*   **El problema:** En preguntas de opción múltiple, la pregunta suele ser genérica (ej. *"¿Cuál de las siguientes afirmaciones sobre la apelación es correcta?"*). Si buscas solo esa frase en el índice, recuperas conceptos generales de apelación, pero no el artículo específico que valida la opción D.
*   **La jugada maestra:** Recuperar usando **5 consultas combinadas**:
    *   Consulta 0: La pregunta.
    *   Consultas 1 a 4: La pregunta + el texto de cada opción (A, B, C, D).
    *   Fusionar los resultados con RRF (*Reciprocal Rank Fusion*). De esta forma, el artículo exacto que desmiente o confirma una de las opciones entra obligatoriamente en el Top-10 de evidencia.

#### C. Router Determinista por Regex (Burlar la debilidad de los Embeddings)
*   **El problema:** Los modelos de embeddings densos representan significado, pero **fracasan distinguiendo números**. Para un encoder vectorial, el vector de *"artículo 42"* y el de *"artículo 24"* son casi idénticos.
*   **La jugada maestra:** Si la pregunta menciona explícitamente una norma (ej. *"artículo 899 del Código de Comercio"* o *"Ley 1150 de 2007"*), un router por expresiones regulares salta la búsqueda vectorial e **inserta ese artículo exacto de primero (`[P1]`) con score 1.0**. Esto garantiza acierto del 100% en preguntas con cita textual.

#### D. Teoría de Juegos en la Abstención: La Regla de Oro Asimétrica
*   **La fórmula del evaluador:** Acertar = 1 pt, Abstenerse = 0.5 pts, Equivocarse = 0 pts.
*   **Estrategia asimétrica matemática:**
    1.  **En Opción Múltiple (Cerradas): NUNCA abstenerse.** Si respondes al azar o por descarte tienes entre 25% y 75% de probabilidad de ganar 1.0 punto; si te abstienes recibes 0 en exactitud cerrada.
    2.  **En Texto Libre (Semiabiertas y Abiertas): Abstención agresiva si el Reranker es bajo.** Si el mejor score de tus pasajes es $< 0.08$ (es decir, el tema no está en tu corpus), **declara abstención de inmediato**. Te llevas 0.5 puntos automáticos y evitas que el LLM invente una norma que te castigaría con el doble de penalización en citas.

#### E. Compresión Asimétrica de Evidencia (Para no ahogar al 8B)
*   Pasar 10 pasajes completos de 300 palabras son ~4.000 tokens de contexto. En un modelo de 8B, 4.000 tokens ralentizan la inferencia a más de 100 segundos en CPU o calientan la GPU.
*   **La técnica:** Pasa el texto completo **únicamente de los primeros 3 pasajes** (los más relevantes según el reranker), y de los pasajes 4 al 10 pasa **solo el encabezado canónico y las primeras 2 líneas**.
    *   Ahorras 60% de tokens y triplicas la velocidad de generación.
    *   El evaluador sigue viendo los 10 pasajes en `pasajes_recuperados`, por lo que tus respaldos de citas siguen siendo 100% válidos.

---

### Cuadro Resumen de Diferenciación

| Si haces lo que hacen todos... | Si implementas estas técnicas... |
| :--- | :--- |
| El modelo escribe prosa bonita pero cita artículos equivocados $\rightarrow$ **0 pts en citas**. | Post-filtro regex elimina normas no respaldadas e inyecta encabezados canónicos $\rightarrow$ **20 pts en citas**. |
| Las preguntas abiertas divagan y fallan en RAGAS $\rightarrow$ **< 0.35 en RAGAS**. | **Tu idea del checklist cerrado** fuerza un silogismo judicial estricto $\rightarrow$ **> 0.60 en RAGAS**. |
| En opción múltiple recuperan solo la pregunta y el artículo clave no aparece. | Multi-query con las 4 opciones asegura que el artículo que valida la opción correcta esté en el Top-3. |
| El sábado colapsan por tiempo haciendo 3 llamadas LLM por ítem. | Single-pass decomposition en un solo prompt estructurado ($\leq 3$ s por ítem). |
