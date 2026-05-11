import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

from domain.project.repository import AbstractProjectRepository
from domain.run.agent_runtime import AbstractAgentRuntime
from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, AgentRole, ExecutionResult, Run
from domain.run.repo_manager import AbstractRepoManager

logger = logging.getLogger(__name__)


def _logged(
        role: AgentRole,
        action: Callable[[ExecutionResult], ActionResult],
) -> Callable[[ExecutionResult], ActionResult]:
    def wrapped(so_far: ExecutionResult) -> ActionResult:
        logger.info("Agent %s starting", role.value)
        result = action(so_far)
        logger.info("Agent %s completed", role.value)
        return result

    return wrapped


class RunExecutor:
    def __init__(
            self,
            graph_manager: AbstractGraphManager,
            project_repo: AbstractProjectRepository,
            agent_runtime: AbstractAgentRuntime,
            repo_manager: AbstractRepoManager,
            workspace_base_path: str,
    ) -> None:
        self._graph_manager = graph_manager
        self._project_repo = project_repo
        self._agent_runtime = agent_runtime
        self._repo_manager = repo_manager
        self._workspace_base_path = Path(workspace_base_path)

    def execute(self, run: Run) -> ExecutionResult:
        project = self._project_repo.get_by_id(run.project_id)
        if project is None:
            raise ValueError(f"Project {run.project_id} not found")

        with tempfile.TemporaryDirectory(prefix=f"{str(run.id)}_", dir=self._workspace_base_path) as workspace:
            logger.info("Temporary workspace created: %s", workspace)

            self._repo_manager.clone(project.repo_path, project.default_branch, workspace)
            logger.info("Repo %s (branch=%s) cloned to workspace", project.repo_path, project.default_branch)

            def planner_action(_) -> ActionResult:
                prompt = f"Task: {run.title}\n\n{run.description}"
                output = self._agent_runtime.run(AgentRole.planner, prompt, workspace)
                return ActionResult(output=output)

            def coder_action(so_far: ExecutionResult) -> ActionResult:
                return ActionResult(output=f"Implemented fake task for run title '{run.title}'")

            def reviewer_action(so_far: ExecutionResult) -> ActionResult:
                return ActionResult(output="Approved fake implementation", approved=True)

            return self._graph_manager.execute_graph(Agent(
                role=AgentRole.planner,
                action=_logged(AgentRole.planner, planner_action),
                next=Agent(
                    role=AgentRole.coder,
                    action=_logged(AgentRole.coder, coder_action),
                    next=Agent(
                        role=AgentRole.reviewer,
                        action=_logged(AgentRole.reviewer, reviewer_action),
                    )
                )
            ))
