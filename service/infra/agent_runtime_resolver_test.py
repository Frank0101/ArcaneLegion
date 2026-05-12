from domain.run.models import AgentRole
from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter, AgentRuntimeResolver


class _CapturingAdapter(AbstractAgentRuntimeAdapter):
    def __init__(self) -> None:
        self.prompt: str | None = None
        self.workspace: str | None = None

    def run(self, prompt: str, workspace: str) -> str:
        self.prompt = prompt
        self.workspace = workspace
        return "output"


class _FakeAdapter(AbstractAgentRuntimeAdapter):
    def run(self, prompt: str, workspace: str) -> str:
        return "stub output"


def test_planner_role_delegates_to_claude_code_api_adapter() -> None:
    claude_code_api = _CapturingAdapter()
    resolver = AgentRuntimeResolver(claude_code_api=claude_code_api, claude_code_sub=_FakeAdapter(),
                                    stub=_FakeAdapter())

    resolver.run(AgentRole.planner, "prompt", "/workspace")

    assert claude_code_api.prompt == "prompt"
    assert claude_code_api.workspace == "/workspace"


def test_non_planner_role_delegates_to_stub_adapter() -> None:
    stub = _CapturingAdapter()
    resolver = AgentRuntimeResolver(claude_code_api=_FakeAdapter(), claude_code_sub=_FakeAdapter(), stub=stub)

    resolver.run(AgentRole.coder, "prompt", "/workspace")

    assert stub.prompt == "prompt"
