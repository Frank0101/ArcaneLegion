from pathlib import Path

from domain.run.models import AgentRole
from infra.agent_runtime_resolver import AbstractAgentRuntimeAdapter, AgentRuntimeResolver


class _CapturingAdapter(AbstractAgentRuntimeAdapter):
    def __init__(self) -> None:
        self.instructions: str | None = None
        self.workspace: str | None = None

    def run(self, instructions: str, workspace: str) -> str:
        self.instructions = instructions
        self.workspace = workspace
        return "output"


class _FakeAdapter(AbstractAgentRuntimeAdapter):
    def run(self, instructions: str, workspace: str) -> str:
        return "stub output"


def _make_resolver(
        claude_code_api: AbstractAgentRuntimeAdapter,
        claude_code_sub: AbstractAgentRuntimeAdapter,
        codex_api: AbstractAgentRuntimeAdapter,
        stub: AbstractAgentRuntimeAdapter,
        playbooks_path: Path,
) -> AgentRuntimeResolver:
    return AgentRuntimeResolver(
        playbooks_path=playbooks_path,
        claude_code_api=claude_code_api,
        claude_code_sub=claude_code_sub,
        codex_api=codex_api,
        stub=stub,
    )


def test_planner_role_delegates_to_claude_code_api_adapter(tmp_path: Path) -> None:
    claude_code_api = _CapturingAdapter()
    resolver = _make_resolver(claude_code_api, _FakeAdapter(), _FakeAdapter(), _FakeAdapter(), tmp_path)

    resolver.run(AgentRole.planner, "prompt", "/workspace")

    assert claude_code_api.workspace == "/workspace"


def test_non_planner_role_delegates_to_stub_adapter(tmp_path: Path) -> None:
    stub = _CapturingAdapter()
    resolver = _make_resolver(_FakeAdapter(), _FakeAdapter(), _FakeAdapter(), stub, tmp_path)

    resolver.run(AgentRole.coder, "prompt", "/workspace")

    assert stub.workspace == "/workspace"


def test_playbook_is_prepended_to_prompt(tmp_path: Path) -> None:
    (tmp_path / "planner.md").write_text("playbook instructions")
    adapter = _CapturingAdapter()
    resolver = _make_resolver(adapter, _FakeAdapter(), _FakeAdapter(), _FakeAdapter(), tmp_path)

    resolver.run(AgentRole.planner, "task prompt", "/workspace")

    assert adapter.instructions == "playbook instructions\n\n---\n\ntask prompt"


def test_prompt_has_empty_playbook_prefix_when_no_playbook(tmp_path: Path) -> None:
    adapter = _CapturingAdapter()
    resolver = _make_resolver(adapter, _FakeAdapter(), _FakeAdapter(), _FakeAdapter(), tmp_path)

    resolver.run(AgentRole.planner, "task prompt", "/workspace")

    assert adapter.instructions == "\n\n---\n\ntask prompt"
