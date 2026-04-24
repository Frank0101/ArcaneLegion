from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.project import router as project_router

app = FastAPI(title="ArcaneLegion", version="0.1.0")

app.include_router(health_router)
app.include_router(project_router)
