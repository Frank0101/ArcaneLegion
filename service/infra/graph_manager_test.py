from domain.run.models import ActionResult, Agent
from infra.graph_manager import LangGraphManager


def test_all_agent_results_are_collected() -> None:
    agent = Agent(
        name="first",
        action=lambda so_far: ActionResult(output="first output"),
        next=Agent(
            name="second",
            action=lambda so_far: ActionResult(output="second output", approved=False),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results["first"].output == "first output"
    assert result.action_results["second"].output == "second output"
    assert result.action_results["second"].approved is False


def test_action_receives_accumulated_results_from_previous_agents() -> None:
    agent = Agent(
        name="first",
        action=lambda so_far: ActionResult(output="first output"),
        next=Agent(
            name="second",
            action=lambda so_far: ActionResult(
                output=so_far.action_results["first"].output + " second output"
            ),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results["second"].output == "first output second output"
