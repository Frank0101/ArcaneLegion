import logging
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s: %(message)s")

from api.routes.health import router as health_router
from api.routes.project import router as project_router
from api.routes.run import router as run_router
from data.repositories.project import ProjectRepository
from data.repositories.run import RunRepository
from data.session import create_session
from domain.run.executor import RunExecutor
from domain.run.worker import RunWorker
from config import settings
from infra.agent_runtime_resolver import AgentRuntimeResolver
from infra.agent_runtimes.claude_code import ClaudeCodeAgentRuntime
from infra.agent_runtimes.stub import StubAgentRuntime
from infra.repo_manager_strategy import RepoManagerStrategy
from infra.lang_graph.lang_graph_manager import LangGraphManager
from infra.repo_managers.github import GitHubRepoManager


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    Path(settings.workspace_base_path).mkdir(exist_ok=True)
    session = create_session()
    worker = RunWorker(
        RunRepository(session),
        RunExecutor(
            LangGraphManager(),
            ProjectRepository(session),
            AgentRuntimeResolver(claude_code=ClaudeCodeAgentRuntime(), stub=StubAgentRuntime()),
            RepoManagerStrategy([GitHubRepoManager(settings.github_token)]),
            settings.workspace_base_path,
        ),
        poll_interval=settings.worker_poll_interval,
    )
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    yield


app = FastAPI(title="ArcaneLegion", version="0.1.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(project_router)
app.include_router(run_router)
