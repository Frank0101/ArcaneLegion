# ArcaneLegion

## Running the service

**With Docker (recommended)**

```bash
docker compose up --build
```

**Locally**

```bash
cd service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The service will be available at `http://localhost:8000`. Health check: `GET /health`.
