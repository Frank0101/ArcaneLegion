from collections.abc import Generator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.run import RunRequest, RunResponse
from data.repositories.run import RunRepository
from data.session import create_session
from domain.run.service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


def get_session() -> Generator[Session, None, None]:
    session = create_session()
    try:
        yield session
    finally:
        session.close()


def get_repository(session: Session = Depends(get_session)) -> RunRepository:
    return RunRepository(session)


def get_service(repo: RunRepository = Depends(get_repository)) -> RunService:
    return RunService(repo)


@router.get("/", response_model=list[RunResponse])
def list_runs(service: RunService = Depends(get_service)) -> list[RunResponse]:
    return [RunResponse.model_validate(r) for r in service.get_all()]


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: UUID, service: RunService = Depends(get_service)) -> RunResponse:
    run = service.get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate(run)


@router.post("/", response_model=RunResponse, status_code=201)
def create_run(body: RunRequest, service: RunService = Depends(get_service)) -> RunResponse:
    run = service.create(
        project_id=body.project_id,
        title=body.title,
        description=body.description,
    )
    return RunResponse.model_validate(run)
