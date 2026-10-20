SHELL := /bin/bash
COMPOSE := docker compose -f ops/compose.yaml --env-file .env

.PHONY: install keys up down logs migrate seed test lint format typecheck limits check smoke contract i18n test-env test-env-down test-env-status studio app model

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

i18n:
	poetry run python ops/tools/i18n.py build

model:
	poetry run python ops/tools/fetch_models.py pt

limits:
	poetry run python ops/tools/check_line_limits.py
	poetry run python ops/tools/i18n.py check

typecheck:
	poetry run pyright

format:
	poetry run ruff check --fix .
	poetry run black .

check: lint limits test

test-env:
	poetry run python ops/tools/testenv.py up

test-env-down:
	poetry run python ops/tools/testenv.py down

test-env-status:
	poetry run python ops/tools/testenv.py status

app:
	poetry run python ops/tools/testenv.py up

studio:
	poetry run python -m ops.studio

smoke:
	poetry run python ops/tools/smoke.py

contract:
	poetry run pytest shared/tests/test_routes.py

