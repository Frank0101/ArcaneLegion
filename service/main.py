from fastapi import FastAPI

from api.routes_health import router as health_router

app = FastAPI(title="ArcaneLegion", version="0.1.0")

app.include_router(health_router)
