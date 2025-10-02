SHELL := /bin/bash

.PHONY: format lint test prestart

format:
	uv run ruff check src --fix
	uv run ruff format src

lint:
	uv run mypy src/
	uv run ruff check src/
	uv run ruff format src --check

test:
	docker-compose up -d db
	uv run coverage run --source=src -m pytest
	uv run coverage report --show-missing
	uv run coverage html --title "coverage"

prestart:
	uv run alembic upgrade head

create-migration:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

start:
	docker-compose up --build