# Reporte de avance — Hackathon 2026

**Equipo:** <nombre del equipo>
**Integrantes:** <nombre 1> · <nombre 2> · <nombre 3>
**Fecha de la medición:** 2026-09-29

<!-- Enviar como REPORTE_AVANCE.pdf (una página) a rf.manrique@uniandes.edu.co,
asunto "[Hackathon 2026] Avance — <nombre del equipo>", antes del viernes 2 de octubre
a las 17:00. Si se mejora el puntaje antes del viernes, actualizar las tablas. -->

---

## 1. Puntaje sobre las preguntas de muestra

Resultado de `python scripts/evaluate.py --submission runs/muestra_colab/submissions.jsonl --split sample [--ragas]`.

| Componente | Puntos obtenidos | Puntos posibles |
|---|---:|---:|
| Exactitud en cerradas (9 de 15; 0,600) | 12,00 | 20 |
| Calidad de citación (recall ponderado 0,776; 0 citas sin respaldo) | 15,51 | 20 |
| Abstención calibrada (0,779) | 7,79 | 10 |
| **Total automático sin RAGAS** | **35,30** | **50** |
| Corrección en texto libre — RAGAS (0,4456; referencia GPT-5.4: 0,451) | 13,37 | 30 |
| **Total automático con RAGAS** | **48,67** | **80** |

Observaciones: ninguna norma citada carece de respaldo en la evidencia recuperada (0 de
139 citas). En texto libre la corrección ya iguala la referencia del mejor modelo del
estudio. En 26 de 28 preguntas de texto libre la recuperación trae una norma del
fundamento; en 5 de las 6 cerradas falladas la norma de referencia sí estaba en la
evidencia, por lo que el margen de mejora está en el razonamiento sobre las opciones.

## 2. Estado del corpus

| Métrica | Valor |
|---|---|
| Documentos incorporados | 186 (1 Constitución, 14 códigos, 52 leyes, 10 decretos, 2 decisiones andinas, 107 sentencias) |
| Fragmentos indexados | 41.384 (por artículo; sentencias por secciones) |
| Áreas del banco con cobertura | Las 10: constitucional (47 docs), familia (32), laboral (29), administrativo (27), civil (26), penal (21), procesal (21), comercial (21), mercados (19), tributario (17) |
| Áreas del banco sin cobertura | Ninguna |
| Cobertura del listado inicial (seed) | 519 de 559 ítems (93 %) |

Fuentes consultadas: Gestor Normativo de la Función Pública (76 documentos), relatoría de
la Corte Constitucional (93), relatoría de la Corte Suprema de Justicia (14), Secretaría
General de la Comunidad Andina (2) y Normograma de la Cancillería (1). Los 186 documentos
se verificaron automáticamente contra su URL oficial: 184 coinciden al 100 %; los otros
dos son un PDF escaneado transcrito con OCR local y un `.doc` oficial convertido.

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
