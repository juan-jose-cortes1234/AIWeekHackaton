# LOOP.md — protocolo de una iteración

Se lanza desde la raíz del repo (`C:\SeptimoSemestre\HackathonAIWeek`) con:

```
/loop Ejecuta UNA iteración siguiendo LOOP.md
```

(sin intervalo: el loop marca su propio ritmo). Cada disparo = **una tarea** de `PLAN.md`,
terminada, probada y registrada.

**Git lo maneja solo el usuario.** El loop no ejecuta ningún comando de git
(ni `init`, `status`, `add`, `commit`, `push`, `stash`, ramas). Al cerrar un hito
(una fase F0–F5 completa) el loop se pausa para que el usuario haga commit y push.

---

## 0. Antes de empezar (siempre)

1. Lee `CLAUDE.md` (reglas), la sección de la tarea en `PLAN.md`, las últimas 3
   entradas de `PROGRESO.md` y la sección **Bloqueos** de `PLAN.md`.
2. Si hay mensajes nuevos del usuario en la conversación, **tienen prioridad**
   sobre el backlog: atiéndelos primero y regístralo en `PROGRESO.md`.
3. Si `PLAN.md` tiene una tarea en `[~]` de una iteración anterior, retómala
   primero, usando la lista de archivos tocados que quedó en `PROGRESO.md`
   (nunca borres archivos del equipo ni `CORPUS_RAW_DIR`).
4. Revisa si un bloqueo se resolvió (p. ej. `CORPUS_RAW_DIR/fuentes.csv` ya
   existe, `.env` ya tiene la llave —compruébalo sin imprimirla—, responde el
   endpoint del decoder). Si se resolvió, quita el `[B]` y vuelve la tarea a `[ ]`.

## 1. Elegir la tarea

- La primera `[ ]` de `PLAN.md` cuyas dependencias (tareas anteriores de las
  que depende) estén `[x]`. Marca `[~]`.
- Si la tarea necesita algo humano (corpus, llave, servidor del decoder, GPU):
  hazla hasta donde se pueda con fixtures, deja el resto como subtarea `[B]`
  con instrucción concreta en **Bloqueos**, y pasa a la siguiente tarea no bloqueada.
- Si es demasiado grande para una iteración (~45 min de trabajo), divídela en
  `Txx.a/b/c` dentro de `PLAN.md` y haz solo la primera.

## 2. Implementar

- Sigue `docs/ARQUITECTURA.md`. Si una decisión del diseño resulta
  equivocada, cámbiala en el documento **y** explica el porqué en `PROGRESO.md`.
- Código mínimo y completo; nada de “TODO: implementar”. Pruebas en `tests/`
  para toda lógica determinista (segmentación, encabezados, post-filtro de citas,
  esquema, abstención).
- Sin modelos falsos ni mocks: las pruebas usan los modelos reales de `.env` (ver `CLAUDE.md`).
- Fixtures de prueba: texto inventado marcado `TEXTO DE PRUEBA`, nunca
  presentado como norma real, nunca dentro de `CORPUS_RAW_DIR` ni del índice real.

## 3. Verificar (obligatorio antes de marcar `[x]`)

1. `pytest -q` pasa completo.
2. El criterio *Acepta* de la tarea se cumple; ejecuta el comando que lo demuestra.
3. Si la tarea toca recuperación, generación o citas y ya existe pipeline:
   corre `python scripts/evaluate.py --submission runs/<tag>/submissions.jsonl --split sample`
   (sin `--ragas`; el juez cuesta dinero y se usa solo en T23 o si el usuario lo pide)
   y anota los números.
4. Revisa que no se violó ninguna regla de `CLAUDE.md` (modelos abiertos, nada
   de `data/` en el índice, temperatura 0, `.env` intacto y cubierto por `.gitignore`).

Si algo falla y no lo puedes arreglar en esta iteración: deja la tarea en `[~]`,
describe en `PROGRESO.md` el fallo exacto y **la lista de archivos que tocaste**.
Nunca dejes rota una tarea que ya estaba `[x]`: si tu cambio la rompe y no lo
puedes arreglar, deshaz tu cambio a mano en esos archivos.

## 4. Registrar

- `PLAN.md`: marca `[x]` (o `[B]` / `[~]`).
- `PROGRESO.md`: añade **al final** una entrada con la plantilla que hay allí,
  incluida la lista de archivos creados o modificados.
- Si cambió el puntaje: fila nueva en la tabla de evolución de `CORPUS.md` y en `PROGRESO.md`.
- Si la tarea **cambia el comportamiento del sistema** (recuperación, generación, citas, corte del corpus,
  configuración por defecto): entrada nueva en `docs/CAMBIOS.md` con antes / ahora / por qué /
  evidencia / archivos / si requiere reindexar.

## 5. Hitos (commit y push los hace el usuario)

Si con esta tarea quedó completa una fase (F0, F1, …, F5) de `PLAN.md`:

1. Asegúrate de que `pytest -q` pasa y de que `.gitignore` excluye `.env`,
   `build/`, `runs/`, `dist/`, modelos y el corpus crudo.
2. Añade en `PROGRESO.md` una entrada `## HITO Fx listo` con: qué quedó
   funcionando, cómo probarlo (comandos) y un mensaje de commit sugerido.
3. Díselo al usuario en un mensaje corto con ese mismo mensaje de commit sugerido,
   y **detén el loop**. El usuario hace commit y push y lo relanza.

## 6. Decidir el siguiente disparo

- Acabas de cerrar un hito → el loop ya quedó detenido (sección 5).
- Quedan tareas `[ ]` sin bloquear → programa el siguiente disparo pronto (~60–120 s).
- Solo quedan tareas bloqueadas por humanos → escribe un resumen corto para el
  usuario (qué falta y cómo desbloquearlo) y **detén el loop**.
- Todas las tareas `[x]` → corre el ensayo general (T30) una vez más, resume
  el estado final para el usuario y **detén el loop**.
- Si dos iteraciones seguidas fallan en la misma tarea → detén el loop y pide ayuda al usuario.

## Nunca

- Ejecutar comandos de git de ningún tipo.
- Usar un modelo cerrado en el sistema, ni escribir tú contenido jurídico para el corpus, prompts o respuestas.
- Indexar o poner en prompts cualquier cosa de `data/` (preguntas, respuestas, `legal_basis`).
- Editar `submissions.jsonl` a mano o “arreglar” respuestas después de generarlas.
- Leer, imprimir o modificar el valor de `OPENROUTER_API_KEY` (solo comprobar que no está vacío).
- Borrar o mover archivos de `CORPUS_RAW_DIR`.
- Correr el juez (`--ragas`) en bucle.
- Cambiar temperatura, semilla o índice después del congelamiento del sábado.
