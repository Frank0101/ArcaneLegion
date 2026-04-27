import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.project import router as project_router
from api.routes.run import router as run_router
from data.repositories.run import RunRepository
from data.session import create_session
from domain.run.worker import RunWorker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    session = create_session()
    worker = RunWorker(RunRepository(session))
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    yield


app = FastAPI(title="ArcaneLegion", version="0.1.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(project_router)
app.include_router(run_router)
