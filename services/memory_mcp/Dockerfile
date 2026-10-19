FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1

WORKDIR /app
COPY packages /app/packages
COPY services /app/services
RUN pip install --no-cache-dir poetry==2.5.1 \
    && cd /app/services/memory_mcp \
    && poetry install --only main

WORKDIR /app/services/memory_mcp
EXPOSE 8080
CMD ["uvicorn", "memory_mcp.main:app", "--host", "0.0.0.0", "--port", "8080"]
