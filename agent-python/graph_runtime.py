import asyncio
from typing import TypedDict

from langgraph.graph import END, StateGraph

from main import PendingAction, PendingFollowUp, handle_agent_message


class GraphAgentState(TypedDict, total=False):
    """Minimal LangGraph state shape for the Agent workflow."""

    user_message: str
    response: str
    pending_action: PendingAction | None
    pending_follow_up: PendingFollowUp | None


def normal_message_node(state: GraphAgentState) -> GraphAgentState:
    """Run the existing normal-message Agent handler inside a graph node."""
    user_message = state.get("user_message", "")
    turn_result = asyncio.run(handle_agent_message(user_message))
    return {
        "response": turn_result.response,
        "pending_action": turn_result.pending_action,
        "pending_follow_up": turn_result.pending_follow_up,
    }


def build_graph():
    """Build the smallest LangGraph workflow for the Agent tutorial."""
    graph = StateGraph(GraphAgentState)
    graph.add_node("normal_message", normal_message_node)
    graph.set_entry_point("normal_message")
    graph.add_edge("normal_message", END)
    return graph.compile()


if __name__ == "__main__":
    compiled_graph = build_graph()
    result = compiled_graph.invoke({"user_message": "create a task for tomorrow"})
    print(result["response"])
