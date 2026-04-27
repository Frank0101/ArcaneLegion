from collections.abc import Generator
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.run import RunResponse, RunRequest
from data.repositories.run import RunRepository
from data.session import create_session
from domain.run.models import Run, RunStatus

router = APIRouter(prefix="/runs", tags=["runs"])


def get_session() -> Generator[Session, None, None]:
    session = create_session()
    try:
        yield session
    finally:
        session.close()


def get_repository(session: Session = Depends(get_session)) -> RunRepository:
    return RunRepository(session)


@router.get("/", response_model=list[RunResponse])
def list_runs(repo: RunRepository = Depends(get_repository)) -> list[RunResponse]:
    return [RunResponse.model_validate(p) for p in repo.get_all()]


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: UUID, repo: RunRepository = Depends(get_repository)) -> RunResponse:
    run = repo.get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate(run)


@router.post("/", response_model=RunResponse, status_code=201)
def create_run(body: RunRequest, repo: RunRepository = Depends(get_repository)) -> RunResponse:
    run = repo.create(Run(
        id=uuid4(),
        project_id=body.project_id,
        title=body.title,
        description=body.description,
        status=RunStatus.queued,
        created_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None,
        error_message=None,
    ))
    return RunResponse.model_validate(run)


@router.put("/{run_id}", response_model=RunResponse)
def update_run(
        run_id: UUID,
        body: RunRequest,
        repo: RunRepository = Depends(get_repository),
) -> RunResponse:
    existing = repo.get_by_id(run_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Run not found")
    updated = repo.update(Run(
        id=run_id,
        project_id=body.project_id,
        title=body.title,
        description=body.description,
        status=existing.status,
        created_at=existing.created_at,
        started_at=existing.started_at,
        completed_at=existing.completed_at,
        error_message=existing.error_message,
    ))
    return RunResponse.model_validate(updated)


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: UUID, repo: RunRepository = Depends(get_repository)) -> None:
    if repo.get_by_id(run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    repo.delete(run_id)
