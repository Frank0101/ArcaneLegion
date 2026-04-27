from abc import ABC, abstractmethod

from domain.run.models import ExecutionResult, Run


class AbstractGraphManager(ABC):
    @abstractmethod
    def execute(self, run: Run) -> ExecutionResult: ...
