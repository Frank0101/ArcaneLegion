from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from domain.project.models import Project
from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository


class _FakeRunRepository(AbstractRunRepository):
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
        queued = [r for r in self._runs.values() if r.status == RunStatus.queued]
        return min(queued, key=lambda r: r.created_at) if queued else None


@pytest.fixture
def repo() -> _FakeRunRepository:
    return _FakeRunRepository()


@pytest.fixture
def make_project() -> Callable[..., Project]:
    def _factory(**kwargs: object) -> Project:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "name": "Test Project",
            "repo_path": "/tmp/repo",
            "default_branch": "main",
        }
        defaults.update(kwargs)
        return Project(**defaults)  # type: ignore[arg-type]

    return _factory


@pytest.fixture
def make_run() -> Callable[..., Run]:
    def _factory(**kwargs: object) -> Run:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "project_id": uuid4(),
            "title": "Test Run",
            "description": "A test run",
            "status": RunStatus.queued,
            "created_at": datetime(2026, 1, 1, 0, 0, 0),
            "started_at": None,
            "completed_at": None,
            "error_message": None,
        }
        defaults.update(kwargs)
        return Run(**defaults)  # type: ignore[arg-type]

    return _factory
