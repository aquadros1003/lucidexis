SHELL := /bin/bash

.PHONY: format lint test prestart create-migration start

format:
	uv run ruff check src --fix
	uv run ruff format src

lint:
	uv run mypy src/
	uv run ruff format src --check

test:
	docker-compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 3
	@docker-compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS testdb;" || true
	@docker-compose exec -T db psql -U postgres -d postgres -c "CREATE DATABASE testdb;" || true
	uv run alembic -x db_url=postgresql+psycopg://postgres:password@localhost:5432/testdb upgrade head
	uv run coverage report --show-missing
	uv run coverage run --source=src -m pytest

prestart:
	uv run alembic upgrade head

create-migration:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

start:
	docker-compose up --build