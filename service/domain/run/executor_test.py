from typing import Callable, Optional
from uuid import UUID

from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository
from domain.run.executor import RunExecutor
from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, AgentRole, ExecutionResult, Run
from domain.run.runtime import AbstractAgentRuntime


class _CapturingGraphManager(AbstractGraphManager):
    def __init__(self, result: ExecutionResult) -> None:
        self.received_agent: Optional[Agent] = None
        self._result = result

    def execute_graph(self, agent: Agent) -> ExecutionResult:
        self.received_agent = agent
        return self._result


class _FakeProjectRepository(AbstractProjectRepository):
    def __init__(self, projects: list[Project]) -> None:
        self._projects = {p.id: p for p in projects}

    def get_all(self) -> list[Project]: return list(self._projects.values())

    def get_by_id(self, project_id: UUID) -> Project | None: return self._projects.get(project_id)

    def create(self, project: Project) -> Project: return project

    def update(self, project: Project) -> Project: return project

    def delete(self, project_id: UUID) -> None: pass


class _FakeAgentRuntime(AbstractAgentRuntime):
    def run(self, role: AgentRole, prompt: str, repo_path: str, branch: str) -> str:
        return "fake plan"


def test_execute_passes_planner_coder_reviewer_chain_to_graph_manager(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    manager = _CapturingGraphManager(ExecutionResult(action_results={}))

    RunExecutor(manager, _FakeProjectRepository([project]), _FakeAgentRuntime()).execute(run)

    assert manager.received_agent is not None
    assert manager.received_agent.role == AgentRole.planner
    assert manager.received_agent.next is not None
    assert manager.received_agent.next.role == AgentRole.coder
    assert manager.received_agent.next.next is not None
    assert manager.received_agent.next.next.role == AgentRole.reviewer
    assert manager.received_agent.next.next.next is None


def test_execute_returns_graph_manager_result(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    expected = ExecutionResult(action_results={
        AgentRole.reviewer: ActionResult(output="done", approved=True)
    })
    manager = _CapturingGraphManager(expected)

    result = RunExecutor(manager, _FakeProjectRepository([project]), _FakeAgentRuntime()).execute(run)

    assert result is expected
