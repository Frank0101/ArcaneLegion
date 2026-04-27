from datetime import datetime
from uuid import uuid4

from domain.run.models import ActionResult, Agent, Run, RunStatus
from infra.graph_manager import LangGraphManager


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


def test_execute_collects_all_agent_outputs() -> None:
    run = _make_run(title="My Task")
    agent = Agent(
        name="coder",
        action=lambda: ActionResult(output=f"Implemented fake task for run title '{run.title}'"),
        next=Agent(
            name="reviewer",
            action=lambda: ActionResult(output="Approved fake implementation", approved=True),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results["coder"].output == "Implemented fake task for run title 'My Task'"
    assert result.action_results["reviewer"].output == "Approved fake implementation"
    assert result.action_results["reviewer"].approved is True


def test_execute_not_approved_when_reviewer_rejects() -> None:
    agent = Agent(
        name="coder",
        action=lambda: ActionResult(output="coded"),
        next=Agent(
            name="reviewer",
            action=lambda: ActionResult(output="Rejected", approved=False),
        ),
    )

    result = LangGraphManager().execute_graph(agent)

    assert result.action_results["reviewer"].output == "Rejected"
