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
        prefix: str,
        role: AgentRole,
        action: Callable[[ExecutionResult], ActionResult],
) -> Callable[[ExecutionResult], ActionResult]:
    def wrapped(so_far: ExecutionResult) -> ActionResult:
        logger.info("%s Agent %s starting", prefix, role.value)
        result = action(so_far)
        logger.info("%s Agent %s completed", prefix, role.value)
        logger.debug("%s\n\n--- output ---\n%s", prefix, result.output)
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

        prefix = f"[run:{str(run.id)[:8]}]"

        with tempfile.TemporaryDirectory(prefix=f"{str(run.id)}_", dir=self._workspace_base_path) as workspace:
            logger.info("%s Temporary workspace created: %s", prefix, workspace)

            self._repo_manager.clone(project.repo_path, project.default_branch, workspace)
            logger.info("%s Repo %s (branch=%s) cloned to workspace", prefix, project.repo_path,
                        project.default_branch)

            def planner_action(_) -> ActionResult:
                prompt = f"# Task: {run.title}\n\n{run.description}"
                logger.debug("%s\n\n--- prompt ---\n%s", prefix, prompt)

                output = self._agent_runtime.run(AgentRole.planner, prompt, workspace)
                return ActionResult(prompt=prompt, output=output)

            def coder_action(so_far: ExecutionResult) -> ActionResult:
                return ActionResult(prompt="", output=f"Implemented fake task for run title '{run.title}'")

            def reviewer_action(so_far: ExecutionResult) -> ActionResult:
                return ActionResult(prompt="", output="Approved fake implementation", approved=True)

            return self._graph_manager.execute_graph(Agent(
                role=AgentRole.planner,
                action=_logged(prefix, AgentRole.planner, planner_action),
                next=Agent(
                    role=AgentRole.coder,
                    action=_logged(prefix, AgentRole.coder, coder_action),
                    next=Agent(
                        role=AgentRole.reviewer,
                        action=_logged(prefix, AgentRole.reviewer, reviewer_action),
                    )
                )
            ))
