from uuid import UUID, uuid4

from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository


class ProjectService:
    def __init__(self, repo: AbstractProjectRepository) -> None:
        self._repo = repo

    def get_all(self) -> list[Project]:
        return self._repo.get_all()

    def get_by_id(self, project_id: UUID) -> Project | None:
        return self._repo.get_by_id(project_id)

    def create(self, name: str, repo_path: str, default_branch: str) -> Project:
        return self._repo.create(Project(
            id=uuid4(),
            name=name,
            repo_path=repo_path,
            default_branch=default_branch,
        ))

    def update(self, project: Project) -> Project | None:
        if self._repo.get_by_id(project.id) is None:
            return None
        return self._repo.update(project)

    def delete(self, project_id: UUID) -> bool:
        if self._repo.get_by_id(project_id) is None:
            return False
        self._repo.delete(project_id)
        return True
