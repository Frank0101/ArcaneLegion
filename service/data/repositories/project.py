from uuid import UUID

from sqlalchemy.orm import Session

from data.models.project import ProjectRow
from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository


def _to_domain(row: ProjectRow) -> Project:
    return Project(
        id=row.id,
        name=row.name,
        repo_path=row.repo_path,
        default_branch=row.default_branch,
    )


class ProjectRepository(AbstractProjectRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[Project]:
        rows = self._session.query(ProjectRow).all()
        return [_to_domain(row) for row in rows]

    def get_by_id(self, project_id: UUID) -> Project | None:
        row = self._session.get(ProjectRow, project_id)
        return _to_domain(row) if row else None

    def create(self, project: Project) -> Project:
        row = ProjectRow(
            id=project.id,
            name=project.name,
            repo_path=project.repo_path,
            default_branch=project.default_branch,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_domain(row)

    def update(self, project: Project) -> Project:
        row = self._session.get(ProjectRow, project.id)
        if row is None:
            raise ValueError(f"Project {project.id} not found")
        row.name = project.name
        row.repo_path = project.repo_path
        row.default_branch = project.default_branch
        self._session.commit()
        self._session.refresh(row)
        return _to_domain(row)

    def delete(self, project_id: UUID) -> None:
        row = self._session.get(ProjectRow, project_id)
        if row is not None:
            self._session.delete(row)
            self._session.commit()
