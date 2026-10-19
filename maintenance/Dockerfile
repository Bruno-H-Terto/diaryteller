FROM mongo:8 AS mongo-tools
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*
COPY --from=mongo-tools /usr/bin/mongodump /usr/local/bin/mongodump
COPY --from=mongo-tools /usr/bin/mongorestore /usr/local/bin/mongorestore
WORKDIR /app
COPY shared /app/shared
COPY maintenance /app/maintenance
RUN pip install --no-cache-dir poetry==2.5.1 \
    && cd /app/maintenance \
    && poetry install --only main

WORKDIR /app/maintenance
ENTRYPOINT ["poetry", "run", "diary-maintenance"]
CMD ["schedule"]
