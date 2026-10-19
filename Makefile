SHELL := /bin/bash
COMPOSE := docker compose -f ops/compose.yaml --env-file .env

.PHONY: install keys up down logs migrate seed test lint format typecheck limits check smoke profile contract android-contract-up android-contract-test android-contract-smoke android-contract-down

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
	poetry run alembic -c api/alembic.ini upgrade head

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

contract:
	poetry run python scripts/export_openapi.py
	poetry run python scripts/check_contract.py

android-contract-up: keys
	$(COMPOSE) up -d postgres mongo minio dex
	$(COMPOSE) run --rm identity alembic -c alembic.ini upgrade head
	$(COMPOSE) run --rm identity python -m identity.seed

android-contract-test:
	poetry run pytest -m "not e2e"
	poetry run python scripts/check_contract.py

android-contract-smoke:
	poetry run python scripts/smoke.py

android-contract-down:
	$(COMPOSE) down
