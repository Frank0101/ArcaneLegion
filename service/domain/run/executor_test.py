from datetime import datetime
from typing import Optional
from uuid import uuid4

from domain.run.executor import RunExecutor
from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, ExecutionResult, Run, RunStatus


class _CapturingGraphManager(AbstractGraphManager):
    def __init__(self, result: ExecutionResult) -> None:
        self.received_agent: Optional[Agent] = None
        self._result = result

    def execute_graph(self, agent: Agent) -> ExecutionResult:
        self.received_agent = agent
        return self._result


def _make_run(**kwargs: object) -> Run:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "project_id": uuid4(),
        "title": "Test Run",
        "description": "A test run",
        "status": RunStatus.queued,
        "created_at": datetime(2026, 1, 1, 0, 0, 0),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
    }
    defaults.update(kwargs)
    return Run(**defaults)  # type: ignore[arg-type]


def test_execute_passes_coder_reviewer_chain_to_graph_manager() -> None:
    manager = _CapturingGraphManager(ExecutionResult(action_results={}))

    RunExecutor(manager).execute(_make_run())

    assert manager.received_agent is not None
    assert manager.received_agent.name == "coder"
    assert manager.received_agent.next is not None
    assert manager.received_agent.next.name == "reviewer"
    assert manager.received_agent.next.next is None


def test_execute_returns_graph_manager_result() -> None:
    expected = ExecutionResult(action_results={
        "reviewer": ActionResult(output="done", success=True)
    })
    manager = _CapturingGraphManager(expected)

    result = RunExecutor(manager).execute(_make_run())

    assert result is expected
