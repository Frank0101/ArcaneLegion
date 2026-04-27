from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository


class RunService:
    def __init__(self, repo: AbstractRunRepository) -> None:
        self._repo = repo

    def get_all(self) -> list[Run]:
        return self._repo.get_all()

    def get_by_id(self, run_id: UUID) -> Run | None:
        return self._repo.get_by_id(run_id)

    def create(self, project_id: UUID, title: str, description: str) -> Run:
        return self._repo.create(Run(
            id=uuid4(),
            project_id=project_id,
            title=title,
            description=description,
            status=RunStatus.queued,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
            error_message=None,
        ))

    def update(self, run: Run) -> Run | None:
        if self._repo.get_by_id(run.id) is None:
            return None
        return self._repo.update(run)

    def delete(self, run_id: UUID) -> bool:
        if self._repo.get_by_id(run_id) is None:
            return False
        self._repo.delete(run_id)
        return True
