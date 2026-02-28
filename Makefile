SHELL := /bin/bash

.PHONY: format lint test prestart create-migration start

format:
	uv run ruff check src --fix
	uv run ruff format src

lint:
	uv run mypy src/
	uv run ruff format src --check

test:
	@postgres_output=$$(docker compose up -d db 2>&1); \
	if [[ $$postgres_output =~ Creating|Starting ]]; then \
		echo "Waiting for database to start..."; \
		sleep 5; \
	fi
	@postgres_container=$$(docker ps | grep db | cut -f1 -d ' ')
	docker exec -i $$postgres_container psql -U postgres -c 'CREATE EXTENSION IF NOT EXISTS vector;' > /dev/null 2>&1 || true
	docker exec -i $$postgres_container psql -U postgres -c 'create database testdb' > /dev/null 2>&1 || true
	docker exec -i $$postgres_container psql -U postgres -d testdb -c 'CREATE EXTENSION IF NOT EXISTS vector;' > /dev/null 2>&1 || true
	uv run alembic -x db_url=postgresql+psycopg://postgres:password@localhost:5432/testdb upgrade head
	uv run coverage run --source=src -m pytest
	uv run coverage report

prestart:
	uv run alembic upgrade head

create-migration:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

start:
	docker-compose up --build