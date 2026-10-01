# Runbook del sábado 3 de octubre de 2026

Guía paso a paso para la ejecución ciega (9:00–15:00) y la verificación en vivo
(15:00–17:00). Imprimirla o tenerla abierta. Todos los comandos se corren desde
la raíz del repositorio con el entorno activado.

> Regla de oro: **después de las 9:00 no se cambia nada** del índice, del corpus,
> de los prompts ni de la configuración del decoder. Solo se ejecuta.

---

## A. Antes del sábado (hasta el viernes)

- [ ] Corpus final construido e indexado (en GPU si es grande): `python -m src.corpus.build`,
      `python -m src.corpus.manifest`, `python -m src.index.build`.
- [ ] Zip publicado: `python -m src.corpus.empaquetar` → subir a la nube con acceso público →
      `CORPUS_ZIP_URL` y `CORPUS_ZIP_SHA256` en `.env` y en el README. Probar el enlace desde una
      sesión privada y con `python -m src.corpus.nube --forzar`.
- [ ] **Índice congelado:** anotar aquí el sha256 del zip: `________________________`.
- [ ] Máquina(s) del sábado definidas (GPU): `DECODER_BACKEND`, `DECODER_DEVICE`,
      `ENCODER_DEVICE` fijados en su `.env`. La misma configuración se usa para la verificación.
- [ ] Ensayo en esa máquina: `python -m src.pipeline.main --split sample --limite 20` y leer
      `runs/<tag>/tiempos.json` → s/pregunta (p50) = `____` ⇒ 992 × p50 = `____` h.
- [ ] Si la proyección supera ~4,5 h: preparar **N máquinas** con el mismo `.env` y el mismo
      zip (ver D). N = ⌈ proyección / 4,5 h ⌉ = `____`.
- [ ] Modelos ya descargados en cada máquina (caché de Hugging Face): correr una vez
      `python -m src.generation.ping` y `python -m src.retrieval.buscar "prueba"`.
- [ ] Commit y push del repositorio con todo lo anterior.

## B. 9:00 — Recepción de las preguntas

1. Copiar el archivo entregado a `data/test_992.jsonl`.
2. Comprobar: `python -c "import json;r=[json.loads(l) for l in open('data/test_992.jsonl',encoding='utf-8')];from collections import Counter;print(len(r),Counter(x['formato'] for x in r))"`
   → deben ser 992 líneas.
3. Comprobar corpus e índice congelados: `python -m src.corpus.nube` (sha256 igual al anotado).

## C. 9:10 — Ejecución (una máquina)

```bash
python -m src.pipeline.main --split test --out submissions.jsonl --tag sabado
```

- Escribe cada respuesta al terminarla. **Si se interrumpe, se relanza el mismo comando**
  y continúa donde quedó (salta los ids ya escritos).
- Una pregunta que falle no detiene la corrida: queda con respuesta de respaldo y el
  error en `runs/sabado/trazas.jsonl`.
- Seguimiento: el contador `[n/992]` en consola; `wc -l submissions.jsonl`.
- **A los 20 minutos**, estimar: (992 − hechas) × s/pregunta. Si no alcanza antes de
  las 14:15, pasar a D sin detener esta máquina (usar particiones de lo que falte).

## D. Plan B — varias máquinas en paralelo

El sistema es determinista: una respuesta es la misma sin importar dónde se genere.
En la máquina k de n (misma configuración y mismo zip):

```bash
python -m src.pipeline.main --split test --particion k/n --out parte_k.jsonl --tag sabado_k
```

O por **rangos de posiciones** (1.ª a 250.ª, etc.; ambos extremos incluidos; son posiciones en
el archivo, no ids). Más fácil de repartir a mano y de rehacer si una máquina se cae:

```bash
python -m src.pipeline.main --split test --rango 1 250   --out parte_1.jsonl --tag sabado_1
python -m src.pipeline.main --split test --rango 251 500 --out parte_2.jsonl --tag sabado_2
python -m src.pipeline.main --split test --rango 501 750 --out parte_3.jsonl --tag sabado_3
python -m src.pipeline.main --split test --rango 751 992 --out parte_4.jsonl --tag sabado_4
```

En los cuadernos (Colab/Kaggle) es la variable `RANGO = "1 250"` de la celda 2.

Con el comando único (recomendado en Turing; ver `docs/COMO_EJECUTAR.md` §11), en la máquina k:

```bash
python run.py --split test --gpu --indice-existente --rango INICIO FIN --tag sabado_k
```

Unir al final (en cualquier orden) y validar:

```bash
cat parte_*.jsonl > submissions.jsonl
python -m src.eval.validar_entrega submissions.jsonl --split test
```

Si una máquina ya había respondido parte del banco, sus líneas sirven: se concatenan y
`validar_entrega` avisa de duplicados (conservar una sola línea por id).

## E. 14:00 — Validación final

```bash
python -m src.eval.validar_entrega submissions.jsonl --split test
```

Debe decir `992 líneas para 992 preguntas · … · VÁLIDA`. Si faltan ids, relanzar el
comando de C (solo procesa los faltantes).

## F. 14:15 — Cierre de la entrega (antes de las 15:00)

Checklist oficial (`entregables/sabado/README.md`):

- [ ] `submissions.jsonl` en la raíz, válido contra `schema/submission.schema.json`.
- [ ] El índice quedó congelado y no se modificó después de la entrega (sha256 igual).
- [ ] La temperatura del decoder está en 0 (`validar_final()` lo exige; no tocar `.env`).
- [ ] El `README` tiene la sección `## Corpus e índice` con el enlace, tamaño y sha256.
- [ ] El enlace abre desde una sesión privada del navegador, sin pedir permisos.
- [ ] El comprimido incluye `LICENSE`.
- [ ] La interfaz gráfica corre en el equipo del grupo: `python -m interfaz.app`.
- [ ] `informe/INFORME_TECNICO.pdf` (≤ 3 páginas), `CORPUS.md`, `corpus_manifest.json`,
      enlace al video.
- [ ] Commit y push; el repositorio es accesible para el jurado.

## G. 15:00 — Verificación en vivo

El jurado elige 2–3 ids entregados y pide regenerarlos. En **la misma máquina y con la
misma configuración** con que se generaron:

```bash
python -m src.eval.verificar --ids <id1>,<id2>,<id3> --split test
```

Regenera sin caché y compara con `submissions.jsonl`. Debe imprimir `COINCIDE` en cada
id (mismos pasajes recuperados y mismas normas citadas; la redacción puede variar).
Para mostrarlo en la interfaz: marcar “Regenerar sin caché”.

Si algo difiere: revisar que `.env`, el zip (sha256) y el dispositivo (`cuda`/`cpu`)
sean los mismos de la corrida. Las citas se derivan de los pasajes, así que si los
pasajes coinciden, las normas también deberían.

## H. Problemas frecuentes

| Síntoma | Acción |
|---|---|
| `No hay índice` | `python -m src.corpus.nube` (o revisar `INDEX_DIR`) |
| sha256 no coincide | No usar ese zip. Volver a descargar el publicado |
| Falta memoria de GPU | `DECODER_BACKEND=llamacpp` con CUDA (Q4_K_M ≈ 6 GB) en vez de `transformers` bf16 (≈ 16 GB) |
| Muy lento | Plan B (D); en último caso `USE_RERANKER=0` **solo si se decidió antes de las 9:00** |
| Corte de luz / cierre | Relanzar el mismo comando: reanuda |
| `validar_entrega` con errores de esquema | Relanzar C para esos ids tras borrarlos del archivo (el pipeline nunca escribe líneas inválidas; revisar si hubo edición manual — prohibida) |
