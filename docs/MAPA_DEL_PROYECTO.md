# Mapa del proyecto

Qué hay en cada documento y carpeta del repositorio, para revisarlo en equipo.

**Estado:** el flujo está completo de punta a punta (corpus → índice → recuperación
→ generación → citas → abstención → `submissions.jsonl` → evaluador) y ya corrió
entero, incluso en un contenedor Docker limpio. Falta alimentarlo con el corpus
real y medirlo en GPU.

---

## 1. Para empezar (léanlos primero)

| Archivo | Qué encuentran |
|---|---|
| **`README.md`** | La puerta de entrada: cómo reproducir todo con un comando, requisitos de hardware, arquitectura con el motivo de cada elección, comandos por etapa, interfaz y limitaciones. Tiene marcadores `<…>` por llenar: nombre del equipo, integrantes, enlace del corpus y puntajes. |
| **`GUIA_CORPUS.md`** | **La guía para construir el corpus**, la tarea central del equipo: qué normas descargar por prioridad (nivel 1, 2 y 3 por área), cómo organizar la carpeta de OneDrive, el formato de `fuentes.csv`, consejos de descarga (Senado, SUIN, relatorías) y controles de calidad. |
| **`docs/BRECHAS.md`** | Lista automática de las normas que **faltan** en el corpus, ordenadas por cuántas preguntas del banco dependen de ellas. Se regenera con `python -m src.eval.brechas`. |
| **`docs/fuentes.ejemplo.csv`** | Plantilla de `fuentes.csv` con una fila de ejemplo. |

## 2. Entregables del reto

| Archivo | Qué es | Estado |
|---|---|---|
| `CORPUS.md` | Bitácora del corpus (vale 5 puntos). Las tablas de inventario y cobertura se llenan solas; la sección "Método" ya está redactada | Falta la prosa de "Criterio" y "Lectura de la curva" (marcada `BORRADOR`) |
| `corpus_manifest.json` | Manifiesto del corpus | Se genera con `python -m src.corpus.manifest` cuando haya corpus |
| `informe/INFORME_TECNICO.md` | Borrador del informe técnico (≤ 3 páginas) | Faltan puntajes y análisis de errores; se exporta a PDF |
| `docs/REPORTE_AVANCE.md` | Borrador del reporte del **viernes 17:00** | Faltan el puntaje de la muestra y el estado del corpus |
| `docs/RUNBOOK_SABADO.md` | **Guía paso a paso del sábado**: preparación previa, ejecución de las 992 preguntas, plan B con varias máquinas, checklist de cierre y verificación en vivo | Completo; tiene casillas para anotar hash y tiempos |
| `interfaz/` | Interfaz gráfica (vale 10 puntos): `python -m interfaz.app` → http://localhost:8000 | Funciona; confirmar la paleta de Software Colombia |
| `LICENSE` | Licencia del código (Apache-2.0) | — |

## 3. El código (`src/`), en el orden en que corre

| Carpeta | Qué hace |
|---|---|
| `src/config.py` | Toda la configuración sale de `.env`. Incluye la **lista blanca de modelos abiertos**: si alguien configura un modelo cerrado, el sistema no arranca. |
| `src/corpus/` | **Ingesta:** valida `fuentes.csv`, extrae texto de HTML/PDF/DOCX, corta por artículo, pone a cada fragmento el nombre canónico de su norma (clave para que las citas cuenten), bloquea la construcción si se cuela material del banco de preguntas, genera el manifiesto, descarga el corpus desde la nube y empaqueta el zip publicable. |
| `src/index/` | **Índices:** bge-m3 con FAISS (búsqueda por significado) y BM25 (búsqueda por palabras exactas, que distingue "artículo 42" de "artículo 24"). |
| `src/retrieval/` | **Búsqueda híbrida:** primero el artículo que la pregunta cite, luego la combinación de ambos índices y el reordenamiento con el reranker. Devuelve 10 pasajes. |
| `src/generation/` | **Respuesta:** Qwen3-8B con temperatura 0, los prompts de cada formato (`prompts/*.txt`), el **filtro que borra las citas sin respaldo** en los pasajes y la regla de abstención. |
| `src/pipeline/main.py` | Recorre las preguntas y escribe `submissions.jsonl`. Si se interrumpe, retoma donde quedó, y permite repartir el trabajo entre varias máquinas (`--particion k/n`). |
| `src/eval/` | Mide la calidad de la recuperación, genera el reporte de brechas, simula la **verificación en vivo** (`verificar`) y valida la entrega final (`validar_entrega`). |
| `run.py` / `run.sh` / `Dockerfile` | El **comando único** que exige el reto, y el contenedor para la prueba de reproducibilidad. |

## 4. Cómo se construyó (útil para el video y el informe)

| Archivo | Qué encuentran |
|---|---|
| `docs/ARQUITECTURA.md` | El diseño técnico detallado y el porqué de cada decisión (por ejemplo, la cuenta de por qué nunca conviene abstenerse en selección múltiple). |
| `PROGRESO.md` | Bitácora de cada tarea: qué se hizo, cómo se verificó, **mediciones reales** (tiempos en CPU y en Docker) y decisiones que tomamos (pasajes completos, sin Ollama, sin modelos falsos…). |
| `PLAN.md` | Las 31 tareas con su estado y la sección **Bloqueos**, con lo que falta de parte del equipo. |
| `CLAUDE.md` / `LOOP.md` | Reglas y protocolo del asistente que desarrolló el código. No hace falta revisarlos, salvo curiosidad. |
| `tests/` | 99 pruebas automáticas, todas con los modelos reales. |
| `data/`, `schema/`, `scripts/` | Material oficial del reto (preguntas de muestra, esquema, evaluador), copiado sin cambios. |

## 5. Lo que tiene que hacer el equipo, en orden

1. **Corpus real** en OneDrive, siguiendo `GUIA_CORPUS.md` y `docs/BRECHAS.md`.
2. **Indexar**, idealmente en GPU, y correr la muestra: con eso se llenan el reporte del viernes y el informe.
3. **Llave del juez** en `.env` para la parte de RAGAS.
4. **Medir en Turing**, para decidir cuántas máquinas usar el sábado.
5. **Publicar el zip** del corpus y pegar el enlace en `.env` y en el README.
6. **Video** de 5 minutos: arquitectura, corpus, demo con la interfaz y limitaciones.

## Fechas

- **Viernes 2 de octubre, 17:00:** reporte de avance con el puntaje sobre la muestra.
- **Sábado 3 de octubre, 9:00–15:00:** ejecución ciega de las 992 preguntas e interfaz; 15:00 verificación en vivo.
