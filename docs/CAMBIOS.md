# Registro de cambios del sistema

Trazabilidad de cada modificación que afecta el comportamiento del sistema: **cómo
estaba antes, cómo está ahora, por qué se cambió y con qué evidencia**. Lo mantiene el
loop (ver `LOOP.md` §4); las entradas más recientes van al final.

Cada entrada sigue esta plantilla:

```
## C-NN · AAAA-MM-DD · <título> (tarea TXX)
- Antes: comportamiento previo (con el caso que lo evidenció).
- Ahora: comportamiento nuevo.
- Por qué: problema que resuelve.
- Evidencia: medición antes/después (puntaje, caso, prueba). Si aún no se midió, decirlo.
- Archivos: código y configuración tocados.
- Requiere reindexar: sí/no.
```

Línea base de referencia (antes de C-01): corrida `runs/muestra_colab` del 2026-09-29 —
cerradas 12,00/20 (9/15) · citas 15,51/20 · abstención 7,79/10 · RAGAS 13,37/30 ·
**total 48,67/80** · ~35 s por pregunta en GPU T4.

---

## C-01 · 2026-09-30 · Respuestas abiertas sin truncar (tarea T22a)
- **Antes:** tope de salida de 900 tokens para preguntas abiertas. Si el modelo escribía más, el
  JSON quedaba cortado, el sistema lo reintentaba con la misma instrucción (con temperatura 0 el
  resultado es idéntico: se volvía a cortar) y, sin JSON válido, se registraba **abstención**.
  Caso: pregunta 247 (avenida 68, artículo 2 de la Constitución) → 1.800 tokens en dos intentos,
  163 s, abstención, 0 en RAGAS y en citas pese a tener la norma en la evidencia.
- **Ahora:** (1) tope de 1.400 tokens para abiertas; (2) prompt de abiertas más conciso (máximo 5
  normas en el marco, una frase por norma, sin repetir hechos ni textos); (3) si la salida se corta
  por longitud (`finish_reason == "length"`), **no se reintenta** y se **rescatan los campos
  completos** con `reparar_json_truncado`; el reintento queda solo para JSON mal formado sin corte;
  (4) en abiertas rescatadas se completan campos faltantes sin inventar contenido: conclusión = última
  oración del análisis, jurisprudencia = frase fija "La evidencia recuperada no incluye jurisprudencia
  pertinente para el caso."; (5) la abstención exige el campo principal (`respuesta` en
  semiabiertas, `analisis` en abiertas).
- **Por qué:** una respuesta parcial fundamentada vale más que una abstención (RAGAS y citas), y el
  reintento inútil duplicaba el tiempo en los casos más lentos.
- **Evidencia:** pruebas nuevas (reparación de JSON en 6 casos; salida real de Qwen3-8B cortada a
  120 tokens → rescatada, sin reintento; abierta rescatada pasa `evaluate.validate`). Medición sobre
  la muestra (caso 247 y tiempo de abiertas): **la 247 ya no se abstiene: responde y acierta la norma (Ley 472 de 1998); generación máx. 163 s → 81 s** (ver «Medición conjunta» al final).
- **Archivos:** `src/generation/llm.py`, `src/generation/contexto.py`,
  `src/generation/prompts/open_ended.txt`, `src/generation/citas.py`, `src/generation/abstencion.py`,
  pruebas en `tests/test_llm.py`, `tests/test_citas.py`, `tests/test_abstencion.py`.
- **Requiere reindexar:** no.

## C-02 · 2026-09-30 · Tope de 4 pasajes por documento (tarea T22b)
- **Antes:** el único límite de diversidad era 3 pasajes por artículo o por sección. Como una
  sentencia tiene muchas secciones (y la detección de secciones era imprecisa, ver C-04), un mismo
  documento podía ocupar los 10 puestos. En la muestra, 24 de 41 preguntas tenían más de 4 pasajes
  del mismo documento (4 con 10 de 10; p. ej. la 563 → 10 de la T-760 de 2008).
- **Ahora:** además del límite por artículo/sección, máximo `MAX_POR_DOCUMENTO=4` pasajes de un mismo
  documento. **Excepción:** si la pregunta menciona el documento (router o norma citada en la pregunta,
  p. ej. "según la Sentencia SU-455 de 2020…"), puede superar el tope. `MAX_POR_DOCUMENTO=0` desactiva.
  Además, `src.eval.recuperacion` ahora recupera exactamente igual que el pipeline (pregunta + cada
  opción en selección múltiple) y reporta el máximo de pasajes del mismo documento por pregunta.
- **Por qué:** liberar puestos de evidencia para otras normas pertinentes cuando la pregunta no es
  sobre un documento concreto.
- **Evidencia (muestra, solo recuperación, `runs/recuperacion_tope0` vs `runs/recuperacion_tope4`):**
  acierto@10 95,1 % → 95,1 %; recall de cuerpos del fundamento 87,8 % → 87,8 % (**neutro**);
  preguntas con > 4 pasajes del mismo documento 24 → 9 (las 9 mencionan ese documento). De las normas
  del fundamento aún no recuperadas, 2 no están en el corpus (SU-016/2020, SU-277/2025) y 4 están pero
  quedan fuera por ranking en ambos casos (58, 60, 679, 1073). Efecto sobre respuestas y citas:
  sin cambio visible en citas (ver «Medición conjunta» al final).
- **Archivos:** `src/retrieval/hibrido.py`, `src/config.py`, `.env.example`, `src/eval/recuperacion.py`,
  `tests/test_hibrido.py`.
- **Requiere reindexar:** no.

## C-03 · 2026-09-30 · Evidencia por opción y análisis antes de elegir en selección múltiple (tarea T22c)
- **Antes:** la pregunta y cada opción se usaban como consultas, pero todos los resultados competían
  por los mismos 10 puestos; el modelo devolvía primero la letra y luego la justificación y los
  descartes. Caso: 748 (vicio del acto administrativo; correcta A "falsa motivación", respondió D):
  la evidencia traía el CPACA (art. 46) pero no el art. 137, que enumera las causales de nulidad.
- **Ahora:** (1) `responder.recuperar_mc`: 4 puestos para la pregunta (`PUESTOS_PREGUNTA`) y el resto
  repartido por rondas entre las opciones (mejor pasaje aún no incluido de cada opción, buscando
  «pregunta + opción», reranker con 8 candidatos por opción), sin duplicados y con el tope por
  documento de C-02; cada pasaje de opción se marca en el prompt "(recuperado para la opción X)".
  (2) Esquema y prompt de MC: primero `analisis_opciones` (una frase por opción: la evidencia la
  respalda o la contradice, con [Pn]) y después `respuesta_correcta`; la gramática fuerza ese orden.
  (3) `descarte_opciones` se deriva del análisis (ya no lo escribe el modelo aparte); si falta alguna
  opción se usa la frase fija "La evidencia recuperada no respalda esta opción.". Tope MC 450 → 500 tokens.
- **Por qué:** que cada alternativa tenga evidencia propia y que el modelo contraste las opciones
  antes de elegir (en 5 de las 6 MC falladas la norma estaba en la evidencia: fallaba la elección).
- **Evidencia (recuperación, 15 MC, `runs/medicion_mc_opciones.json`):** norma del fundamento en la
  evidencia 13/15 → 13/15 (neutro); normas distintas por pregunta 15,1 → 16,0; 3,1 de 4 opciones con
  evidencia propia en promedio. **La 748 aún no trae el art. 137 del CPACA** (la opción A trajo el
  art. 5 de la Ley 678 de 2001): la pregunta es larga y domina la consulta «pregunta + opción».
  Costo: ~46 s por MC en CPU (5 búsquedas); en GPU por medir. Pruebas: 20 passed (incluida
  generación real: analiza las 4 opciones y elige la correcta). Efecto en exactitud: **9/15 → 9/15**: arregla la 748 (D → A) pero daña la 290 (C → A) (ver «Medición conjunta» al final).
- **Siguiente idea (no aplicada):** consulta por opción = texto de la opción + pocas palabras clave de
  la pregunta, en lugar de la pregunta completa.
- **Archivos:** `src/generation/responder.py`, `src/retrieval/hibrido.py` (`n_rerank`),
  `src/generation/contexto.py`, `src/generation/prompts/multiple_choice.txt`, `src/generation/citas.py`,
  `src/config.py`, `.env.example`, `tests/test_contexto.py`.
- **Requiere reindexar:** no.

## C-04 · 2026-09-30 · Detección estricta de secciones en sentencias (tarea T22d)
- **Antes:** un título de sección se reconocía si la línea (corta) **empezaba** con una palabra
  clave, sin distinguir mayúsculas y sin respetar el orden de la sentencia. Falsos positivos reales:
  en la C-355/2006, frases como "concepto del Procurador.", "concepto de vida protegido por la
  Convención[44].", "aclaración de voto basada esencialmente en…", "Salvamento de voto: Stevens)." (cita
  de un caso de EE. UU.); en la T-760/2008 el anexo posterior a la decisión ("II. Consideraciones",
  "RESUELVE") hizo que **494 fragmentos** quedaran etiquetados como RESUELVE. La etiqueta va dentro del
  texto de cada fragmento ("Sentencia … [RESUELVE]"), así que el modelo podía tomar un argumento como
  la decisión o un salvamento como la posición de la Corte.
- **Ahora:** `titulo_seccion` acepta un título solo si coincide **completo** con una sección conocida
  y está en **mayúsculas o numerado**; etiquetas normalizadas (SÍNTESIS, ANTECEDENTES, HECHOS, LA
  DEMANDA, NORMA DEMANDADA, INTERVENCIONES, CONCEPTO DEL MINISTERIO PÚBLICO, PROBLEMA JURÍDICO,
  CONSIDERACIONES, COMPETENCIA, CASO CONCRETO, DECISIÓN, RESUELVE, SALVAMENTO DE VOTO, ACLARACIÓN DE
  VOTO). `secciones_sentencia` sigue el orden del documento: un solo RESUELVE; tras la fórmula de cierre
  ("Notifíquese…", "Cópiese…", "Cúmplase…") firmas y anexos quedan **sin etiqueta**; salvamentos y
  aclaraciones solo se reconocen después del RESUELVE y sus títulos internos no cambian la sección.
  Ante la duda, sin etiqueta.
- **Por qué:** que las etiquetas que lee el modelo sean fiables, en especial RESUELVE (sentido del
  fallo) y los votos disidentes (no confundirlos con la ratio de la Corte).
- **Ajustes de T22e** (salieron del chequeo automático sobre el corpus real):
  (1) un subtítulo con numeración de varios niveles ("7.1. Decisión del juez de primera instancia",
  partido en dos líneas en la SU-455/2020) ya no abre sección: se queda en la que lo contiene;
  (2) se acepta "CONSIDERACIONES DE LA CORTE CONSTITUCIONAL" / "DE LA SALA PLENA";
  (3) un título de voto partido en dos líneas ("ACLARACIÓN DE" / "VOTO A LA SENTENCIA…") se une.
- **Evidencia:** 42 pruebas del segmentador (incluye los falsos positivos reales y el orden completo
  cuerpo → decisión → resuelve → cierre/anexo → salvamento → aclaración). Chequeo automático
  (`python -m src.corpus.secciones`) tras reconstruir el corpus:

  | Sentencia | Antes | Ahora |
  |---|---|---|
  | T-760/2008 (885 → 883 fragm.) | RESUELVE 494; "ANÁLISIS DEL CASO (“relativo a…" 221 | RESUELVE 20; COMPETENCIA 361; 500 sin etiqueta = auto 522/2015 anexo tras el "Notifíquese" |
  | C-355/2006 (1.104 → 1.101) | 13 etiquetas inventadas con frases sueltas ("CONCEPTO DE VIDA PROTEGIDO…" 86, "SALVAMENTO DE VOTO, CON LOS CUALES…" 117…) | SALVAMENTO DE VOTO 388; ACLARACIÓN DE VOTO 298; INTERVENCIONES 179; COMPETENCIA 126; 19 sin etiqueta |
  | SU-455/2020 (105) | sin parte motiva; COMPETENCIA 31; DECISIÓN 22 | CONSIDERACIONES 51; SALVAMENTO DE VOTO 19; DECISIÓN 1; RESUELVE 1 |
  | Las 107 sentencias | 64 con avisos (3 con RESUELVE > 25 %) | 26 con avisos, ninguno por RESUELVE desbordado |

  Los 26 avisos restantes son etiquetas **faltantes**, no equivocadas (sobre todo sentencias de la
  Corte Suprema, SC/SL/SP, con otros títulos): quedan sin etiqueta, que es lo conservador.
  Limitación conocida: un título de salvamento en minúsculas y sin numeración ("Salvamento Parcial
  de Voto de …") no se reconoce. Corpus: 186 documentos, 41.384 → 41.336 fragmentos; 10.496
  fragmentos con texto nuevo (los recalcula el cuaderno de Colab).
- **Archivos:** `src/corpus/segmentar.py`, `tests/test_segmentar.py`, `src/corpus/secciones.py`
  (chequeo nuevo), `tests/test_secciones.py`.
- **Requiere reindexar:** **sí** (cambia el texto de los fragmentos de sentencias; ver T22e).

## C-05 · 2026-09-30 · Consola en UTF-8 en todos los comandos (tarea T22e)
- **Antes:** en Windows, `python -m src.corpus.build` corrido a mano (sin `PYTHONIOENCODING`, que
  solo fijan `run.sh`/`run.py`) se caía con `UnicodeEncodeError` al imprimir la "→" del resumen,
  **antes de la guardia anti-fuga**: el corpus quedaba escrito pero `_fuga.json` era el de la corrida
  anterior. Pasó en las dos primeras reconstrucciones de T22e.
- **Ahora:** `src/config.py`, que todos los módulos importan, pasa `stdout`/`stderr` a UTF-8 (con
  reemplazo de lo que no se pueda mostrar) si la consola no lo está. Mismo resultado con `run.sh`,
  `run.py` o un comando suelto, en Windows, Linux o Colab.
- **Por qué:** reproducibilidad de los comandos por etapa de `docs/COMO_EJECUTAR.md`; que la guardia
  anti-fuga corra siempre.
- **Evidencia:** `src.corpus.build` sin `PYTHONIOENCODING` en la consola de Windows → código 0,
  resumen impreso y guardia ejecutada (0 graves; `_fuga.json` regenerado).
- **Archivos:** `src/config.py`.
- **Requiere reindexar:** no.


---

## Medición conjunta C-01..C-05 · 2026-09-30 · corrida `runs/muestra_t22` (Colab T4)

Los cinco cambios se midieron juntos, en un solo viaje a Colab, contra la línea base `runs/muestra_colab`.

| Componente | Línea base | C-01..C-05 | Diferencia |
|---|---:|---:|---:|
| Cerradas /20 | 12,00 (9/15) | 12,00 (9/15) | = |
| Citas /20 | 15,51 (38 aciertos) | 15,10 (37 aciertos) | −0,41 |
| Abstención /10 | 7,79 | 7,67 | −0,12 |
| RAGAS /30 | 13,37 (0,4456) | 12,62 (0,4208) | −0,75 |
| **Total /80** | **48,67** | **47,39** | **−1,28** |
| s por pregunta | 34,9 (máx 163) | 31,7 (máx 81) | −3,2 |

- **Lo que se ganó:** 748 en MC (C-03); 247 responde en lugar de abstenerse (C-01); 0 citas sin respaldo
  y 0 errores de esquema se mantienen; generación más rápida y sin colas largas.
- **Lo que se perdió:** 290 en MC: con el análisis previo de C-03 el modelo leyó bien que [P1] fija
  4 meses y aun así marcó C como "la contradice" y eligió A (2 años). Citas de la 748 y la 879 (la 879
  cita solo el Código Civil, no el CGP: variación del modelo con otra evidencia).
- **RAGAS (−0,025):** sin atribución posible, el reporte no da puntaje por pregunta y la longitud de
  las respuestas no cambió; puede ser ruido del juez (no medido).
- **Conclusión:** neutro con leve baja, dentro de lo que podría ser ruido. Ningún cambio se revierte
  todavía: los efectos en los casos objetivo se cumplieron. Candidato a revisar: el formato
  "analizar antes de elegir" en MC (C-03 parte 2), comparando con elegir primero sobre la misma
  evidencia por opción.

## C-06 · 2026-09-30 · Selección múltiple: elegir primero, con la evidencia por opción (experimento)
- **Antes (C-03):** el esquema obligaba a escribir primero `analisis_opciones` (una frase por opción,
  "la respalda / la contradice") y después la letra. En `runs/muestra_t22` arregló la 748 pero dañó la
  290: el modelo escribió que [P1] fija 4 meses y aun así marcó la opción C (4 meses) como "la
  contradice" y eligió A (2 años).
- **Ahora:** `MC_ANALISIS_PREVIO=0` (por defecto): primero `respuesta_correcta`, luego `justificacion`
  y `descarte_opciones` (una frase por cada otra letra), como en la línea base, **conservando la
  evidencia por opción de C-03** (pasajes marcados "(recuperado para la opción X)"). Plantilla
  `prompts/multiple_choice_elegir.txt`. `MC_ANALISIS_PREVIO=1` vuelve al formato de C-03. La caché del
  decoder distingue ambas variantes (el esquema y el prompt forman parte de la clave).
- **Por qué:** separar el efecto de la evidencia por opción (recuperación) del efecto del formato de
  salida (razonamiento), que en un modelo de 8B puede introducir contradicciones.
- **Cómo se mide:** solo cambia selección múltiple ⇒ en Colab se responden las 15 MC (`IDS` en el
  cuaderno) y se combinan con las 35 de texto libre de `runs/muestra_t22`
  (`python -m src.eval.combinar`); evaluador sin juez (RAGAS no cambia: mismas respuestas de texto).
- **Evidencia (`runs/muestra_v2`, junto con el corpus v2):** MC 9/15, igual que t22 y la línea base,
  pero con otro reparto: recupera la 290 y mantiene la 748; pierde la 487 (A → D) con exactamente la
  misma evidencia que en t22, así que esa pérdida es del formato. Conclusión: ningún formato domina;
  la elección en MC del modelo de 8B varía ±1 pregunta según el formato. Se deja C-06 por defecto
  (total 49,64/80, el mejor; los demás componentes subieron con el corpus).
- **Evidencia preliminar (CPU local, `runs/mc_elegir_local`):** 290 → **C** (correcta; descarta A como
  "plazo para demandar") y 748 → **A** (correcta): las dos aciertan. 20 pruebas de contexto pasan, incluida
  la generación real. Medición de las 15 MC: pendiente de Colab.
- **Archivos:** `src/config.py`, `.env.example`, `src/generation/contexto.py`,
  `src/generation/prompts/multiple_choice_elegir.txt`, `src/generation/responder.py`,
  `src/pipeline/main.py`, `src/eval/combinar.py` (nuevo), `notebooks/muestra_en_colab.ipynb` (`IDS`),
  `tests/test_contexto.py`, `tests/test_combinar.py`.
- **Requiere reindexar:** no.

## C-07 · 2026-10-01 · Selección múltiple: buscar cada opción por sí misma (opción + palabras clave)
- **Antes (C-03):** la evidencia de cada opción se buscaba con «pregunta completa + opción». En
  preguntas largas la pregunta dominaba la consulta y la opción casi no pesaba, ni en BM25 ni en el
  encoder: en la 748 (63 palabras) la opción «Falsa motivación» nunca trajo el art. 137 del CPACA.
- **Ahora:** `MC_CONSULTA_OPCION=clave` (por defecto): la consulta de cada opción es **el texto de
  la opción seguido de hasta `MC_PALABRAS_CLAVE=10` palabras clave de la pregunta**. Las palabras
  clave son las más raras del corpus (menor frecuencia documental en el índice BM25, nuevo
  `IndiceBM25.frecuencia`), conservando su orden; se descartan las palabras vacías de BM25 y las que
  solo plantean la pregunta ("lea", "responda", "siguiente", "correcta"…). Ejemplos:
  748 → «Falsa motivación 368 2014 Ambiente Sostenible relleno sanitario pueblos indígenas consulta
  vicio»; 290 → «4 meses pactar plazo liquidación bilateral contrato Estatal sometido Estatuto
  contratación supletorio». La búsqueda de la pregunta sola (4 puestos), el reparto por rondas y
  las marcas «(recuperado para la opción X)» no cambian. `MC_CONSULTA_OPCION=pregunta` vuelve a C-03.
- **Por qué:** que BM25 y el encoder busquen lo que distingue a cada opción sin perder el tema
  (la opción sola no sirve cuando es corta: «2 meses»).
- **Evidencia (`runs/muestra_v3`, Kaggle, junto con el corpus v3):** MC 9/15 otra vez: gana la 58
  (B → A) y pierde la 748 (A → D). Sin efecto neto en exactitud; el total cayó a 46,22/80 por
  RAGAS y citas en texto libre, que C-07 no toca (solo cambia la búsqueda de MC).
- **Archivos:** `src/generation/responder.py` (`palabras_clave`, `consulta_opcion`,
  `consultas_extra`, `recuperar_mc`), `src/index/lexico.py` (`frecuencia`), `src/config.py`,
  `.env.example`, `tests/test_contexto.py`, `tests/test_hibrido.py`.
- **Requiere reindexar:** no.

## C-08 · 2026-10-01 · Selección múltiple: responder en abierto y luego elegir la opción (experimento)
- **Antes (C-06/C-07):** el modelo veía las opciones desde el principio y elegía la letra. En tres
  corridas seguidas el resultado fue 9/15 con distintas preguntas acertadas: con la misma evidencia,
  la letra cambiaba según cómo se presentaban las opciones (487 con evidencia idéntica en t22 y v2;
  748 y 58 entre v2 y v3).
- **Ahora:** `MC_MODO=abierta` (por defecto), dos llamadas al decoder:
  (1) responde la pregunta **sin ver las opciones**, con la evidencia sin marcas de opción
  (`prompts/multiple_choice_abierta.txt`, esquema `respuesta` + `pasajes_usados`, 350 tokens);
  (2) con esa respuesta preliminar, la evidencia (con sus marcas) y las opciones, elige la letra
  (`prompts/multiple_choice_desde_abierta.txt`, esquema de "elegir primero"; si la respuesta
  preliminar contradice la evidencia, prima la evidencia). La traza guarda la respuesta abierta y
  la opción más parecida a ella según bge-m3 (`opcion_por_similitud`, solo diagnóstico), para
  comparar "elegir por similitud" sin otra corrida. `MC_MODO=directo` vuelve a una sola llamada.
- **Por qué:** que el modelo razone la respuesta sin que las opciones lo arrastren y luego la
  contraste con ellas.
- **Costo:** una llamada más por pregunta de selección múltiple (el paso 1 es corto).
- **Cómo se mide:** solo cambia MC ⇒ en Kaggle `RANGO = "1 15"` (las 15 MC de la muestra, mismo
  corpus v3 y misma recuperación que `runs/muestra_v3`), combinadas en local con las 35 de texto
  libre de `muestra_v3` (`python -m src.eval.combinar`) y evaluador sin juez.
- **Evidencia (`runs/mc_abierta`, Kaggle T4; combinada con el texto libre de `muestra_v3` en
  `runs/mc_abierta_50`):** **MC 10/15** (primera vez por encima de 9; base, v2 y v3: 9/15). Frente a
  v3, con el mismo corpus y la misma recuperación: gana la 487 (D → A) y no pierde ninguna. Citas
  37 → 38 aciertos (15,51); abstención 7,91; **sin juez 36,75/50** (v3: 34,77; v2: 35,83). Elegir por
  similitud con bge-m3 habría acertado solo 4/15 ⇒ la elección debe hacerla el modelo. Fallan 128,
  528 (la respuesta abierta calcula mal la cuantía: 30 millones no supera 150 SMLMV), 647, 671 y 748
  (la evidencia sigue sin el art. 137 del CPACA y la respuesta abierta habla de "irregularidad del
  proceso"). Costo: 51,9 s por MC en T4 (antes ~33 s).
- **Archivos:** `src/generation/responder.py` (`generar_respuesta`, `opcion_por_similitud`,
  `mensajes_que_caben`), `src/generation/contexto.py` (`etapa`, `esquema_mc_abierta`, `MAX_TOKENS`),
  `src/generation/prompts/multiple_choice_abierta.txt`, `multiple_choice_desde_abierta.txt`,
  `src/pipeline/main.py`, `src/config.py`, `.env.example`, `tests/test_contexto.py`, cuadernos.
- **Requiere reindexar:** no.
- **Decisión (2026-10-01, usuario):** se descarta por costo/beneficio (+1 de 15 con casi el doble
  de latencia en MC). `MC_MODO=directo` vuelve a ser el valor por defecto; el código queda.

## C-09 · 2026-10-01 · Selección múltiple con el modo de razonamiento de Qwen3 (experimento)
- **Antes:** Qwen3 siempre con `/no_think` y la gramática JSON desde el primer token: el modelo
  elegía la letra sin razonar. Caso 528: con el art. 25 del CGP en la evidencia, dijo "mayor
  cuantía" para 30 millones (mínima cuantía es hasta 40 SMLMV).
- **Ahora:** en selección múltiple, `MC_RAZONAMIENTO_TOKENS=1024` (0 lo apaga): Qwen3 razona en
  `<think>…</think>` con ese tope y luego escribe el JSON de "elegir primero" con la gramática. En
  llama.cpp son dos tramos sobre el mismo prompt ChatML: (1) sin gramática hasta `</think>` o el
  tope; (2) con el razonamiento cerrado y la gramática; llama.cpp reutiliza el prefijo evaluado, así
  que el tramo 2 no relee la evidencia. Al decidir cuántos pasajes caben se reserva el tope de
  razonamiento. El razonamiento queda en la traza. Temperatura 0 y semilla fija: determinista.
  Las reglas del reto no lo prohíben (modelo abierto ≤ 8B, temperatura 0, determinista); la
  restricción es el tiempo (~22 s por pregunta en promedio con una máquina).
- **Por qué:** en 3 de las 5 MC falladas el problema es de razonamiento sobre evidencia correcta.
- **Cómo se mide:** Kaggle `RANGO = "1 15"`, mismo corpus v3 y misma recuperación que
  `runs/muestra_v3` y `runs/mc_abierta`; combinar con el texto libre de `muestra_v3`.
- **Evidencia:** pendiente.
- **Archivos:** `src/generation/llm.py` (`razonamiento_tokens`, `_generar_razonando`,
  `Generacion.razonamiento`), `src/generation/responder.py`, `src/config.py`, `.env.example`,
  cuadernos.
- **Requiere reindexar:** no.

## C-10 · 2026-10-01 · Documentos complementarios: máximo 2 de los 10 pasajes
- **Antes:** las 100 leyes y decretos del corpus v3 competían en igualdad con el resto. En
  `runs/muestra_v3` entraron en la evidencia de 19 de 35 preguntas de texto libre (en la 1073, 5 de
  10 pasajes), sobre todo los decretos únicos reglamentarios (1074/2015, 2555/2010, 1069/2015,
  1072/2015, 780/2016); total 49,64 → 46,22/80 (RAGAS 0,4605 → 0,3815), aunque las normas de
  referencia seguían en la evidencia (44/49 → 42/49).
- **Ahora:** `config/documentos_complementarios.txt` (versionado en el repositorio, no en
  `fuentes.csv`) lista esas 100 fuentes; como máximo `MAX_COMPLEMENTARIOS=2` pasajes de ellas entre
  los 10, en la búsqueda normal y en la evidencia por opción de selección múltiple. Excepción: los
  documentos que la pregunta menciona (router o norma citada) no cuentan para el tope. `0` = sin
  tope; quitar una línea de la lista = documento principal.
- **Por qué:** conservar lo que aportan (p. ej. la 58 de MC) sin que desplacen a las normas
  principales. Decisión del usuario: no medir antes la variación del juez de RAGAS.
- **Evidencia:** pendiente (corrida completa de las 50 con el corpus v3).
- **Archivos:** `config/documentos_complementarios.txt` (nuevo), `src/retrieval/hibrido.py`
  (`leer_complementarios`, tope en `buscar`), `src/generation/responder.py` (`recuperar_mc`),
  `src/config.py`, `.env.example`, `tests/test_hibrido.py`.
- **Requiere reindexar:** no.

### Corrección (2026-10-01, tras `runs/muestra_v4`)
La premisa de C-10 era errónea: la caída de RAGAS de v3 (0,4605 → 0,3815) se debió a que el juez
no devolvió veredicto en 6 de 33 respuestas (cuentan como cero; v2: 0 fallos). Sobre las respuestas
con veredicto, v3 promedia 0,495 frente a 0,488 de v2. En v4 el juez falló en 21 de 33 (RAGAS
oficial 0,1744; 0,509 sobre las 12 calificadas). C-09 en v4: MC 10/15 (gana 487 y 528, pierde 58),
63 s por MC, citas en MC más escasas (358 pierde su norma). C-10 en v4: 879 pierde su cita, 253 una
de tres. Decisión de C-09 y C-10 pendiente de recalificar con RAGAS.

## C-11 · 2026-10-01 · Respuestas abiertas más cortas (máximo ~200 palabras)
- **Antes (C-01):** las abiertas sumaban 196 a 323 palabras entre los cuatro campos (análisis de 5 a
  8 oraciones). El juez de RAGAS descompone la respuesta en afirmaciones: más largo = más llamadas y
  más riesgo de `TimeoutError`. En la recalificación de v4 fallaron 7 de 33 (5 timeouts, 2 cortes de
  conexión); una de ellas, la abierta de 323 palabras (679). Las respuestas de referencia promedian
  ~107 palabras.
- **Ahora:** `prompts/open_ended.txt` pide máximo 200 palabras en total: marco normativo (hasta 5
  normas, frase muy breve cada una), análisis de 3 o 4 oraciones, hasta 2 sentencias y conclusión de
  una oración. `MAX_TOKENS` de abiertas sigue en 1400 para no truncar.
- **Por qué:** menos riesgo de que el juez agote su tiempo (cuenta como 0) y respuestas más cercanas
  al tamaño de las de referencia. Los fallos de red del juez no dependen de nosotros.
- **Evidencia:** pendiente (`muestra_v5`: igual que v4 salvo este cambio).
- **Archivos:** `src/generation/prompts/open_ended.txt`.
- **Requiere reindexar:** no.
- **Evidencia (`runs/muestra_v6`, paquete 9141cc86a064):** solo cambiaron las 4 abiertas
  respondidas; el resto, idéntico a v4. Pero **no se acortaron** (196–323 → 212–293 palabras): el
  modelo sí escribe menos (430–610 tokens de salida), y el largo lo pone nuestro postproceso, que
  agrega al marco normativo "Normas aplicables: …" con hasta 6 normas de la evidencia que el modelo
  no citó (40–60 palabras). Citas 34 → 35. El juez volvió a fallar en 7 de 33 (red); sobre las
  calificadas, 0,495.

## C-12 · 2026-10-01 · Arreglo: el filtro de citas corrompía el texto con citas solapadas
- **Antes:** `_quitar_spans` reemplazaba cada cita sin respaldo por "la normativa aplicable" de
  derecha a izquierda, pero con tramos solapados (un código dentro de una cita más larga, o la
  extensión hacia "el artículo 5 del…") el segundo reemplazo cortaba el texto ya modificado. Caso
  679 en `muestra_v6`: el marco normativo empezaba "la normativa aplicla normativa aplicablembia…".
  Ese texto lo lee el juez de RAGAS.
- **Ahora:** se calculan los tramos finales sobre el texto original, se unen los que se solapan y
  luego se reemplazan. Mismo criterio de qué se elimina; solo cambia que el texto queda legible.
- **Evidencia:** comprobado sobre el caso ("Artículo 49 de la Constitución Política de Colombia…" →
  un solo reemplazo, resto intacto). Prueba `test_citas_solapadas_no_corrompen_el_texto` (sin
  correr: el usuario pide que se le pregunte antes).
- **Archivos:** `src/generation/citas.py`, `tests/test_citas.py`.
- **Requiere reindexar:** no.
