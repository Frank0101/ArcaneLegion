from collections.abc import Generator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.project import ProjectRequest, ProjectResponse
from data.repositories.project import ProjectRepository
from data.session import create_session
from domain.project.models import Project
from domain.project.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_session() -> Generator[Session, None, None]:
    session = create_session()
    try:
        yield session
    finally:
        session.close()


def get_repository(session: Session = Depends(get_session)) -> ProjectRepository:
    return ProjectRepository(session)


def get_service(repo: ProjectRepository = Depends(get_repository)) -> ProjectService:
    return ProjectService(repo)


@router.get("/", response_model=list[ProjectResponse])
def list_projects(service: ProjectService = Depends(get_service)) -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(p) for p in service.get_all()]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, service: ProjectService = Depends(get_service)) -> ProjectResponse:
    project = service.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectRequest, service: ProjectService = Depends(get_service)) -> ProjectResponse:
    project = service.create(
        name=body.name,
        repo_path=body.repo_path,
        default_branch=body.default_branch,
    )
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
        project_id: UUID,
        body: ProjectRequest,
        service: ProjectService = Depends(get_service),
) -> ProjectResponse:
    project = service.update(Project(
        id=project_id,
        name=body.name,
        repo_path=body.repo_path,
        default_branch=body.default_branch,
    ))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, service: ProjectService = Depends(get_service)) -> None:
    if not service.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
