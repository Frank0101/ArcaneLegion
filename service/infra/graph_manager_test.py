from domain.run.models import ActionResult, Agent, AgentRole
from infra.graph_manager import LangGraphManager


def test_all_agent_results_are_collected() -> None:
    agent = Agent(
        role=AgentRole.planner,
        action=lambda so_far: ActionResult(output="first output"),
        next=Agent(
            role=AgentRole.coder,
            action=lambda so_far: ActionResult(output="second output", approved=False),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results[AgentRole.planner].output == "first output"
    assert result.action_results[AgentRole.coder].output == "second output"
    assert result.action_results[AgentRole.coder].approved is False


def test_action_receives_accumulated_results_from_previous_agents() -> None:
    agent = Agent(
        role=AgentRole.planner,
        action=lambda so_far: ActionResult(output="first output"),
        next=Agent(
            role=AgentRole.coder,
            action=lambda so_far: ActionResult(
                output=so_far.action_results[AgentRole.planner].output + " second output"
            ),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results[AgentRole.coder].output == "first output second output"
