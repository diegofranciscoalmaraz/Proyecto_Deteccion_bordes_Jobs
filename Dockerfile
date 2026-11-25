FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV INPUT_DIR=/data/entrada/imagenette2/val
ENV OUTPUT_DIR=/data/salida
ENV TOTAL_TASKS=16

CMD ["python", "app/worker.py"]
