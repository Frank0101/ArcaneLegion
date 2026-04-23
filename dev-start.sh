#!/bin/bash
set -e

export DATABASE_URL=postgresql+psycopg://arcane:arcane@localhost:5432/arcane_legion

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
