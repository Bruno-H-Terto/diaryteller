FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY shared /app/shared
COPY speech /app/speech
RUN pip install --no-cache-dir poetry==2.5.1 \
    && cd /app/speech \
    && poetry install --only main

WORKDIR /app/speech
EXPOSE 8000
CMD ["uvicorn", "speech.app:app", "--host", "0.0.0.0", "--port", "8000"]
