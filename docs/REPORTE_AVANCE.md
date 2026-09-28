# Reporte de avance — Hackathon 2026

**Equipo:** <nombre del equipo>
**Integrantes:** <nombre 1> · <nombre 2> · <nombre 3>
**Fecha de la medición:** <AAAA-MM-DD>

<!-- BORRADOR. Enviar como REPORTE_AVANCE.pdf (una página) a
rf.manrique@uniandes.edu.co, asunto "[Hackathon 2026] Avance — <nombre del equipo>",
antes del viernes 2 de octubre a las 17:00. -->

---

## 1. Puntaje sobre las preguntas de muestra

Resultado de `python scripts/evaluate.py --submission runs/<tag>/submissions.jsonl --split sample`.

| Componente | Puntos obtenidos | Puntos posibles |
|---|---:|---:|
| Exactitud en cerradas | `<x>` | 20 |
| Calidad de citación | `<x>` | 20 |
| Abstención calibrada | `<x>` | 10 |
| **Total automático sin RAGAS** | `<x>` | **50** |

Observaciones sobre el resultado: `<dos o tres líneas; p. ej. 0 citas sin
respaldo gracias al post-filtro; los fallos de cerradas se concentran en …>`

## 2. Estado del corpus

| Métrica | Valor |
|---|---|
| Documentos incorporados | `<n>` |
| Fragmentos indexados | `<n>` |
| Áreas del banco con cobertura | `<lista>` |
| Áreas del banco sin cobertura | `<lista>` |

Fuentes consultadas: Secretaría del Senado, SUIN-Juriscol, relatorías de la
Corte Constitucional, la Corte Suprema de Justicia y el Consejo de Estado
`<, DIAN, SIC…>`. Cobertura del seed: `<x de 559 ítems>` (`docs/BRECHAS.md`).

## 3. Arquitectura actual

| Componente | Elección |
|---|---|
| Encoder | `BAAI/bge-m3` (MIT) |
| Decoder | `Qwen/Qwen3-8B` (Apache-2.0), temperatura 0, sin modo de razonamiento |
| Estrategia de recuperación | Híbrida: router de artículos citados + BM25 jurídico + denso (FAISS exacto), fusión RRF, reranker `bge-reranker-v2-m3`, 10 pasajes |
| Segmentación del corpus | Por artículo con encabezado canónico de la norma; sentencias por secciones |
| Mecanismo de abstención | Nunca en selección múltiple; en texto libre solo sin evidencia pertinente |

## 4. Riesgos identificados

1. **Cómputo:** en CPU cada respuesta tarda ~2,5 min. Mitigación: ejecución en
   GPU (sala Turing / Colab) medida antes del sábado; plan B repartiendo las
   preguntas entre varias máquinas (el sistema es determinista).
2. **Cobertura del corpus:** normas del banco ausentes del corpus. Mitigación:
   reporte automático de brechas y priorización por peso en el banco.
3. **Publicación del corpus:** el enlace debe descargarse sin permisos durante 30
   días. Mitigación: zip determinista con sha256 verificado por el propio sistema
   y prueba desde una sesión privada.
