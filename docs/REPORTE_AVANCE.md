# Reporte de avance — Hackathon 2026

**Equipo:** Los PoliTICos
**Integrantes:** Juan José Cortés Villamil · Pablo Medina Forero · Miguel Santiago Roa Vallejo
**Fecha:** 2 de octubre de 2026

## 1. Puntaje sobre las preguntas de muestra

Evaluador oficial (`scripts/evaluate.py --ragas`), GPU T4, juez sin fallos (corrida `muestra_v12`).

| Componente | Puntos | Posibles |
|---|---:|---:|
| Exactitud en cerradas (11 de 15) | 14,67 | 20 |
| Calidad de citación (recall 0,816; 0 citas sin respaldo) | 16,33 | 20 |
| Abstención calibrada (0,837) | 8,37 | 10 |
| Corrección en texto libre — RAGAS (0,4572; referencia 0,451) | 13,72 | 30 |
| **Total automático** | **53,09** | **80** |

Evolución: línea base 48,67 → 53,09. Ninguna norma citada carece de respaldo en la evidencia;
las normas del fundamento de referencia llegan a la evidencia en 46 de 49 casos. En texto libre
la corrección supera la referencia del estudio (0,451).

## 2. Estado del corpus

| Métrica | Valor |
|---|---|
| Documentos | 650: Constitución, 14 códigos, 149 leyes (16 convenios de doble imposición), 40 decretos, 30 resoluciones, 11 circulares, 2 decisiones andinas, 141 sentencias, 262 conceptos (DIAN, SIC, Supersociedades) |
| Fragmentos indexados | 77.014 (por artículo; sentencias por secciones) |
| Áreas del banco cubiertas | Las 10 (de 43 documentos en penal a 252 en tributario) |
| Cobertura del listado inicial (seed) | 98 %–100 % de los ítems por área |


## 3. Arquitectura actual

| Componente | Elección |
|---|---|
| Encoder | `BAAI/bge-m3` (MIT) |
| Decoder | `google/gemma-4-E4B-it` (Apache-2.0, 7.996.156.490 parámetros), GGUF Q8_0 con su plantilla de chat, temperatura 0 |
| Recuperación | Router de artículos citados + BM25 jurídico + denso (FAISS exacto), fusión RRF, reranker `bge-reranker-v2-m3`, cupo de 4 normas en los 10 pasajes, evidencia por opción en selección múltiple |
| Segmentación | Por artículo con encabezado canónico de la norma; sentencias por secciones |
| Abstención | Solo si el modelo no produce una respuesta utilizable (con los pesos oficiales, responder suma más) |

## 4. Riesgos identificados

1. **Exactitud en cerradas (73 %):** el modelo de 8B elige distinto según cómo se le presentan
   las opciones, aun con la norma en la evidencia; seguimos trabajando la selección de evidencia.
2. **Tiempo de cómputo:** ~40 s por pregunta en una T4 (992 ≈ 11 h); el banco se repartirá por
   rangos entre varias GPU de la sala Turing (`run.py --rango`).
3. **Claves discutibles en la muestra:** 2 de las 4 preguntas de selección múltiple falladas tienen
   una clave con errata o más amplia que la norma.
