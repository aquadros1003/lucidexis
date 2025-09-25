SHELL := /bin/bash

.PHONY: format lint test prestart

format:
	uv run ruff check src scripts --fix
	uv run ruff format src scripts

lint:
	uv run ruff check src scripts
	uv run ruff format src scripts --check

test:
	docker-compose up -d db
	uv run coverage run --source=src -m pytest
	uv run coverage report --show-missing
	uv run coverage html --title "coverage"

prestart:
	uv run python src/backend_pre_start.py
	uv run alembic upgrade head
	uv run python src/initial_data.py
