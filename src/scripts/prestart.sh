#! /usr/bin/env bash

set -e
set -x

# Run migrations
uv run --no-dev alembic upgrade head
