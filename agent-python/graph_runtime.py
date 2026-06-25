from typing import TypedDict

from langgraph.graph import END, StateGraph


class GraphAgentState(TypedDict, total=False):
    """Minimal LangGraph state shape for the Agent workflow."""

    user_message: str
    response: str


def normal_message_node(state: GraphAgentState) -> GraphAgentState:
    """Minimal node that proves the graph can receive and update Agent state."""
    user_message = state.get("user_message", "")
    return {"response": f"Graph skeleton received: {user_message}"}


def build_graph():
    """Build the smallest LangGraph workflow for the Agent tutorial."""
    graph = StateGraph(GraphAgentState)
    graph.add_node("normal_message", normal_message_node)
    graph.set_entry_point("normal_message")
    graph.add_edge("normal_message", END)
    return graph.compile()


if __name__ == "__main__":
    compiled_graph = build_graph()
    result = compiled_graph.invoke({"user_message": "hello from LangGraph"})
    print(result["response"])
