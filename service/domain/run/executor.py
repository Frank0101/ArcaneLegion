from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ExecutionResult, Run


class RunExecutor:
    def __init__(self, graph_manager: AbstractGraphManager) -> None:
        self._graph_manager = graph_manager

    def execute(self, run: Run) -> ExecutionResult:
        return self._graph_manager.execute(run)
