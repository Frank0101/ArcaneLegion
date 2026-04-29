from abc import abstractmethod

from domain.run.agent_runtime import AbstractAgentRuntime
from domain.run.models import AgentRole


class AbstractAgentRuntimeStrategy(AbstractAgentRuntime):
    @staticmethod
    @abstractmethod
    def can_handle(role: AgentRole) -> bool: ...


class AgentRuntimeStrategy(AbstractAgentRuntime):
    def __init__(self, runtimes: list[AbstractAgentRuntimeStrategy]) -> None:
        self._runtimes = runtimes

    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str:
        for runtime in self._runtimes:
            if runtime.can_handle(role):
                return runtime.run(role, prompt, repo_path, branch)
        raise ValueError(f"No runtime available for role {role.value}")
