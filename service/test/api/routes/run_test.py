from collections.abc import Generator
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.routes.run import get_repository
from domain.run.models import Run
from domain.run.repository import AbstractRunRepository
from main import app

_CREATED_AT = datetime(2026, 1, 1, 0, 0, 0)


def _make_run(**kwargs: object) -> Run:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "project_id": uuid4(),
        "title": "Test Run",
        "description": "A test run",
        "status": "pending",
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
        "status": "pending",
        "created_at": _CREATED_AT.isoformat(),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
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


@pytest.fixture
def repo() -> FakeRunRepository:
    return FakeRunRepository()


@pytest.fixture
def client(repo: FakeRunRepository) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_repository] = lambda: repo
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
    body = _run_body(title="My Run", status="running")
    response = client.post("/runs/", json=body)
    data = response.json()
    assert data["title"] == "My Run"
    assert data["status"] == "running"
    assert data["started_at"] is None
    assert data["error_message"] is None
    assert "id" in data


def test_create_run_with_optional_fields(client: TestClient) -> None:
    body = _run_body(
        started_at="2026-01-01T10:00:00",
        completed_at="2026-01-01T11:00:00",
        error_message="something failed",
    )
    response = client.post("/runs/", json=body)
    assert response.status_code == 201
    data = response.json()
    assert data["started_at"] is not None
    assert data["completed_at"] is not None
    assert data["error_message"] == "something failed"


def test_update_run_returns_updated(client: TestClient, repo: FakeRunRepository) -> None:
    run = _make_run(title="Old Title", status="pending")
    repo.create(run)
    body = _run_body(project_id=str(run.project_id), title="New Title", status="completed")
    response = client.put(f"/runs/{run.id}", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["status"] == "completed"


def test_update_run_returns_404_when_not_found(client: TestClient) -> None:
    response = client.put(f"/runs/{uuid4()}", json=_run_body())
    assert response.status_code == 404


def test_delete_run_returns_204(client: TestClient, repo: FakeRunRepository) -> None:
    run = _make_run()
    repo.create(run)
    response = client.delete(f"/runs/{run.id}")
    assert response.status_code == 204


def test_delete_run_returns_404_when_not_found(client: TestClient) -> None:
    response = client.delete(f"/runs/{uuid4()}")
    assert response.status_code == 404
