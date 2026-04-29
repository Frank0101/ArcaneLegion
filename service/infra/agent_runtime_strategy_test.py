import pytest

from domain.run.models import AgentRole
from infra.agent_runtime_strategy import AbstractAgentRuntimeStrategy, AgentRuntimeStrategy


class _MatchingRuntime(AbstractAgentRuntimeStrategy):
    def __init__(self) -> None:
        self.called = False

    @staticmethod
    def can_handle(role: AgentRole) -> bool:
        return True

    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str:
        self.called = True
        return "output"


class _NonMatchingRuntime(AbstractAgentRuntimeStrategy):
    @staticmethod
    def can_handle(role: AgentRole) -> bool:
        return False

    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str:
        raise AssertionError("should not be called")


def test_run_delegates_to_matching_runtime() -> None:
    runtime = _MatchingRuntime()

    AgentRuntimeStrategy([runtime]).run(AgentRole.planner, "prompt", "/repo", "main")

    assert runtime.called is True


def test_run_raises_when_no_runtime_matches() -> None:
    with pytest.raises(ValueError, match=AgentRole.planner.value):
        AgentRuntimeStrategy([_NonMatchingRuntime()]).run(AgentRole.planner, "prompt", "/repo", "main")
