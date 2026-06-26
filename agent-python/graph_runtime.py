import asyncio
from typing import TypedDict

from langgraph.graph import END, StateGraph

from main import (
    AgentState,
    PendingAction,
    PendingFollowUp,
    handle_agent_message,
    handle_pending_action,
    handle_pending_follow_up,
)


class GraphAgentState(TypedDict, total=False):
    """Minimal LangGraph state shape for the Agent workflow."""

    user_message: str
    response: str
    pending_action: PendingAction | None
    pending_follow_up: PendingFollowUp | None


def route_input_node(state: GraphAgentState) -> GraphAgentState:
    """Entry node that lets conditional routing inspect the current state."""
    return {}


def route_input(state: GraphAgentState) -> str:
    """Choose the next node based on pending workflow state."""
    if state.get("pending_action") is not None:
        return "pending_action"

    if state.get("pending_follow_up") is not None:
        return "pending_follow_up"

    return "normal_message"


def normal_message_node(state: GraphAgentState) -> GraphAgentState:
    """Run the existing normal-message Agent handler inside a graph node."""
    user_message = state.get("user_message", "")
    turn_result = asyncio.run(handle_agent_message(user_message))
    return {
        "response": turn_result.response,
        "pending_action": turn_result.pending_action,
        "pending_follow_up": turn_result.pending_follow_up,
    }


def pending_action_node(state: GraphAgentState) -> GraphAgentState:
    """Run the existing confirmation handler inside a graph node."""
    agent_state = AgentState(pending_action=state.get("pending_action"))
    response = handle_pending_action(agent_state, state.get("user_message", ""))
    return {
        "response": response,
        "pending_action": agent_state.pending_action,
        "pending_follow_up": agent_state.pending_follow_up,
    }


def pending_follow_up_node(state: GraphAgentState) -> GraphAgentState:
    """Run the existing follow-up handler inside a graph node."""
    agent_state = AgentState(pending_follow_up=state.get("pending_follow_up"))
    response = handle_pending_follow_up(agent_state, state.get("user_message", ""))
    return {
        "response": response,
        "pending_action": agent_state.pending_action,
        "pending_follow_up": agent_state.pending_follow_up,
    }


def build_graph():
    """Build the smallest LangGraph workflow for the Agent tutorial."""
    graph = StateGraph(GraphAgentState)
    graph.add_node("route_input", route_input_node)
    graph.add_node("normal_message", normal_message_node)
    graph.add_node("pending_action", pending_action_node)
    graph.add_node("pending_follow_up", pending_follow_up_node)
    graph.set_entry_point("route_input")
    graph.add_conditional_edges(
        "route_input",
        route_input,
        {
            "normal_message": "normal_message",
            "pending_action": "pending_action",
            "pending_follow_up": "pending_follow_up",
        },
    )
    graph.add_edge("normal_message", END)
    graph.add_edge("pending_action", END)
    graph.add_edge("pending_follow_up", END)
    return graph.compile()


if __name__ == "__main__":
    compiled_graph = build_graph()
    first_result = compiled_graph.invoke({"user_message": "create a task for tomorrow"})
    print(first_result["response"])

    second_result = compiled_graph.invoke({**first_result, "user_message": "Buy milk"})
    print(second_result["response"])
