from uuid import UUID

from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository


class ProjectRepository(AbstractProjectRepository):
    def get_all(self) -> list[Project]:
        pass

    def get_by_id(self, project_id: UUID) -> Project | None:
        pass

    def create(self, project: Project) -> Project:
        pass

    def update(self, project: Project) -> Project:
        pass

    def delete(self, project_id: UUID) -> None:
        pass
