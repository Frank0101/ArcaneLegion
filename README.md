# ArcaneLegion

## Running the service

### Docker Compose setup

Two compose files are used:

- `docker-compose.yml` — base config, used in all environments
- `docker-compose.override.yml` — dev-only additions (volume mount + `--reload`), automatically merged by Docker Compose when running locally

**Dev (default)**

```bash
docker compose up --build
```

Docker Compose automatically merges the override, giving you live reload on code changes without rebuilding the image.

**Prod (base only)**

```bash
docker compose -f docker-compose.yml up
```

Runs only the base config — no volume mount, no `--reload`.

### Locally (without Docker)

```bash
cd service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
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
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
