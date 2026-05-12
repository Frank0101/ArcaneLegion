from abc import ABC, abstractmethod

from domain.run.agent_runtime import AbstractAgentRuntime
from domain.run.models import AgentRole


class AbstractAgentRuntimeAdapter(ABC):
    @abstractmethod
    def run(self, prompt: str, workspace: str) -> str: ...


class AgentRuntimeResolver(AbstractAgentRuntime):
    def __init__(
            self,
            claude_code_api: AbstractAgentRuntimeAdapter,
            claude_code_sub: AbstractAgentRuntimeAdapter,
            stub: AbstractAgentRuntimeAdapter,
    ) -> None:
        self._claude_code_api = claude_code_api
        self._claude_code_sub = claude_code_sub
        self._stub = stub

    def run(self, role: AgentRole, prompt: str, workspace: str) -> str:
        match role:
            case AgentRole.planner:
                runtime = self._claude_code_api
            case _:
                runtime = self._stub
        return runtime.run(prompt, workspace)
