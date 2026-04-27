from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from domain.run.models import Run, RunStatus
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


def test_execute_returns_success_with_structured_summary() -> None:
    manager = LangGraphManager()
    run = _make_run(title="My Task")

    result = manager.execute(run)

    assert result.success is True
    assert result.error_message is None
    assert result.summary["approved"] is True
    assert result.summary["coder"] == "Implemented fake task for run title 'My Task'"
    assert result.summary["reviewer"] == "Approved fake implementation"


def test_execute_returns_failure_when_reviewer_rejects() -> None:
    manager = LangGraphManager()
    run = _make_run()

    with patch.object(manager, "_graph") as mock_graph:
        mock_graph.invoke.return_value = {
            "run": run,
            "coder_output": "some output",
            "reviewer_output": "Rejected",
            "approved": False,
        }
        result = manager.execute(run)

    assert result.success is False
    assert result.error_message == "Reviewer did not approve"
    assert result.summary["approved"] is False
