from domain.run.models import AgentRole
from infra.agent_runtime_strategy import AbstractAgentRuntimeStrategy


class StubAgentRuntime(AbstractAgentRuntimeStrategy):
    @staticmethod
    def can_handle(role: AgentRole) -> bool:
        return True

    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str:
        return "Stub plan output"
