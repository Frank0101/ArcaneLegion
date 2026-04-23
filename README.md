# ArcaneLegion

## Table of Contents

- [Running the service](#running-the-service)
  - [Docker Compose setup](#docker-compose-setup)
  - [Locally (without Docker)](#locally-without-docker)
- [Running the tests](#running-the-tests)
- [API Documentation](#api-documentation)
- [Database](#database)
  - [Inspecting PostgreSQL locally](#inspecting-postgresql-locally)
  - [Generating a new migration](#generating-a-new-migration)
  - [Running migrations manually](#running-migrations-manually)

## Running the service

### Docker Compose setup

Two compose files are used:

- `docker-compose.yml` — base config, used in all environments
- `docker-compose.override.yml` — dev-only additions (volume mount + `--reload`), automatically merged by Docker Compose when running locally

**Dev (default)**

```bash
docker compose up --build
```

This starts the following services:
- **postgres** — PostgreSQL 16 on port `5432`
- **migrate** — runs `python -m alembic upgrade head` on startup, then exits
- **test** — runs the test suite, then exits (service only starts if tests pass)
- **service** — FastAPI on port `8000` (starts only after migrations and tests succeed)

Docker Compose automatically merges the override, giving you live reload on code changes without rebuilding the image.

**Prod (base only)**

```bash
docker compose -f docker-compose.yml up
```

Runs only the base config — no volume mount, no `--reload`.

### Locally (without Docker)

Unlike Docker Compose, running locally does not automatically start PostgreSQL or run migrations. Use the provided script which handles everything in sequence:

```bash
./dev-start.sh
```

The service will be available at `http://localhost:8000`. Health check: `GET /health`.

## Running the tests

```bash
cd service
source .venv/bin/activate
python -m pytest test/ -v
```

If you haven't set up the virtual environment yet, do so first:

```bash
cd service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API Documentation

FastAPI automatically generates interactive docs. Once the service is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database

### Inspecting PostgreSQL locally

PostgreSQL is exposed on port `5432`. Connect via psql inside the container:

```bash
docker exec -it arcane-legion-postgres psql -U arcane -d arcane_legion
```

Or from your host if psql is installed:

```bash
psql postgresql://arcane:arcane@localhost:5432/arcane_legion
```

Useful psql commands:

```
\dt          -- list all tables
\d <table>   -- describe a table schema
\q           -- quit
```

### Generating a new migration

After adding or modifying a model in `data/models/`, generate a migration from `service/` with `DATABASE_URL` set:

```bash
python -m alembic revision --autogenerate -m "short description of change"
```

Alembic will compare the current models against the database schema and write a new migration file to `data/infra/alembic/versions/`. Review the generated file before applying it.

### Running migrations manually

Migrations run automatically on `docker compose up` via the `migrate` service. To run them manually:

```bash
docker compose run --rm migrate
```

Or directly from `service/` (with `DATABASE_URL` set):

```bash
python -m alembic upgrade head
```
