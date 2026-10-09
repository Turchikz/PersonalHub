FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIPER_VOICE=ru_RU-denis-medium \
    PIPER_MODELS_DIR=/models

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app.py start.py ./
RUN mkdir -p /models

EXPOSE 5000
ENTRYPOINT ["python", "/app/start.py"]
