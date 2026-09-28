# Contenedor limpio para la verificación de reproducibilidad.
#   docker build -t hackathon-rag .
#   docker run --rm --env-file .env -v hf-cache:/root/.cache/huggingface hackathon-rag
# El corpus e índice se descargan de CORPUS_ZIP_URL (declarado en .env / --env-file);
# los modelos abiertos (bge-m3, bge-reranker-v2-m3, Qwen3-8B GGUF) se descargan de Hugging Face.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EN_CONTENEDOR=1 \
    CORPUS_SOURCE=nube

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["bash", "run.sh"]
