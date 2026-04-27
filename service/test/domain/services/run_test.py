from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository
from domain.run.service import RunService


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


def _make_run(**kwargs: object) -> Run:
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


@pytest.fixture
def repo() -> FakeRunRepository:
    return FakeRunRepository()


@pytest.fixture
def service(repo: FakeRunRepository) -> RunService:
    return RunService(repo)


def test_get_all_returns_empty(service: RunService) -> None:
    assert service.get_all() == []


def test_get_all_returns_all(service: RunService, repo: FakeRunRepository) -> None:
    repo.create(_make_run(title="Alpha"))
    repo.create(_make_run(title="Beta"))
    assert len(service.get_all()) == 2


def test_get_by_id_returns_run(service: RunService, repo: FakeRunRepository) -> None:
    run = _make_run()
    repo.create(run)
    assert service.get_by_id(run.id) == run


def test_get_by_id_returns_none_when_not_found(service: RunService) -> None:
    assert service.get_by_id(uuid4()) is None


def test_create_assigns_id(service: RunService) -> None:
    run = service.create(project_id=uuid4(), title="Run", description="desc")
    assert run.id is not None


def test_create_ids_are_unique(service: RunService) -> None:
    r1 = service.create(project_id=uuid4(), title="Run 1", description="desc")
    r2 = service.create(project_id=uuid4(), title="Run 2", description="desc")
    assert r1.id != r2.id


def test_create_sets_status_to_queued(service: RunService) -> None:
    run = service.create(project_id=uuid4(), title="Run", description="desc")
    assert run.status == RunStatus.queued


def test_create_sets_created_at(service: RunService) -> None:
    before = datetime.now(timezone.utc)
    run = service.create(project_id=uuid4(), title="Run", description="desc")
    after = datetime.now(timezone.utc)
    assert before <= run.created_at <= after


def test_create_leaves_timing_fields_unset(service: RunService) -> None:
    run = service.create(project_id=uuid4(), title="Run", description="desc")
    assert run.started_at is None
    assert run.completed_at is None
    assert run.error_message is None


def test_create_sets_provided_fields(service: RunService) -> None:
    project_id = uuid4()
    run = service.create(project_id=project_id, title="My Run", description="My desc")
    assert run.project_id == project_id
    assert run.title == "My Run"
    assert run.description == "My desc"


def test_update_returns_updated_run(service: RunService, repo: FakeRunRepository) -> None:
    run = _make_run(title="Old", status=RunStatus.running)
    repo.create(run)
    updated_run = Run(
        id=run.id,
        project_id=run.project_id,
        title="New",
        description=run.description,
        status=run.status,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
    )
    result = service.update(updated_run)
    assert result is not None
    assert result.title == "New"


def test_update_preserves_status(service: RunService, repo: FakeRunRepository) -> None:
    run = _make_run(status=RunStatus.running)
    repo.create(run)
    updated_run = Run(
        id=run.id,
        project_id=run.project_id,
        title="New Title",
        description=run.description,
        status=run.status,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
    )
    result = service.update(updated_run)
    assert result is not None
    assert result.status == RunStatus.running


def test_update_returns_none_when_not_found(service: RunService) -> None:
    run = _make_run()
    assert service.update(run) is None


def test_delete_returns_true_when_deleted(service: RunService, repo: FakeRunRepository) -> None:
    run = _make_run()
    repo.create(run)
    assert service.delete(run.id) is True
    assert repo.get_by_id(run.id) is None


def test_delete_returns_false_when_not_found(service: RunService) -> None:
    assert service.delete(uuid4()) is False
