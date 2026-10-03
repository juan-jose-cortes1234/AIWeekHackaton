# Verificación independiente de alternativas — C-25, 2026-10-03

El usuario reportó de nuevo **11/15** con la versión anterior, sin identificar
los resultados de cada perfil. Esta nueva variante está implementada pero su
exactitud con Gemma todavía debe medirse en Colab. No se afirma 12/15 o 13/15.

## Un único ZIP y dos perfiles

`dist/paquete_colab_muestra.zip` contiene src, configuración, preguntas, esquema,
evaluador, índice FAISS/BM25/manifiesto y `notebooks/muestra_en_colab.ipynb`.
Subirlo a Mi unidad y ejecutar el cuaderno actualizado. No requiere otro parche
ni reconstruir el índice. Los pesos reales se descargan en Colab; no hay secretos
en el paquete.

La celda 2 usa `TAG="muestra_mc_v17"`, `COMPARAR_MC=True` y
`PERFILES_MC="v12,verificacion"`. Produce **30 respuestas**, 15 por perfil,
cargando los modelos una sola vez. Son 90 llamadas previstas al decoder:
15 del control y 75 de verificación (sin contar reparaciones JSON internas).
Usar este TAG nuevo para no mezclar código o resultados con una corrida anterior.

| Perfil | Recuperación | Generación por pregunta |
|---|---|---|
| `v12` | Control original, 20/8 candidatos y cuatro puestos de pregunta | Una llamada |
| `verificacion` | Mismos candidatos y selección de pasajes de v12 | Cuatro auditorías independientes y una selección |

El perfil nuevo es opcional. Los defaults de producción conservan v12.
Gemma E4B Q8, BGE-M3, BGE-reranker-v2-m3, temperatura 0 y semilla 42 se mantienen.
Los perfiles anteriores siguen disponibles, pero no se activan en esta comparación.

## Qué comprueba

Cada auditoría recibe la pregunta, todas las alternativas para resolver referencias
entre ellas, una alternativa objetivo y evidencia del corpus. No recibe respuestas
previas ni informes de las otras auditorías. Primero genera hasta dos citas breves,
después una explicación corta y finalmente `respaldada`, `contradicha` o
`evidencia_insuficiente`.

La comprobación exige que cada cita esté literalmente en su pasaje original **y**
en el texto visible. Solo normaliza Unicode NFC y espacios; conserva puntuación,
mayúsculas, negaciones y cifras. Una cita alterada o ausente degrada la conclusión
a evidencia insuficiente. Una conclusión de respaldo o contradicción sin ninguna
cita también se degrada. No encontrar respaldo no significa contradicción.

La quinta llamada recibe los estados comprobados, las citas aceptadas y los
pasajes originales. No recibe citas rechazadas ni explicaciones sin comprobar.
Gemma compara las alternativas completas y elige; no se decide por mayoría,
un umbral arbitrario ni reglas por ID. La presencia literal de una cita **no**
demuestra que respalde semánticamente una opción: Gemma sigue haciendo ese juicio.

Todas las etapas leen los mismos pasajes con los mismos números P. Se reserva
espacio para los informes antes de comenzar y, si hace falta, se reduce el prefijo
visible. Esto puede hacer que lea menos pasajes que v12; las trazas registran los
índices exactos. Si los informes exceden la reserva, se conservan sus estados y
referencias P, omitiendo la duplicación de citas que ya están en el contexto.
No cambian textos, offsets, corpus, índice, gold ni evaluador.

## Medir y revisar

Cada perfil guarda submissions, trazas, tiempos y comparación MC dentro de
`resultados_hackathon/muestra_mc_v17/muestra_mc_v17_<perfil>/` en Drive.
`muestra_mc_v17_experimentos.json` compara aciertos, ganancias, pérdidas y latencia.
Las trazas contienen las cuatro auditorías originales, estados comprobados,
motivos de rechazo, tokens y tiempos. Las citas rechazadas son una intervención
del comprobador; una etapa truncada, JSON inválido o excepción es un fallo y hace
la comparación no utilizable para acreditar una mejora. El fallo de la selección
final activa el fallback MC existente y también invalida esa comparación.

Antes de adoptar la variante, comprobar que supera el control sin perder otros
aciertos y revisar sus errores. Para las 50 preguntas, fijar `COMPARAR_MC=False`,
`SOLO_MC=False` y `PERFIL_MC="verificacion"` después de medirla.
La última celda exporta ambas corridas juntas en un ZIP de resultados.

```text
python -m src.eval.experimentos_mc --tag mc_v17 --perfiles v12,verificacion
python -m src.pipeline.main --split sample --tag muestra_v17 --perfil-mc verificacion --no-cache
```

## Verificación local

221 pruebas deterministas aprobadas; 46 integraciones que necesitan modelos
reales omitidas, incluida la prueba de las cinco etapas. No hay GPU/pesos locales
y no se usaron modelos simulados. Compatibilidad del control: 50 esquemas y 550
renderizados idénticos al v12 archivado; recuperación híbrida y selección por
turnos equivalentes en AST. Inferencia GPU y mejora de exactitud pendientes.
