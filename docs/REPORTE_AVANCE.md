# Reporte de avance — Hackathon 2026

**Equipo:** Los PoliTICos
**Integrantes:** Juan José Cortés Villamil · Pablo Medina Forero · Miguel Santiago Roa Vallejo
**Fecha:** 2 de octubre de 2026  
**Repositorio:** https://github.com/juan-jose-cortes1234/AIWeekHackaton

## 1. Puntaje sobre las preguntas de muestra

Evaluador oficial (`scripts/evaluate.py --ragas`), GPU T4, juez sin fallos, sistema de entrega.

| Componente | Puntos | Posibles |
|---|---:|---:|
| Exactitud en cerradas (11 de 15) | 14,67 | 20 |
| Calidad de citación (recall 0,816; 0 citas sin respaldo) | 16,33 | 20 |
| Abstención calibrada (0,837) | 8,37 | 10 |
| Corrección en texto libre — RAGAS (0,4572; referencia 0,451) | 13,72 | 30 |
| **Total automático** | **53,09** | **80** |

Evolución: línea base 48,67 → 53,09. Ninguna norma citada carece de respaldo en la evidencia;
las normas del fundamento de referencia llegan a la evidencia en 46 de 49 casos. En las 50
preguntas de muestra, RAGAS alcanza 0,4572, por encima del valor de referencia 0,451; los conjuntos
evaluados son distintos. Con el umbral de abstención de 0,025 (ver §3) ninguna pregunta de la
muestra queda sin fundamento suficiente, por lo que no hubo abstenciones.

## 2. Estado del corpus

| Métrica | Valor |
|---|---|
| Documentos | 650: Constitución, 14 códigos, 149 leyes (16 convenios de doble imposición), 40 decretos, 30 resoluciones, 11 circulares, 2 decisiones andinas, 141 sentencias, 262 conceptos (DIAN, SIC, Supersociedades) |
| Fragmentos indexados | 77.014: 47.340 de artículos, 23.472 de secciones, 1.212 de preámbulos y 4.990 de notas |
| Áreas del banco cubiertas | Las 10 (de 43 documentos en penal a 252 en tributario) |
| Cobertura del listado inicial (seed) | 98 %–100 % de los ítems por área |


## 3. Arquitectura actual

| Componente | Elección |
|---|---|
| Encoder | `BAAI/bge-m3` (MIT) |
| Decoder | `google/gemma-4-E4B-it` (Apache-2.0, 7.996.156.490 parámetros), GGUF Q8_0 con su plantilla de chat, temperatura 0 |
| Recuperación | Router de artículos citados + BM25 jurídico + denso (FAISS exacto), fusión RRF, reranker `bge-reranker-v2-m3`, cupo de 4 normas en los 10 pasajes, evidencia por opción en selección múltiple |
| Segmentación | Por artículo y por secciones en sentencias y conceptos, con subdivisión de textos extensos e inclusión de preámbulos y notas; cada fragmento lleva el encabezado canónico de su norma |
| Abstención | En texto libre, `abstencion: true` cuando el corpus no da fundamento suficiente (ningún pasaje supera 0,025 de pertinencia según el reranker y la pregunta no cita una norma del corpus) o el modelo no produce una respuesta utilizable; en selección múltiple siempre se elige una opción |

## 4. Riesgos identificados

1. **Exactitud en cerradas (73 %):** el modelo de 8B elige distinto según cómo se le presentan
   las opciones, aun con la norma en la evidencia; seguimos trabajando la selección de evidencia.
2. **Tiempo de cómputo:** ~40 s por pregunta en una T4 (992 ≈ 11 h de cómputo). Plan: 6 equipos
   en paralelo —3 de la sala Turing y 3 portátiles con Colab—, un rango de ~165 preguntas cada uno
   (`run.py --rango INICIO FIN`), ≈ 2 h. Riesgos: la ejecución por consola aún no se ha ensayado en
   Turing (ensayo previsto antes del sábado) y Colab puede negar GPU por cuota (respaldo: Kaggle).
3. **Posibles inconsistencias en las claves de la muestra, pendientes de verificación:** en la
   pregunta 58 la opción correcta dice «Ley 1564 de 2002», mientras que el Código General del
   Proceso es la Ley 1564 de 2012; en la 128 la clave incluye a las Fintech, que el Decreto 2555 de
   2010 no menciona entre quienes pueden celebrar leasing financiero.
