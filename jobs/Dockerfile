FROM mongo:8 AS mongo-tools
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false POETRY_NO_INTERACTION=1
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*
COPY --from=mongo-tools /usr/bin/mongodump /usr/local/bin/mongodump
COPY --from=mongo-tools /usr/bin/mongorestore /usr/local/bin/mongorestore
WORKDIR /app
COPY packages /app/packages
COPY services /app/services
COPY jobs /app/jobs
RUN pip install --no-cache-dir poetry==2.5.1 \
    && cd /app/jobs \
    && poetry install --only main

WORKDIR /app/jobs
ENTRYPOINT ["poetry", "run", "diary-maintenance"]
CMD ["schedule"]
