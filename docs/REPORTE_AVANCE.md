# Reporte de avance — Hackathon 2026

**Equipo:** Los PoliTICos
**Integrantes:** Juan José Cortés Villamil · Pablo Medina Forero · Miguel Santiago Roa Vallejo
**Fecha:** 2 de octubre de 2026

## 1. Puntaje sobre las preguntas de muestra

Evaluador oficial (`scripts/evaluate.py --ragas`), GPU T4, juez sin fallos.

| Componente | Mejor corrida (1-oct) | Sistema actual (2-oct) | Posibles |
|---|---:|---:|---:|
| Exactitud en cerradas | 12,00 (9/15) | 12,00 (9/15) | 20 |
| Calidad de citación (0 citas sin respaldo) | 15,92 | 15,92 | 20 |
| Abstención calibrada | 7,91 | 7,67 | 10 |
| Corrección en texto libre — RAGAS | 13,81 (0,4605) | 13,00 (0,4335) | 30 |
| **Total automático** | **49,64** | **48,59** | **80** |

La mejor corrida usó Qwen3-8B y un corpus de 238 documentos; el sistema actual usa Gemma 4 E4B
y 618 documentos. Ninguna norma citada carece de respaldo en la evidencia. En texto libre la
corrección iguala la referencia del estudio (0,451). Las normas del fundamento de referencia llegan
a la evidencia en 44 de 49 casos.

## 2. Estado del corpus

| Métrica | Valor |
|---|---|
| Documentos | 618: Constitución, 14 códigos, 132 leyes, 31 decretos, 27 resoluciones, 11 circulares, 2 decisiones andinas, 138 sentencias, 262 conceptos (DIAN, SIC, Supersociedades) |
| Fragmentos indexados | 75.204 (por artículo; sentencias por secciones) |
| Áreas del banco cubiertas | Las 10 (de 43 documentos en penal a 232 en tributario) |
| Cobertura del listado inicial (seed) | 98 %–100 % de los ítems por área |

Fuentes: Función Pública, relatorías de la Corte Constitucional, la Corte Suprema y el Consejo
de Estado, normogramas de la DIAN, la Cancillería, Colpensiones y MinTIC, SIC, Supersociedades,
Bogotá Jurídica y la Secretaría General de la Comunidad Andina.

## 3. Arquitectura actual

| Componente | Elección |
|---|---|
| Encoder | `BAAI/bge-m3` (MIT) |
| Decoder | `google/gemma-4-E4B-it` (Apache-2.0, 7.996.156.490 parámetros), GGUF Q8_0, temperatura 0 |
| Recuperación | Router de artículos citados + BM25 jurídico + denso (FAISS exacto), fusión RRF, reranker `bge-reranker-v2-m3`, cupo de 4 normas en los 10 pasajes, evidencia por opción en selección múltiple |
| Segmentación | Por artículo con encabezado canónico de la norma; sentencias por secciones |
| Abstención | Solo si el modelo no produce una respuesta utilizable (con los pesos oficiales, responder suma más) |

## 4. Riesgos identificados

1. **Exactitud en cerradas (60 %):** el modelo de 8B elige distinto según cómo se le presentan
   las opciones, aun con la norma en la evidencia; seguimos trabajando la selección de evidencia.
2. **Tiempo de cómputo:** ~39 s por pregunta en una T4 (992 ≈ 11 h); el banco se repartirá por
   rangos entre varias GPU de la sala Turing (`run.py --rango`).
3. **Normas aún ausentes:** p. ej. los decretos de salario mínimo (cuantías) y los convenios para
   evitar la doble imposición.
