from uuid import UUID

from sqlalchemy.orm import Session

from data.models.run import RunRow
from domain.run.models import Run, RunStatus
from domain.run.repository import AbstractRunRepository


def _to_domain(row: RunRow) -> Run:
    return Run(
        id=row.id,
        project_id=row.project_id,
        title=row.title,
        description=row.description,
        status=row.status,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        error_message=row.error_message,
    )


class RunRepository(AbstractRunRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[Run]:
        rows = self._session.query(RunRow).all()
        return [_to_domain(row) for row in rows]

    def get_by_id(self, project_id: UUID) -> Run | None:
        row = self._session.get(RunRow, project_id)
        return _to_domain(row) if row else None

    def create(self, run: Run) -> Run:
        row = RunRow(
            id=run.id,
            project_id=run.project_id,
            title=run.title,
            description=run.description,
            status=run.status,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_message=run.error_message,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_domain(row)

    def update(self, run: Run) -> Run:
        row = self._session.get(RunRow, run.id)
        if row is None:
            raise ValueError(f"Run {run.id} not found")
        row.id = run.id
        row.project_id = run.project_id
        row.title = run.title
        row.description = run.description
        row.status = run.status
        row.created_at = run.created_at
        row.started_at = run.started_at
        row.completed_at = run.completed_at
        row.error_message = run.error_message
        self._session.commit()
        self._session.refresh(row)
        return _to_domain(row)

    def delete(self, project_id: UUID) -> None:
        row = self._session.get(RunRow, project_id)
        if row is not None:
            self._session.delete(row)
            self._session.commit()

    def claim_oldest_queued(self) -> Run | None:
        row = (
            self._session.query(RunRow)
            .filter(RunRow.status == RunStatus.queued)
            .order_by(RunRow.created_at.asc())
            .with_for_update(skip_locked=True)
            .first()
        )
        return _to_domain(row) if row else None
