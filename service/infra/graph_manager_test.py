from domain.run.models import ActionResult, Agent
from infra.graph_manager import LangGraphManager


def test_all_agent_results_are_collected() -> None:
    agent = Agent(
        name="first",
        action=lambda: ActionResult(output="first output"),
        next=Agent(
            name="second",
            action=lambda: ActionResult(output="second output", approved=False),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results["first"].output == "first output"
    assert result.action_results["second"].output == "second output"
    assert result.action_results["second"].approved is False
