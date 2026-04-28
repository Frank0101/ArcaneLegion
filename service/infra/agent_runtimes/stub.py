from domain.run.models import AgentRole
from domain.run.runtime import AbstractAgentRuntime


class StubAgentRuntime(AbstractAgentRuntime):
    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str:
        return "Stub plan output"
