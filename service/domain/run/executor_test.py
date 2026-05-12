from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import pytest

from domain.project.models import Project
from domain.project.repository import AbstractProjectRepository
from domain.run.agent_runtime import AbstractAgentRuntime
from domain.run.executor import RunExecutor
from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, AgentRole, ExecutionResult, Run
from domain.run.repo_manager import AbstractRepoManager


class _CapturingGraphManager(AbstractGraphManager):
    def __init__(self, result: ExecutionResult) -> None:
        self.received_agent: Agent | None = None
        self._result = result

    def execute_graph(self, agent: Agent) -> ExecutionResult:
        self.received_agent = agent
        return self._result


class _ActionExecutingGraphManager(AbstractGraphManager):
    def execute_graph(self, agent: Agent) -> ExecutionResult:
        result = ExecutionResult(action_results={})
        current: Agent | None = agent
        while current is not None:
            action_result = current.action(result)
            result = ExecutionResult(action_results={**result.action_results, current.role: action_result})
            current = current.next
        return result


class _FakeProjectRepository(AbstractProjectRepository):
    def __init__(self, projects: list[Project]) -> None:
        self._projects = {p.id: p for p in projects}

    def get_all(self) -> list[Project]: return list(self._projects.values())

    def get_by_id(self, project_id: UUID) -> Project | None: return self._projects.get(project_id)

    def create(self, project: Project) -> Project: return project

    def update(self, project: Project) -> Project: return project

    def delete(self, project_id: UUID) -> None: pass


class _FakeRepoManager(AbstractRepoManager):
    def clone(self, repo_url: str, branch: str, workspace: str) -> None: pass


class _CapturingRepoManager(AbstractRepoManager):
    def __init__(self) -> None:
        self.repo_url: str | None = None
        self.branch: str | None = None
        self.workspace: str | None = None

    def clone(self, repo_url: str, branch: str, workspace: str) -> None:
        self.repo_url = repo_url
        self.branch = branch
        self.workspace = workspace


class _WorkspaceObservingRepoManager(AbstractRepoManager):
    def __init__(self) -> None:
        self.workspace: str | None = None
        self.existed_at_clone: bool = False

    def clone(self, repo_url: str, branch: str, workspace: str) -> None:
        self.workspace = workspace
        self.existed_at_clone = Path(workspace).is_dir()


class _RaisingWorkspaceObservingRepoManager(_WorkspaceObservingRepoManager):
    def clone(self, repo_url: str, branch: str, workspace: str) -> None:
        super().clone(repo_url, branch, workspace)
        raise RuntimeError("clone failed")


class _FakeAgentRuntime(AbstractAgentRuntime):
    def run(self, role: AgentRole, prompt: str, workspace: str) -> str:
        return "fake plan"


class _CapturingAgentRuntime(AbstractAgentRuntime):
    def __init__(self) -> None:
        self.role: AgentRole | None = None
        self.prompt: str | None = None
        self.workspace: str | None = None

    def run(self, role: AgentRole, prompt: str, workspace: str) -> str:
        self.role = role
        self.prompt = prompt
        self.workspace = workspace
        return "captured"


def _make_executor(
        manager: AbstractGraphManager,
        project: Project,
        workspace_base_path: str,
        runtime: AbstractAgentRuntime | None = None,
        repo_manager: AbstractRepoManager | None = None,
) -> RunExecutor:
    return RunExecutor(
        manager,
        _FakeProjectRepository([project]),
        runtime or _FakeAgentRuntime(),
        repo_manager or _FakeRepoManager(),
        workspace_base_path,
    )


def test_execute_passes_planner_coder_reviewer_chain_to_graph_manager(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    manager = _CapturingGraphManager(ExecutionResult(action_results={}))

    _make_executor(manager, project, workspace_base_path).execute(run)

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
        workspace_base_path: str,
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    expected = ExecutionResult(action_results={
        AgentRole.reviewer: ActionResult(prompt="", output="done", approved=True)
    })
    manager = _CapturingGraphManager(expected)

    result = _make_executor(manager, project, workspace_base_path).execute(run)

    assert result is expected


def test_execute_raises_when_project_not_found(
        make_run: Callable[..., Run],
        workspace_base_path: str,
) -> None:
    run = make_run()
    executor = RunExecutor(
        _CapturingGraphManager(ExecutionResult(action_results={})),
        _FakeProjectRepository([]),
        _FakeAgentRuntime(),
        _FakeRepoManager(),
        workspace_base_path,
    )

    with pytest.raises(ValueError, match=str(run.project_id)):
        executor.execute(run)


def test_execute_creates_workspace_directory(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    repo_manager = _WorkspaceObservingRepoManager()

    _make_executor(_CapturingGraphManager(ExecutionResult(action_results={})), project, workspace_base_path,
                   repo_manager=repo_manager).execute(run)

    # The directory is gone by the time execute() returns, so we observe creation
    # from inside clone — the only hook that runs while the context manager is open.
    assert repo_manager.existed_at_clone is True


def test_execute_removes_workspace_directory(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    repo_manager = _WorkspaceObservingRepoManager()

    _make_executor(_CapturingGraphManager(ExecutionResult(action_results={})), project, workspace_base_path,
                   repo_manager=repo_manager).execute(run)

    assert repo_manager.workspace is not None
    assert not Path(repo_manager.workspace).exists()


def test_execute_removes_workspace_directory_on_exception(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    repo_manager = _RaisingWorkspaceObservingRepoManager()

    with pytest.raises(RuntimeError, match="clone failed"):
        _make_executor(_CapturingGraphManager(ExecutionResult(action_results={})), project, workspace_base_path,
                       repo_manager=repo_manager).execute(run)

    # The directory is gone once execute() unwinds, so existed_at_clone is the
    # only point where we can confirm it was created before being cleaned up.
    assert repo_manager.existed_at_clone is True
    assert not Path(repo_manager.workspace).exists()


def test_execute_clones_into_run_prefixed_subdirectory_of_workspace(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project()
    run = make_run(project_id=project.id)
    repo_manager = _CapturingRepoManager()

    _make_executor(_CapturingGraphManager(ExecutionResult(action_results={})), project, workspace_base_path,
                   repo_manager=repo_manager).execute(run)

    assert repo_manager.workspace is not None
    assert Path(repo_manager.workspace).parent == Path(workspace_base_path)
    assert Path(repo_manager.workspace).name.startswith(str(run.id))


def test_execute_clones_repo_with_project_url_and_branch(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project(repo_path="https://github.com/org/repo", default_branch="develop")
    run = make_run(project_id=project.id)
    repo_manager = _CapturingRepoManager()

    _make_executor(_CapturingGraphManager(ExecutionResult(action_results={})), project, workspace_base_path,
                   repo_manager=repo_manager).execute(run)

    assert repo_manager.repo_url == "https://github.com/org/repo"
    assert repo_manager.branch == "develop"


def test_execute_calls_planner_with_correct_role_and_prompt(
        make_run: Callable[..., Run],
        make_project: Callable[..., Project],
        workspace_base_path: str,
) -> None:
    project = make_project(default_branch="main")
    run = make_run(project_id=project.id, title="Fix login bug", description="Users cannot log in")
    runtime = _CapturingAgentRuntime()

    _make_executor(_ActionExecutingGraphManager(), project, workspace_base_path, runtime=runtime).execute(run)

    assert runtime.role == AgentRole.planner
    assert runtime.prompt == "# Task: Fix login bug\n\nUsers cannot log in"
    assert runtime.workspace is not None
