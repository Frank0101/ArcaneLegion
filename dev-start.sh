#!/bin/bash
set -e

set -a
source "$(dirname "$0")/.env"
set +a

# Override .env's DATABASE_URL (which uses the Docker-internal host "postgres") with localhost,
# since alembic and uvicorn run on the host machine and reach the container via the mapped port.
export DATABASE_URL=postgresql+psycopg://arcane:arcane@localhost:5432/arcane_legion

echo "==> Checking dependencies..."
for cmd in docker python3 git node npm claude codex; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: '$cmd' is not installed or not in PATH" >&2
        exit 1
    fi
done

echo "==> Starting PostgreSQL..."
docker compose up postgres -d --wait

echo "==> Setting up virtual environment..."
cd service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

echo "==> Running migrations..."
.venv/bin/python -m alembic upgrade head

echo "==> Starting service..."
.venv/bin/uvicorn main:app --reload
