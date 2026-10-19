SHELL := /bin/bash
COMPOSE := docker compose -f ops/compose.yaml --env-file .env

.PHONY: install keys up down logs migrate seed test lint format typecheck limits check smoke contract

install:
	poetry install --with dev

keys:
	poetry run python ops/tools/dev_keys.py

up: keys
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

migrate:
	poetry run alembic -c api/alembic.ini upgrade head

seed:
	poetry run python -m identity.config.seed

test:
	poetry run pytest

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run pyright

limits:
	poetry run python ops/tools/check_line_limits.py

typecheck:
	poetry run pyright

format:
	poetry run ruff check --fix .
	poetry run black .

check: lint limits test

smoke:
	poetry run python ops/tools/smoke.py

contract:
	poetry run pytest shared/tests/test_routes.py

