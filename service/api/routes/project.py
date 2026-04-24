from collections.abc import Generator
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.project import ProjectRequest, ProjectResponse
from data.repositories.project import ProjectRepository
from data.session import create_session
from domain.project.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


def get_session() -> Generator[Session, None, None]:
    session = create_session()
    try:
        yield session
    finally:
        session.close()


def get_repository(session: Session = Depends(get_session)) -> ProjectRepository:
    return ProjectRepository(session)


@router.get("/", response_model=list[ProjectResponse])
def list_projects(repo: ProjectRepository = Depends(get_repository)) -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(p) for p in repo.get_all()]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, repo: ProjectRepository = Depends(get_repository)) -> ProjectResponse:
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectRequest, repo: ProjectRepository = Depends(get_repository)) -> ProjectResponse:
    project = repo.create(Project(
        id=uuid4(),
        name=body.name,
        repo_path=body.repo_path,
        default_branch=body.default_branch,
    ))
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
        project_id: UUID,
        body: ProjectRequest,
        repo: ProjectRepository = Depends(get_repository),
) -> ProjectResponse:
    existing = repo.get_by_id(project_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Project not found")
    updated = repo.update(Project(
        id=project_id,
        name=body.name,
        repo_path=body.repo_path,
        default_branch=body.default_branch,
    ))
    return ProjectResponse.model_validate(updated)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: UUID, repo: ProjectRepository = Depends(get_repository)) -> None:
    if repo.get_by_id(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    repo.delete(project_id)
