SHELL := /bin/bash
COMPOSE := docker compose -f ops/compose.yaml --env-file .env

.PHONY: install keys up down logs migrate seed test lint format typecheck limits check smoke profile

install:
	poetry install --with dev

keys:
	poetry run python scripts/dev_keys.py

up: keys
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

migrate:
	poetry run alembic -c services/identity/alembic.ini upgrade head

seed:
	poetry run python -m identity.seed

test:
	poetry run pytest

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run pyright

limits:
	poetry run python scripts/check_line_limits.py

typecheck:
	poetry run pyright

format:
	poetry run ruff check --fix .
	poetry run black .

check: lint limits test

smoke:
	poetry run python scripts/smoke.py

profile:
	poetry run python scripts/profile_memory.py
