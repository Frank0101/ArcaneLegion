from typing import TypedDict, cast

from langgraph.graph import END, StateGraph

from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ExecutionResult, Run


class _GraphState(TypedDict):
    run: Run
    coder_output: str
    reviewer_output: str
    approved: bool


def _coder_node(state: _GraphState) -> dict[str, object]:
    return {"coder_output": f"Implemented fake task for run title '{state['run'].title}'"}


def _reviewer_node(state: _GraphState) -> dict[str, object]:
    return {"reviewer_output": "Approved fake implementation", "approved": True}


class LangGraphManager(AbstractGraphManager):
    def __init__(self) -> None:
        builder: StateGraph = StateGraph(_GraphState)
        builder.add_node("coder", _coder_node)
        builder.add_node("reviewer", _reviewer_node)
        builder.set_entry_point("coder")
        builder.add_edge("coder", "reviewer")
        builder.add_edge("reviewer", END)
        self._graph = builder.compile()

    def execute(self, run: Run) -> ExecutionResult:
        final_state = cast(_GraphState, self._graph.invoke({
            "run": run,
            "coder_output": "",
            "reviewer_output": "",
            "approved": False
        }))
        if final_state["approved"]:
            return ExecutionResult(
                success=True,
                summary={
                    "coder": final_state["coder_output"],
                    "reviewer": final_state["reviewer_output"],
                    "approved": True,
                },
                error_message=None,
            )
        return ExecutionResult(
            success=False,
            summary={
                "coder": final_state["coder_output"],
                "reviewer": final_state["reviewer_output"],
                "approved": False,
            },
            error_message="Reviewer did not approve",
        )
