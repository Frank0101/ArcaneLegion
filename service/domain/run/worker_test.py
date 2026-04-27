from typing import Callable
from unittest.mock import patch

import pytest

from domain.run.executor import RunExecutor
from domain.run.models import ExecutionResult, Run, RunStatus
from domain.run.repository import AbstractRunRepository
from domain.run.worker import RunWorker


class FakeRunExecutor(RunExecutor):
    def __init__(self) -> None:
        pass

    def execute(self, _run: Run) -> ExecutionResult:
        return ExecutionResult(action_results={})


class FailingRunExecutor(RunExecutor):
    def __init__(self) -> None:
        pass

    def execute(self, _run: Run) -> ExecutionResult:
        raise RuntimeError("execution failed")


@pytest.fixture
def executor() -> FakeRunExecutor:
    return FakeRunExecutor()


@pytest.fixture
def worker(repo: AbstractRunRepository, executor: FakeRunExecutor) -> RunWorker:
    return RunWorker(repo, executor, poll_interval=0)


def test_tick_sleeps_when_no_queued_run(worker: RunWorker) -> None:
    with patch("domain.run.worker.time.sleep") as mock_sleep:
        worker._tick()

    mock_sleep.assert_called_once_with(0)


def test_tick_marks_run_running_then_completed(
        worker: RunWorker, repo: AbstractRunRepository, make_run: Callable[..., Run]
) -> None:
    run = make_run()
    repo.create(run)

    worker._tick()

    result = repo.get_by_id(run.id)
    assert result is not None
    assert result.status == RunStatus.completed
    assert result.started_at is not None
    assert result.completed_at is not None


def test_tick_marks_run_failed_when_execution_raises(
        repo: AbstractRunRepository, make_run: Callable[..., Run]
) -> None:
    run = make_run()
    repo.create(run)

    RunWorker(repo, FailingRunExecutor(), poll_interval=0)._tick()

    result = repo.get_by_id(run.id)
    assert result is not None
    assert result.status == RunStatus.failed
    assert result.error_message == "execution failed"
