from abc import ABC, abstractmethod
from uuid import UUID

from domain.run.models import Run


class AbstractRunRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[Run]: ...

    @abstractmethod
    def get_by_id(self, run_id: UUID) -> Run | None: ...

    @abstractmethod
    def create(self, run: Run) -> Run: ...

    @abstractmethod
    def update(self, run: Run) -> Run: ...

    @abstractmethod
    def delete(self, run_id: UUID) -> None: ...

    @abstractmethod
    def claim_oldest_queued(self) -> Run | None: ...
