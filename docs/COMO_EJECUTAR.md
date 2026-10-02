# Cómo ejecutar el sistema, paso a paso

Guía práctica para el equipo. El `README.md` describe el sistema para el jurado; aquí está el
**cómo**: instalar, construir el corpus y el índice, responder, evaluar y experimentar.

Convención: los comandos se corren desde la raíz del repositorio. En Windows, `python`
significa `.venv\Scripts\python.exe` (o actívelo con `.venv\Scripts\activate`); en Linux/Mac,
`.venv/bin/python` (`source .venv/bin/activate`).

---

## 0. Requisitos

- Git y **Python ≥ 3.10** (probado con 3.11).
- **≥ 16 GB de RAM** (los tres modelos juntos ocupan ~10 GB) y ~20 GB de disco (modelos de
  Hugging Face, que se descargan solos la primera vez).
- Cuenta de Google para Colab (GPU gratuita). En CPU todo funciona, pero una respuesta tarda
  ~2,5 min y construir el índice completo ~8 h.

## 1. Instalación (una vez)

```bash
git clone <URL del repositorio>
cd <carpeta del repositorio>
python -m pip install uv
python -m uv venv --python 3.11 .venv
python -m uv pip install --python .venv/Scripts/python.exe -r requirements.txt
```
(En Linux/Mac: `--python .venv/bin/python`.)

Comprobación rápida, sin modelos (~1 min):
```bash
python -m pytest -q tests/test_config.py tests/test_fuentes.py tests/test_citas.py
```

## 2. Configuración

```bash
cp .env.example .env
```
En `.env`:
- `CORPUS_RAW_DIR`: carpeta con `fuentes.csv` y los documentos (por defecto `./corpus_raw`).
- `OPENROUTER_API_KEY`: la llave del juez, **solo** para evaluar con RAGAS. Se comparte por un
  canal privado; `.env` nunca se sube a git.
- `CORPUS_ZIP_URL`: dejar **vacío** mientras trabajen con el corpus local (se llena el día de la
  entrega con el zip publicado).
- El resto trae los valores por defecto del sistema; los parámetros de experimentación están
  documentados en el propio `.env.example` y en `docs/CAMBIOS.md`.

## 3. Corpus

El corpus crudo (`fuentes.csv` + documentos) vive en el Google Drive del equipo y no está en git.

1. Descargar la carpeta del Drive y dejarla en `./corpus_raw/` (con `fuentes.csv` en su raíz).
2. Validar, procesar y generar manifiesto:
   ```bash
   python -m src.corpus.validar      # errores de fuentes.csv, fila por fila
   python -m src.corpus.build        # texto limpio → fragmentos (≈ 5 min); guardia anti-fuga
   python -m src.corpus.manifest     # corpus_manifest.json y tablas de CORPUS.md
   python -m src.eval.brechas        # docs/BRECHAS.md: normas que aún faltan
   ```
3. Chequeo de secciones de las sentencias: `python -m src.corpus.secciones` (las 3 de control) o
   `--todas`; termina con código 1 si ve algo raro (RESUELVE desbordado, sin RESUELVE o sin parte motiva).
4. Qué mirar: el resumen de `build` (artículos por documento: si un código sale con muy pocos,
   algo se cortó mal) y que termine sin "GUARDIA ANTI-FUGA". Formato de `fuentes.csv` y
   consejos de descarga: `GUIA_CORPUS.md`.

## 4. Índice (vectores bge-m3 + FAISS + BM25)

El índice depende del corpus procesado: **después de cada `src.corpus.build` que cambie
fragmentos hay que actualizarlo**. Es incremental: solo se calculan los fragmentos nuevos o
modificados (caché en `build/cache/emb/`). Archivos del índice:

| Archivo | Qué es |
|---|---|
| `build/indice/chunks.jsonl` | Los fragmentos (lo produce `src.corpus.build`) |
| `build/indice/index.faiss` | Vectores bge-m3 (búsqueda por significado) |
| `build/indice/bm25/` | Índice BM25 (búsqueda por palabras exactas) |
| `build/indice/index_manifest.json` | Modelo, n.º de fragmentos y hashes: dice a qué fragmentos corresponde |
| `build/cache/emb/baai_bge_m3.npz` | Caché de vectores: evita recalcular lo que no cambió |

**Estado al 1-oct:** 338 documentos, 68.603 fragmentos, índice al día en el proyecto.

### Compartir el índice con el equipo (Drive)
No hace falta que cada uno lo reconstruya. Quien lo tenga al día genera un zip con todo:
```bash
python -m src.index.paquete_colab --modo muestra --con-indice   # dist/paquete_colab_muestra.zip (~610 MB)
```
y lo sube a Drive. Los demás lo descomprimen **en la raíz del proyecto** (deben quedar
`build/indice/` y `build/cache/emb/`) y comprueban con `python -m src.index.build`, que debe
decir **"reutilizado (sin cambios)"**. `--con-indice` se niega si el índice local no corresponde
a los fragmentos. Ese mismo zip es el que usan los cuadernos (sección 5).

### Reconstruirlo (cuando cambia el corpus)
- **En Colab o Kaggle (recomendado):** el cuaderno de la sección 5 actualiza el índice en la GPU
  antes de responder (celda 4), y devuelve el índice nuevo en su zip. Solo calcula los
  fragmentos nuevos (23.402 fragmentos tardaron 21 min en una T4 de Kaggle). Con el paquete sin `--con-indice`.
- **Solo el índice:** `python -m src.index.paquete_colab` → `dist/paquete_colab.zip` y el
  cuaderno `notebooks/indice_en_colab.ipynb` (devuelve `indice_colab.zip`).
- **Local, pocos fragmentos nuevos:** `python -m src.index.build` (~0,7 s por fragmento en CPU).

### Verificar
```bash
python -m src.index.build          # debe decir "reutilizado (sin cambios)"
python -m src.retrieval.buscar "¿Cuál es el plazo para liquidar un contrato estatal?" --area administrativo
```

## 5. Responder y evaluar la muestra en GPU (Colab o Kaggle)

Hay dos cuadernos con el **mismo flujo**: `notebooks/muestra_en_colab.ipynb` (Google Colab) y
`notebooks/muestra_en_kaggle.ipynb` (Kaggle, cuando Colab no da GPU: ~30 h semanales). Hacen,
en orden: instalar → índice (celda 4) → probar el decoder → responder → evaluar → un zip con
índice + resultados.

### 5.1 Preparar (cada vez que cambie el código o el corpus)
```bash
python -m src.index.paquete_colab --modo muestra --con-indice   # o sin --con-indice si el índice local no está al día
```
- **Colab:** subir `dist/paquete_colab_muestra.zip` a *Google Drive → Mi unidad* (reemplazando
  el anterior). Llave del juez: ícono 🔑 *Secretos* → `OPENROUTER_API_KEY` con *Acceso al cuaderno*.
- **Kaggle** (cuenta verificada con teléfono): *Datasets* → tu dataset `paquete-colab-muestra` →
  **New Version** → subir el zip (la primera vez: *+ Create → New Dataset*, título
  `paquete-colab-muestra`, privado). Llave: *Add-ons → Secrets* → `OPENROUTER_API_KEY`.
- **Volver a subir el cuaderno** desde el repositorio cada vez que cambie (*Archivo → Subir
  cuaderno* en Colab; *File → Import Notebook* en Kaggle). Una copia vieja abierta en el navegador
  no tiene los cambios.

### 5.2 Elegir qué correr (celda 2)
| Variable | Qué hace | Ejemplos |
|---|---|---|
| `TAG` | Nombre de la corrida: resultados en `runs/<TAG>/` y zip `<TAG>.zip`. Use uno nuevo por experimento para no pisar otros | `"muestra_v4"`, `"mc_razonamiento"` |
| `RANGO` | Preguntas por **posición** en el archivo (no por id), ambos extremos incluidos | `""` = las 50; `"1 15"` = las 15 de selección múltiple de la muestra; `"16 50"` = texto libre |
| `IDS` | Preguntas concretas por id | `"290,748"` |

Con `RANGO` o `IDS` la corrida es **parcial**: la celda 6 muestra los aciertos de selección
múltiple y se salta RAGAS (no gasta la llave); la evaluación completa se hace en el computador
(5.4). Con ambos vacíos responde las 50 y evalúa sin juez y con RAGAS.

### 5.3 Ejecutar
1. *Entorno de ejecución → GPU T4* (Colab) o *Session options → Accelerator → GPU T4 x2* e
   *Internet → On* (Kaggle; no P100). En Kaggle, además, *Input → Add Input →* el dataset.
2. **Ejecutar todo.** Revisar en la salida:
   - celda 3c: `GPU disponible para llama.cpp: True` (si dice `False`, correr la 3b);
   - celda 4 (índice) y celda 5 (preguntas): `CÓDIGO DE SALIDA: 0` (el tick verde no basta).
3. Es normal ver la CPU al 100 % en la instalación y en la celda 4 (BM25 y FAISS van en CPU); la
   generación (Qwen), el encoder y el reranker van en GPU.
4. Descargar `<TAG>.zip`: Colab lo descarga solo y lo copia a Drive; en Kaggle, enlace al final
   de la última celda (o panel derecho → *Output*).
5. Dejar el zip (o su carpeta descomprimida) en la raíz del proyecto y ubicar: `runs/<TAG>/` a
   `runs/`; si trae un índice distinto del local, `build/indice/` y `build/cache/emb/` a `build/`
   (comprobar con `python -m src.index.build` → "reutilizado").

Tiempos en una T4: ~30 s por pregunta; con razonamiento en selección múltiple (C-09), más.

### 5.4 Evaluar en el computador
```bash
python scripts/evaluate.py --submission runs/<TAG>/submissions.jsonl --split sample           # sin juez: gratis
python scripts/evaluate.py --submission runs/<TAG>/submissions.jsonl --split sample --ragas   # usa la llave del .env
```
Corrida **parcial** (p. ej. las 15 de selección múltiple): primero se combina con una completa
del mismo corpus (las demás respuestas no cambian) y se evalúa la combinada:
```bash
python -m src.eval.combinar --base runs/muestra_v3 --parcial runs/<TAG> --out runs/<TAG>_50
python scripts/evaluate.py --submission runs/<TAG>_50/submissions.jsonl --split sample
```
Para `--ragas` en local: `pip install -r scripts/requirements-evaluador.txt`. Cada corrida con
juez consume la llave: úsela solo para mediciones que valgan la pena.

**Si el reporte avisa "El juez no devolvió veredicto en N items"** (fallos de red entre la máquina
y OpenRouter; cuentan como cero): repetir la evaluación con `--ragas`, preferiblemente desde Colab o el
computador (en Kaggle los fallos de red fueron frecuentes).

### 5.5 Local (CPU; solo para pocas preguntas)
```bash
python -m src.pipeline.main --split sample --ids 51,290,748      # preguntas concretas
python -m src.pipeline.main --split sample --rango 1 15          # de la 1.ª a la 15.ª (por posición)
```
~2,5 min por pregunta (más con razonamiento). Si se interrumpe, el mismo comando continúa.
Solo recuperación (sin generar, gratis): `python -m src.eval.recuperacion`.

## 6. Interfaz gráfica

```bash
python -m interfaz.app        # http://localhost:8000
```
Requiere el índice construido. Los modelos se cargan con la primera consulta.

## 7. Comando único (reproducción, lo que corre el jurado)

```bash
bash run.sh                    # o: python run.py [--limite N] [--sin-ragas]
```
Con `CORPUS_ZIP_URL` descarga el corpus publicado; si no, construye desde `CORPUS_RAW_DIR`.
En contenedor: `docker build -t hackathon-rag .` y
`docker run --rm --env-file .env -v hf-cache:/root/.cache/huggingface hackathon-rag`
(Docker necesita ≥ 12 GB de memoria asignada).

## 8. Experimentar en una rama

1. `git checkout -b experimento-<nombre>`.
2. Cambiar parámetros en `.env` (por ejemplo `MAX_POR_DOCUMENTO`, `PUESTOS_PREGUNTA`,
   `RERANK_CANDIDATOS`, `USE_RERANKER`) o el código.
3. Medir contra la misma muestra: primero `python -m src.eval.recuperacion` (gratis), luego la
   muestra completa en Colab y `evaluate.py`.
4. Registrar en `docs/CAMBIOS.md` una entrada con **antes / ahora / por qué / evidencia / archivos /
   si requiere reindexar**, para poder comparar y unir ramas.
5. Si cambia el corte del corpus o el texto de los fragmentos, **hay que reindexar** (sección 4) y
   las mediciones anteriores dejan de ser comparables.

## 9. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| Colab: `CUDA_ERROR_OUT_OF_MEMORY` / "Failed to load model" | JAX de Colab reservaba la GPU. Ya se evita en `src/config.py`; si reaparece, revise `!nvidia-smi` |
| `libcudart.so.12: cannot open shared object file` al importar llama_cpp | La imagen del entorno trae otra versión de CUDA (Colab pasó a CUDA 13 y Python 3.13). La celda 3c instala `nvidia-cuda-runtime-cu12` y `nvidia-cublas-cu12` y apunta a ellas; si aun así falla, compilar con la celda 3b (~15-20 min) y reiniciar la sesión |
| Colab: celda con tick verde pero sin resultados | Los comandos `!` no marcan error: lea la salida y el "CÓDIGO DE SALIDA" |
| Tras descomprimir, "No hay índice" | Windows creó una carpeta extra: mueva `build/` (o `runs/`) a la raíz del proyecto |
| `.htm` con "�" al abrirlos | Están en windows-1252; el sistema los lee bien, no hay que corregirlos |
| `git push` rechazado por archivo > 100 MB | Un zip quedó en un commit; los `*.zip` están en `.gitignore`: sáquelo con `git rm --cached <archivo>` y vuelva a commitear |
| `run.sh` falla con Python 3.9 | Instale 3.11 (paso 1) o use `python run.py` desde el `.venv` |

## 10. Probar otro decoder (en lugar de Qwen3-8B)

Reglas del reto: **licencia abierta y como máximo 8B parámetros** (puede ir cuantizado),
temperatura 0 y determinista. El sistema se niega a arrancar con un modelo fuera de la lista
blanca.

1. **Elegir el modelo** en Hugging Face con versión **GGUF** (llama.cpp, lo que usan los
   cuadernos): anotar el repositorio y el archivo, p. ej. `bartowski/<modelo>-GGUF` y
   `<modelo>-Q4_K_M.gguf`. Q4_K_M de un 7-8B cabe en una T4. Comprobar la licencia en la ficha
   del modelo (Apache-2.0, MIT, Llama Community, Gemma… — la del modelo, no la del repositorio).
2. **Agregarlo a la lista blanca** en `src/config.py`, `MODELOS_ABIERTOS["decoder"]`, con su
   licencia: el **repositorio GGUF** (y el original, si se usa con transformers).
3. **Cambiarlo en la celda 4 del cuaderno**:
   ```python
   DECODER_GGUF_REPO = "bartowski/<modelo>-GGUF"
   DECODER_GGUF_FILE = "<modelo>-Q4_K_M.gguf"
   ```
   En local, lo mismo en `.env` (`DECODER_GGUF_REPO`, `DECODER_GGUF_FILE`).
4. Regenerar el paquete (5.1), subir paquete y cuaderno, y correr con un `TAG` propio, p. ej.
   `"modelo_x_50"`. Para comparar con Qwen, la misma muestra y el mismo corpus que la corrida de
   referencia.

Qué cambia y qué no con otro modelo:
- El formato de chat se toma del propio GGUF; la salida JSON se sigue forzando con la gramática.
- `/no_think` y el razonamiento en selección múltiple (C-09) son propios de Qwen3: con otro
  modelo se desactivan solos.
- Los prompts (`src/generation/prompts/`) están afinados para Qwen; si otro modelo responde en
  inglés o con formato raro, ese es el primer lugar para ajustar.
- Comparar siempre con el evaluador oficial (5.4) y anotar la corrida en `docs/CAMBIOS.md`.

## 11. Por consola en una máquina con GPU (sala Turing, el sábado)

Todo es **un solo comando** por máquina: `python run.py` (o `bash run.sh`, mismas opciones).

### 11.1 Preparar cada máquina (viernes, una vez)
1. Código: `git clone <URL del repositorio>` y `cd` a la carpeta.
2. Entorno e instalación (Linux, Python 3.11):
   ```bash
   python3.11 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   # Versiones con CUDA (requirements.txt trae las de CPU):
   pip install --force-reinstall --no-deps torch==2.14.0 --index-url https://download.pytorch.org/whl/cu124
   pip install --force-reinstall --no-deps llama-cpp-python==0.3.35 --only-binary llama-cpp-python \
       --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
   ```
   Si no hay rueda precompilada para esa máquina, compilarla (~15 min):
   `CMAKE_ARGS="-DGGML_CUDA=on" pip install --force-reinstall --no-deps --no-binary llama-cpp-python llama-cpp-python==0.3.35`
3. Comprobar la GPU (deben salir `True` y `True`):
   ```bash
   nvidia-smi
   python -c "import torch, llama_cpp; print(torch.cuda.is_available(), llama_cpp.llama_supports_gpu_offload())"
   ```
4. Índice congelado (el mismo en todas las máquinas): descargar de Drive el zip de
   `python -m src.index.paquete_colab --modo muestra --con-indice` y extraer **solo `build/`**
   (el resto del zip es código, que ya viene de git):
   ```bash
   unzip paquete_colab_muestra.zip 'build/*' -d .
   python -m src.index.build        # debe decir "reutilizado (sin cambios)"
   ```
5. `cp .env.example .env` (no hace falta la llave para responder; solo para evaluar con RAGAS).
6. Ensayo, que además descarga los modelos (~6 GB, la primera vez):
   ```bash
   python run.py --split sample --gpu --indice-existente --rango 1 3 --tag ensayo
   ```
   Debe terminar con "Listo: 3 nuevas … 0 con errores de esquema". Anotar los s/pregunta.

### 11.2 El comando
```bash
python run.py --split test --gpu --indice-existente --rango INICIO FIN --tag NOMBRE
```
| Opción | Para qué |
|---|---|
| `--split test` | Las preguntas del sábado: el archivo debe quedar en `data/test_992.jsonl` (`--split sample` = las 50 de muestra) |
| `--gpu` | Encoder, reranker y Qwen en CUDA |
| `--indice-existente` | Usa el índice de `build/` sin reconstruir nada; verifica sus sha256 y se detiene si no corresponden |
| `--rango INICIO FIN` | Solo las preguntas en esas posiciones del archivo, ambos extremos incluidos (1 = la primera). Sin `--rango`, todas |
| `--tag NOMBRE` | Carpeta de resultados `runs/NOMBRE/` (`submissions.jsonl`, `trazas.jsonl`, `tiempos.json`) |

- Escribe cada respuesta al terminarla: **si se interrumpe, se relanza el mismo comando** y
  sigue donde quedó.
- Las 50 de la muestra completas, con evaluación al final:
  `python run.py --split sample --gpu --indice-existente --tag muestra_turing`.

### 11.3 Repartir entre varias máquinas
Rangos contiguos que cubran todo, uno por máquina (con 4 GPUs):
```bash
python run.py --split test --gpu --indice-existente --rango 1 248   --tag sabado_1   # máquina 1
python run.py --split test --gpu --indice-existente --rango 249 496 --tag sabado_2   # máquina 2
python run.py --split test --gpu --indice-existente --rango 497 744 --tag sabado_3   # máquina 3
python run.py --split test --gpu --indice-existente --rango 745 992 --tag sabado_4   # máquina 4
```
Al final, en una sola máquina, reunir y validar:
```bash
cat runs/sabado_*/submissions.jsonl > submissions.jsonl
python -m src.eval.validar_entrega submissions.jsonl --split test
```
Con la muestra, la parte evaluable se arma igual (`cat` de las partes en un `submissions.jsonl`)
y se califica con `python scripts/evaluate.py --submission … --split sample`.
Plan detallado del día (tiempos, contingencias, verificación en vivo): `docs/RUNBOOK_SABADO.md`.

