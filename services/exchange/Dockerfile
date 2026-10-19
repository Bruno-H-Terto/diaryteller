FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY packages /app/packages
COPY services /app/services
RUN pip install --no-cache-dir poetry==2.5.1 \
    && cd /app/services/exchange \
    && poetry install --only main

WORKDIR /app/services/exchange
EXPOSE 8000
CMD ["sh", "-c", "alembic -c alembic.ini upgrade head && uvicorn exchange.main:app --host 0.0.0.0 --port 8000"]
