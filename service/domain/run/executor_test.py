from typing import Callable, Optional

from domain.run.executor import RunExecutor
from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, ExecutionResult, Run


class _CapturingGraphManager(AbstractGraphManager):
    def __init__(self, result: ExecutionResult) -> None:
        self.received_agent: Optional[Agent] = None
        self._result = result

    def execute_graph(self, agent: Agent) -> ExecutionResult:
        self.received_agent = agent
        return self._result


def test_execute_passes_coder_reviewer_chain_to_graph_manager(make_run: Callable[..., Run]) -> None:
    manager = _CapturingGraphManager(ExecutionResult(action_results={}))

    RunExecutor(manager).execute(make_run())

    assert manager.received_agent is not None
    assert manager.received_agent.name == "coder"
    assert manager.received_agent.next is not None
    assert manager.received_agent.next.name == "reviewer"
    assert manager.received_agent.next.next is None


def test_execute_returns_graph_manager_result(make_run: Callable[..., Run]) -> None:
    expected = ExecutionResult(action_results={
        "reviewer": ActionResult(output="done", approved=True)
    })
    manager = _CapturingGraphManager(expected)

    result = RunExecutor(manager).execute(make_run())

    assert result is expected
