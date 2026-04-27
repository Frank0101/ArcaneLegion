from collections.abc import Generator
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data.base import Base
from data.models.project import ProjectRow
from data.repositories.run import RunRepository
from domain.run.models import Run, RunStatus

_CREATED_AT = datetime(2026, 1, 1, 0, 0, 0)
_STARTED_AT = datetime(2026, 1, 1, 0, 1, 0)
_COMPLETED_AT = datetime(2026, 1, 1, 0, 2, 0)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    db_session = session_factory()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def repo(session: Session) -> RunRepository:
    return RunRepository(session)


def make_run(
        run_id: UUID | None = None,
        project_id: UUID | None = None,
        title: str = "Test Run",
        description: str = "A test run",
        status: RunStatus = RunStatus.queued,
        created_at: datetime = _CREATED_AT,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
) -> Run:
    return Run(
        id=run_id or uuid4(),
        project_id=project_id or uuid4(),
        title=title,
        description=description,
        status=status,
        created_at=created_at,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
    )


def add_project(session: Session, project_id: UUID | None = None) -> UUID:
    resolved_project_id = project_id or uuid4()
    session.add(
        ProjectRow(
            id=resolved_project_id,
            name="Arcane",
            repo_path="/repos/arcane",
            default_branch="main",
        )
    )
    session.commit()
    return resolved_project_id


def test_create_and_get_by_id(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    run = make_run(project_id=project_id)

    created = repo.create(run)
    result = repo.get_by_id(run.id)

    assert created == run
    assert result == run


def test_create_with_optional_timestamps_and_error(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    run = make_run(
        project_id=project_id,
        status=RunStatus.failed,
        started_at=_STARTED_AT,
        completed_at=_COMPLETED_AT,
        error_message="boom",
    )

    repo.create(run)
    result = repo.get_by_id(run.id)

    assert result is not None
    assert result.status == RunStatus.failed
    assert result.started_at == _STARTED_AT
    assert result.completed_at == _COMPLETED_AT
    assert result.error_message == "boom"


def test_get_by_id_returns_none_when_not_found(repo: RunRepository) -> None:
    assert repo.get_by_id(uuid4()) is None


def test_get_all_returns_all_runs(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    first = make_run(project_id=project_id, title="Alpha")
    second = make_run(project_id=project_id, title="Beta")
    repo.create(first)
    repo.create(second)

    results = repo.get_all()

    assert {run.id for run in results} == {first.id, second.id}


def test_update_returns_updated_run(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    run = make_run(project_id=project_id)
    repo.create(run)
    updated = Run(
        id=run.id,
        project_id=project_id,
        title="Updated Run",
        description="Updated description",
        status=RunStatus.completed,
        created_at=run.created_at,
        started_at=_STARTED_AT,
        completed_at=_COMPLETED_AT,
        error_message=None,
    )

    result = repo.update(updated)

    assert result == updated
    assert repo.get_by_id(run.id) == updated


def test_update_raises_when_not_found(repo: RunRepository) -> None:
    run = make_run()

    with pytest.raises(ValueError, match=f"Run {run.id} not found"):
        repo.update(run)


def test_delete_removes_run(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    run = make_run(project_id=project_id)
    repo.create(run)

    repo.delete(run.id)

    assert repo.get_by_id(run.id) is None


def test_delete_ignores_missing_run(repo: RunRepository) -> None:
    repo.delete(uuid4())


def test_claim_oldest_queued_returns_none_when_no_queued_runs(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    repo.create(make_run(project_id=project_id, status=RunStatus.running))

    assert repo.claim_oldest_queued() is None


def test_claim_oldest_queued_returns_oldest_queued_run(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    older = make_run(project_id=project_id, created_at=datetime(2026, 1, 1))
    newer = make_run(project_id=project_id, created_at=datetime(2026, 1, 2))
    repo.create(newer)
    repo.create(older)

    result = repo.claim_oldest_queued()

    assert result is not None
    assert result.id == older.id


def test_claim_oldest_queued_ignores_non_queued_runs(repo: RunRepository, session: Session) -> None:
    project_id = add_project(session)
    repo.create(make_run(project_id=project_id, status=RunStatus.running))
    repo.create(make_run(project_id=project_id, status=RunStatus.completed))
    repo.create(make_run(project_id=project_id, status=RunStatus.failed))

    assert repo.claim_oldest_queued() is None
