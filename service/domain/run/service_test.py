from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository
from domain.run.service import RunService


@pytest.fixture
def service(repo: AbstractRunRepository) -> RunService:
    return RunService(repo)


def test_get_all_returns_empty(service: RunService) -> None:
    assert service.get_all() == []


def test_get_all_returns_all(
        service: RunService, repo: AbstractRunRepository, make_run: Callable[..., Run]
) -> None:
    repo.create(make_run(title="Alpha"))
    repo.create(make_run(title="Beta"))
    assert len(service.get_all()) == 2


def test_get_by_id_returns_run(
        service: RunService, repo: AbstractRunRepository, make_run: Callable[..., Run]
) -> None:
    run = make_run()
    repo.create(run)
    assert service.get_by_id(run.id) == run


def test_get_by_id_returns_none_when_not_found(service: RunService) -> None:
    assert service.get_by_id(uuid4()) is None


def test_create_ids_are_unique(service: RunService) -> None:
    r1 = service.create(project_id=uuid4(), title="Run 1", description="desc")
    r2 = service.create(project_id=uuid4(), title="Run 2", description="desc")
    assert r1.id != r2.id


def test_create_sets_created_at(service: RunService) -> None:
    before = datetime.now(timezone.utc)
    run = service.create(project_id=uuid4(), title="Run", description="desc")
    after = datetime.now(timezone.utc)
    assert before <= run.created_at <= after


def test_create_initial_state(service: RunService) -> None:
    project_id = uuid4()
    run = service.create(project_id=project_id, title="My Run", description="My desc")
    assert run.project_id == project_id
    assert run.title == "My Run"
    assert run.description == "My desc"
    assert run.status == RunStatus.queued
    assert run.started_at is None
    assert run.completed_at is None
    assert run.error_message is None
