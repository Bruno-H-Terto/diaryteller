FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1

WORKDIR /app
COPY shared /app/shared
COPY memory_mcp /app/memory_mcp
RUN pip install --no-cache-dir poetry==2.5.1 \
    && cd /app/memory_mcp \
    && poetry install --only main

WORKDIR /app/memory_mcp
EXPOSE 8080
CMD ["uvicorn", "memory_mcp.app:app", "--host", "0.0.0.0", "--port", "8080"]
