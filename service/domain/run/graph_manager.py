from abc import ABC, abstractmethod

from domain.run.models import Agent, ExecutionResult


class AbstractGraphManager(ABC):
    @abstractmethod
    def execute_graph(self, agent: Agent) -> ExecutionResult: ...
