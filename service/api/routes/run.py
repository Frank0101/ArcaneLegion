from collections.abc import Generator
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.run import RunResponse, RunRequest
from data.repositories.run import RunRepository
from data.session import create_session
from domain.run.models import Run

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
        status=body.status,
        created_at=body.created_at,
        started_at=body.started_at,
        completed_at=body.completed_at,
        error_message=body.error_message,
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
        status=body.status,
        created_at=body.created_at,
        started_at=body.started_at,
        completed_at=body.completed_at,
        error_message=body.error_message,
    ))
    return RunResponse.model_validate(updated)


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: UUID, repo: RunRepository = Depends(get_repository)) -> None:
    if repo.get_by_id(run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    repo.delete(run_id)
