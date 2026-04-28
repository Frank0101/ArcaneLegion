import logging
from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from domain.run.graph_manager import AbstractGraphManager
from domain.run.models import ActionResult, Agent, AgentRole, ExecutionResult

logger = logging.getLogger(__name__)

_ACTION_RESULTS_STATE_KEY: str = "action_results"


class _ExecutionState(TypedDict):
    action_results: dict[AgentRole, ActionResult]


def _wrap(agent: Agent) -> Callable[[_ExecutionState], dict[str, object]]:
    def node(state: _ExecutionState) -> dict[str, object]:
        logger.info("Agent %s starting", agent.role.value)
        result = agent.action(ExecutionResult(action_results=state[_ACTION_RESULTS_STATE_KEY]))
        logger.info("Agent %s completed: %s", agent.role.value, result.output)
        return {_ACTION_RESULTS_STATE_KEY: {**state[_ACTION_RESULTS_STATE_KEY], agent.role: result}}

    return node


def _build_graph(agent: Agent) -> StateGraph:
    builder: StateGraph = StateGraph(_ExecutionState)
    current: Optional[Agent] = agent
    prev_name: Optional[str] = None
    while current is not None:
        builder.add_node(current.role.value, _wrap(current))
        if prev_name is None:
            builder.set_entry_point(current.role.value)
        else:
            builder.add_edge(prev_name, current.role.value)
        prev_name = current.role.value
        current = current.next
    if prev_name is not None:
        builder.add_edge(prev_name, END)
    return builder


class LangGraphManager(AbstractGraphManager):
    def execute_graph(self, agent: Agent) -> ExecutionResult:
        graph = _build_graph(agent).compile()
        state = graph.invoke({_ACTION_RESULTS_STATE_KEY: {}})
        return ExecutionResult(action_results=state[_ACTION_RESULTS_STATE_KEY])
