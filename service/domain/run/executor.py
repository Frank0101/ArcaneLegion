from domain.project.repository import AbstractProjectRepository
from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, AgentRole, ExecutionResult, Run
from domain.run.runtime import AbstractAgentRuntime


class RunExecutor:
    def __init__(
            self,
            graph_manager: AbstractGraphManager,
            project_repo: AbstractProjectRepository,
            runtime: AbstractAgentRuntime,
    ) -> None:
        self._graph_manager = graph_manager
        self._project_repo = project_repo
        self._runtime = runtime

    def execute(self, run: Run) -> ExecutionResult:
        project = self._project_repo.get_by_id(run.project_id)
        if project is None:
            raise ValueError(f"Project {run.project_id} not found")

        def planner_action(_) -> ActionResult:
            prompt = f"Task: {run.title}\n\n{run.description}"
            output = self._runtime.run(AgentRole.planner, prompt, project.repo_path, project.default_branch)
            return ActionResult(output=output)

        def coder_action(so_far: ExecutionResult) -> ActionResult:
            return ActionResult(output=f"Implemented fake task for run title '{run.title}'")

        def reviewer_action(so_far: ExecutionResult) -> ActionResult:
            return ActionResult(output="Approved fake implementation", approved=True)

        return self._graph_manager.execute_graph(Agent(
            role=AgentRole.planner,
            action=planner_action,
            next=Agent(
                role=AgentRole.coder,
                action=coder_action,
                next=Agent(
                    role=AgentRole.reviewer,
                    action=reviewer_action,
                )
            )
        ))
