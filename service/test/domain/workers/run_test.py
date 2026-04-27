from datetime import datetime
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository
from domain.run.worker import RunWorker


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
        queued = [r for r in self._runs.values() if r.status == RunStatus.queued]
        return min(queued, key=lambda r: r.created_at) if queued else None


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
def worker(repo: FakeRunRepository) -> RunWorker:
    return RunWorker(repo, poll_interval=0)


def test_tick_sleeps_when_no_queued_run(worker: RunWorker) -> None:
    with patch("domain.run.worker.time.sleep") as mock_sleep:
        worker._tick()

    mock_sleep.assert_called_once_with(0)


def test_tick_marks_run_running_then_completed(worker: RunWorker, repo: FakeRunRepository) -> None:
    run = _make_run()
    repo.create(run)

    worker._tick()

    result = repo.get_by_id(run.id)
    assert result is not None
    assert result.status == RunStatus.completed
    assert result.started_at is not None
    assert result.completed_at is not None


class UpdateFailingOnCompletedRepository(FakeRunRepository):
    def update(self, run: Run) -> Run:
        if run.status == RunStatus.completed:
            raise RuntimeError("execution failed")
        return super().update(run)


def test_tick_marks_run_failed_when_execution_raises() -> None:
    repo = UpdateFailingOnCompletedRepository()
    run = _make_run()
    repo.create(run)

    RunWorker(repo, poll_interval=0)._tick()

    result = repo.get_by_id(run.id)
    assert result is not None
    assert result.status == RunStatus.failed
    assert result.error_message == "execution failed"
