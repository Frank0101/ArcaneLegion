from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, ExecutionResult, Run


class RunExecutor:
    def __init__(self, graph_manager: AbstractGraphManager) -> None:
        self._graph_manager = graph_manager

    def execute(self, run: Run) -> ExecutionResult:
        def planner_action(so_far: ExecutionResult) -> ActionResult:
            return ActionResult(output=f"Planned task for run title '{run.title}'")

        def coder_action(so_far: ExecutionResult) -> ActionResult:
            return ActionResult(output=f"Implemented fake task for run title '{run.title}'")

        def reviewer_action(so_far: ExecutionResult) -> ActionResult:
            return ActionResult(output="Approved fake implementation", approved=True)

        return self._graph_manager.execute_graph(Agent(
            name="planner",
            action=planner_action,
            next=Agent(
                name="coder",
                action=coder_action,
                next=Agent(
                    name="reviewer",
                    action=reviewer_action,
                )
            )
        ))
