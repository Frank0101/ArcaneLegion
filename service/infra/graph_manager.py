from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, ExecutionResult


class _ExecutionState(TypedDict):
    action_results: dict[str, ActionResult]


def _wrap(agent: Agent) -> Callable[[_ExecutionState], dict[str, object]]:
    def node(state: _ExecutionState) -> dict[str, object]:
        result = agent.action()
        return {"action_results": {**state["action_results"], agent.name: result}}

    return node


def _build_graph(agent: Agent) -> StateGraph:
    builder: StateGraph = StateGraph(_ExecutionState)
    current: Optional[Agent] = agent
    prev_name: Optional[str] = None
    while current is not None:
        builder.add_node(current.name, _wrap(current))
        if prev_name is None:
            builder.set_entry_point(current.name)
        else:
            builder.add_edge(prev_name, current.name)
        prev_name = current.name
        current = current.next
    if prev_name is not None:
        builder.add_edge(prev_name, END)
    return builder


class LangGraphManager(AbstractGraphManager):
    def execute_graph(self, agent: Agent) -> ExecutionResult:
        graph = _build_graph(agent).compile()
        state = graph.invoke({"action_results": {}})
        return ExecutionResult(action_results=state["action_results"])
