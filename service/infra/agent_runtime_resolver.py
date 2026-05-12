from abc import ABC, abstractmethod
from pathlib import Path

from domain.run.agent_runtime import AbstractAgentRuntime
from domain.run.models import AgentRole


class AbstractAgentRuntimeAdapter(ABC):
    @abstractmethod
    def run(self, instructions: str, workspace: str) -> str: ...


class AgentRuntimeResolver(AbstractAgentRuntime):
    def __init__(
            self,
            playbooks_path: Path,
            claude_code_api: AbstractAgentRuntimeAdapter,
            claude_code_sub: AbstractAgentRuntimeAdapter,
            codex_api: AbstractAgentRuntimeAdapter,
            stub: AbstractAgentRuntimeAdapter,
    ) -> None:
        self._claude_code_api = claude_code_api
        self._claude_code_sub = claude_code_sub
        self._codex_api = codex_api
        self._stub = stub

        self._playbooks: dict[AgentRole, str] = {
            role: path.read_text() if (path := playbooks_path / f"{role.value}.md").exists() else ""
            for role in AgentRole
        }

    def run(self, role: AgentRole, prompt: str, workspace: str) -> str:
        match role:
            case AgentRole.planner:
                runtime = self._claude_code_api
            case _:
                runtime = self._stub

        instructions = f"{self._playbooks[role]}\n\n---\n\n{prompt}"
        return runtime.run(instructions, workspace)
