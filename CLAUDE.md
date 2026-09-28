# CLAUDE.md — Hackathon 2026 (RAG de derecho colombiano)

Este archivo se carga en cada iteración. Contiene las **reglas no negociables**, el
contexto mínimo y los punteros. El diseño técnico está en `docs/ARQUITECTURA.md`,
el backlog en `PLAN.md`, el protocolo del loop en `LOOP.md` y la bitácora de trabajo
en `PROGRESO.md`.

## Qué estamos construyendo

Un sistema RAG que responde las 1.042 preguntas del benchmark de derecho colombiano
(50 de muestra ahora, 992 ciegas el sábado 3 de octubre de 2026, 9:00–15:00) con
un **decoder abierto ≤ 8B** y un **encoder abierto**, sobre un corpus jurídico
construido por el equipo. Salida: `submissions.jsonl` según
`schema/submission.schema.json`, calificada por `scripts/evaluate.py`.

Material oficial: `InformacionReto/Hackathon 2026/` y `enunciado.pdf` (léelos si
tienes dudas de reglas; mandan sobre este archivo).

## Reglas NO negociables (su violación descalifica o la pide el usuario)

1. **Solo modelos con licencia abierta** en cualquier componente del sistema:
   decoder, encoder, reranker, expansión de consultas, datos sintéticos.
   - Decoder por defecto: `Qwen/Qwen3-8B` (Apache-2.0). Alternativa: `BSC-LT/salamandra-7b-instruct` (Apache-2.0).
   - Encoder por defecto: `BAAI/bge-m3` (MIT). Alternativa: `intfloat/multilingual-e5-large` (MIT).
   - Reranker: `BAAI/bge-reranker-v2-m3` (Apache-2.0).
   - **Prohibidos**: OpenAI, Anthropic, Google, Cohere y cualquier modelo cerrado.
     También `jinaai/jina-embeddings-v3` (CC-BY-NC, no es licencia abierta) y
     cualquier modelo con licencia no comercial o restrictiva.
   - **Sin APIs ni servidores de modelos**: decoder, encoder y reranker corren en
     proceso con pesos de Hugging Face (backends `llamacpp` y `transformers`). No
     se agregan clientes HTTP de LLM (“OpenAI-compatible”, OpenRouter, etc.) y todo
     modelo debe estar en `MODELOS_ABIERTOS` de `src/config.py`.
   - Tú (Claude) eres herramienta de desarrollo: escribes código. **Nunca**
     generas contenido que entre al sistema: ni texto del corpus, ni respuestas,
     ni reformulaciones de consultas, ni ejemplos few-shot de contenido jurídico,
     ni datos sintéticos.
2. **Un único comando** reproduce todo desde cero sobre la muestra:
   `bash run.sh` (equivalente: `python run.py --split sample`). Debe correr en
   contenedor limpio (`Dockerfile`). Y el evaluador oficial debe correr tal cual:
   `python scripts/evaluate.py --submission submissions.jsonl --split sample [--ragas]`.
3. **Temperatura 0** y sistema determinista (semilla fija, desempates estables).
4. **Nunca indexar** `data/` (preguntas, respuestas, `legal_basis`) ni nada que
   contenga respuestas esperadas. `sample_50.jsonl` se usa solo para evaluar.
   Tampoco se copia contenido de la muestra dentro de los prompts.
5. **Nunca editar a mano** `submissions.jsonl`; solo lo escribe el pipeline.
6. **Índice congelado** en la entrega: un hash del corpus y del índice queda
   registrado en `build/indice/index_manifest.json`.
7. **Secretos**: `.env` nunca se imprime, nunca se versiona y nunca se edita su
   valor de `OPENROUTER_API_KEY`. `.env.example` es la plantilla versionada.
   `OPENROUTER_API_KEY` es **solo para el juez del evaluador**, no para el sistema.

## Cómo puntúa el evaluador (entenderlo es la ventaja competitiva)

Lee `scripts/citations.py` y `scripts/evaluate.py` antes de tocar generación. Lo esencial:

- **Citas a nivel de cuerpo**: `bodies()` descarta el artículo; se compara
  `(tipo, número, año)`, p. ej. `("ley","1150","2007")` o `("codigo_civil",None,None)`.
- **Respaldo** = citas que `citations.extract()` encuentra en el `texto` de los
  **primeros 10** `pasajes_recuperados`. Por eso **cada pasaje empieza con el
  nombre canónico de su norma** (p. ej. `Ley 1150 de 2007, artículo 11. ...`).
- Cita correcta y respaldada = 1; correcta sin respaldo = 0,5; incorrecta pero
  respaldada = 0 (sin castigo); incorrecta y sin respaldo = castigo ×2.
  ⇒ **Toda cita del texto de respuesta debe estar en los pasajes** (post-filtro
  determinista con el propio `citations.extract`).
- Texto de citas: MC = `justificacion`; semiabierta = `respuesta` + `referencia_legal`;
  abierta = los cuatro campos.
- Leyes sin año (“Ley 1150”) **no se reconocen** salvo alias (599, 906, 1564,
  1437, 1098, 1801, 1952, 624, 1480). Siempre escribir `Ley N de AAAA`.
- RAGAS (juez) solo ve `respuesta` (semiabierta) y los 4 campos (abierta).
- Abstención: acertar = 1, abstenerse = 0,5, fallar = 0 en 10 pts, pero abstenerse
  pierde exactitud, RAGAS y citas. **La abstención debe ser rara** (ver ARQUITECTURA §7).

## Convenciones del código

- Python ≥ 3.10 (idealmente 3.11) en `.venv`; dependencias fijadas en `requirements.txt`.
- Paquete en `src/` (`src/corpus`, `src/index`, `src/retrieval`, `src/generation`,
  `src/pipeline`, `src/eval`), interfaz en `interfaz/`, pruebas en `tests/`.
- Configuración solo desde `src/config.py` (lee `.env`); sin rutas absolutas en el código.
- Todo módulo ejecutable con `python -m src.<módulo>`; salidas en `build/` y `runs/` (ignoradas por git).
- Pruebas con `pytest -q`; deben pasar al cerrar cada tarea.
- **Nada de modelos falsos ni simulados** (encoders, rerankers o decoders “fake”/mock):
  el código y las pruebas usan siempre los modelos reales configurados en `.env`
  (bge-m3, bge-reranker-v2-m3, Qwen3-8B). Si un modelo o servidor no está
  disponible, la tarea queda `[B]` con instrucciones; no se sustituye por un doble.
  El único dato de prueba permitido es el mini-corpus `TEXTO DE PRUEBA` de
  `tests/conftest.py`, que existe solo para probar el flujo hasta que llegue el corpus real.
- Comentarios y mensajes en español, identificadores en inglés o español, pero consistentes por módulo.
- **Git lo maneja solo el usuario.** No ejecutes ningún comando de git (`init`,
  `add`, `commit`, `push`, `stash`, `checkout`, ramas…). Al cerrar un hito
  (fin de cada fase F0–F5 de `PLAN.md`) avísale al usuario para que él haga
  commit y push.
