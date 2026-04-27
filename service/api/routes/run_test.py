from collections.abc import Generator
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.routes.run import get_service
from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository
from domain.run.service import RunService
from main import app

_CREATED_AT = datetime(2026, 1, 1, 0, 0, 0)


def _make_run(**kwargs: object) -> Run:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "project_id": uuid4(),
        "title": "Test Run",
        "description": "A test run",
        "status": RunStatus.queued,
        "created_at": _CREATED_AT,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
    }
    defaults.update(kwargs)
    return Run(**defaults)  # type: ignore[arg-type]


def _run_body(**kwargs: object) -> dict[str, object]:
    defaults: dict[str, object] = {
        "project_id": str(uuid4()),
        "title": "Test Run",
        "description": "A test run",
    }
    defaults.update(kwargs)
    return defaults


class FakeRunRepository(AbstractRunRepository):
    def __init__(self) -> None:
        self._runs: dict[UUID, Run] = {}

    def get_all(self) -> list[Run]:
        return list(self._runs.values())

    def get_by_id(self, run_id: UUID) -> Run | None:
        return self._runs.get(run_id)

    def create(self, run: Run) -> Run:
        self._runs[run.id] = run
        return run

    def update(self, run: Run) -> Run:
        self._runs[run.id] = run
        return run

    def delete(self, run_id: UUID) -> None:
        self._runs.pop(run_id, None)

    def claim_oldest_queued(self) -> Run | None:
        raise NotImplementedError


@pytest.fixture
def repo() -> FakeRunRepository:
    return FakeRunRepository()


@pytest.fixture
def client(repo: FakeRunRepository) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_service] = lambda: RunService(repo)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_runs_returns_empty(client: TestClient) -> None:
    response = client.get("/runs/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_runs_returns_all(client: TestClient, repo: FakeRunRepository) -> None:
    repo.create(_make_run(title="Alpha"))
    repo.create(_make_run(title="Beta"))
    response = client.get("/runs/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_run_returns_run(client: TestClient, repo: FakeRunRepository) -> None:
    run = _make_run()
    repo.create(run)
    response = client.get(f"/runs/{run.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(run.id)


def test_get_run_returns_404_when_not_found(client: TestClient) -> None:
    response = client.get(f"/runs/{uuid4()}")
    assert response.status_code == 404


def test_create_run_returns_201(client: TestClient) -> None:
    response = client.post("/runs/", json=_run_body())
    assert response.status_code == 201


def test_create_run_returns_run(client: TestClient) -> None:
    body = _run_body(title="My Run")
    response = client.post("/runs/", json=body)
    data = response.json()
    assert data["title"] == "My Run"
    assert data["status"] == RunStatus.queued
    assert data["started_at"] is None
    assert data["error_message"] is None
    assert "id" in data
