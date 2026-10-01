# Reporte de avance — Hackathon 2026

**Equipo:** <nombre del equipo>
**Integrantes:** <nombre 1> · <nombre 2> · <nombre 3>
**Fecha de la medición:** 2026-09-29

<!-- Enviar como REPORTE_AVANCE.pdf (una página) a rf.manrique@uniandes.edu.co,
asunto "[Hackathon 2026] Avance — <nombre del equipo>", antes del viernes 2 de octubre
a las 17:00. Si se mejora el puntaje antes del viernes, actualizar las tablas. -->

---

## 1. Puntaje sobre las preguntas de muestra

Resultado de `python scripts/evaluate.py --submission runs/muestra_v2/submissions.jsonl --split sample [--ragas]`
(corrida del 1 de octubre en una GPU T4; la línea base del 29 de septiembre fue 48,67/80).

| Componente | Puntos obtenidos | Puntos posibles |
|---|---:|---:|
| Exactitud en cerradas (9 de 15; 0,600) | 12,00 | 20 |
| Calidad de citación (recall ponderado 0,796; 0 citas sin respaldo) | 15,92 | 20 |
| Abstención calibrada (0,791) | 7,91 | 10 |
| **Total automático sin RAGAS** | **35,83** | **50** |
| Corrección en texto libre — RAGAS (0,4605; referencia GPT-5.4: 0,451) | 13,81 | 30 |
| **Total automático con RAGAS** | **49,64** | **80** |

Observaciones: ninguna norma citada carece de respaldo en la evidencia recuperada (0 de
152 citas). En texto libre la corrección supera la referencia del mejor modelo del estudio
(0,4605 frente a 0,451). La ampliación del corpus aportó evidencia en 22 de las 50
preguntas. En cerradas el resultado se mantiene en 9 de 15 con distintos formatos de
salida, pero cambian las preguntas acertadas: con la misma evidencia el modelo de 8B
elige distinto según el formato, por lo que el margen de mejora está en el razonamiento
sobre las opciones más que en la recuperación.

## 2. Estado del corpus

| Métrica | Valor |
|---|---|
| Documentos incorporados | 238 (1 Constitución, 14 códigos, 52 leyes, 11 decretos, 1 resolución, 2 decisiones andinas, 138 sentencias, 19 conceptos DIAN, SIC y Consejo de Estado) |
| Fragmentos indexados | 45.201 (por artículo; sentencias por secciones) |
| Áreas del banco con cobertura | Las 10: constitucional (65 docs), administrativo (35), laboral (35), familia (33), mercados (31), civil (30), tributario (29), penal (28), procesal (27), comercial (23) |
| Áreas del banco sin cobertura | Ninguna |
| Cobertura del listado inicial (seed) | Entre 96 % y 99 % de los ítems por área (ver `CORPUS.md`) |

Fuentes consultadas: Gestor Normativo de la Función Pública (76 documentos), relatoría de
la Corte Constitucional (111), relatoría de la Corte Suprema de Justicia (27), Normograma
DIAN (12), Superintendencia de Industria y Comercio (8), Secretaría General de la
Comunidad Andina (2), Consejo de Estado (1) y Normograma de la Cancillería (1). Los 186
documentos iniciales se verificaron automáticamente contra su URL oficial: 184 coinciden
al 100 %; los otros dos son un PDF escaneado transcrito con OCR local y un `.doc` oficial
convertido. Los 52 incorporados el 30 de septiembre se revisaron por contenido (documento
oficial completo, con su número); la verificación contra la URL está pendiente.

## 3. Arquitectura actual

| Componente | Elección |
|---|---|
| Encoder | `BAAI/bge-m3` (MIT) |
| Decoder | `Qwen/Qwen3-8B` (Apache-2.0), GGUF 4 bits con llama.cpp, temperatura 0, sin modo de razonamiento |
| Estrategia de recuperación | Híbrida: router de artículos citados + BM25 jurídico + denso (FAISS exacto), fusión RRF, reranker `bge-reranker-v2-m3`, 10 pasajes |
| Segmentación del corpus | Por artículo con encabezado canónico de la norma; sentencias por secciones con 15 % de solape |
| Mecanismo de abstención | Nunca en selección múltiple; en texto libre solo sin evidencia pertinente o sin respuesta utilizable |

## 4. Riesgos identificados

1. **Tiempo de cómputo:** en una GPU T4 cada pregunta tarda ~35 s (992 ≈ 9,6 h). Plan:
   repartir las preguntas entre 2 o más GPU (sala Turing / Colab) y acortar la generación.
2. **Exactitud en cerradas (60 %):** el modelo elige mal aunque tenga la norma; se
   trabajará el prompt de selección múltiple y la selección de evidencia.
3. **Respuestas abiertas truncadas:** una respuesta abierta superó el límite de salida y
   se registró como abstención; se ajustará el límite y el formato.
