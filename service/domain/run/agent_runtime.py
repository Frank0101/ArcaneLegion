from abc import ABC, abstractmethod

from domain.run.models import AgentRole


class AbstractAgentRuntime(ABC):
    @abstractmethod
    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str: ...
