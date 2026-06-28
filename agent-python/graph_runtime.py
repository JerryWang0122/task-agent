import asyncio
from typing import TypedDict

from langgraph.graph import END, StateGraph

from main import (
    AgentState,
    PendingAction,
    PendingFollowUp,
    PendingActionKind,
    PendingFollowUpKind,
    handle_agent_message,
    handle_pending_action,
    handle_pending_follow_up,
)


SerializedPendingState = dict[str, object]


class GraphAgentState(TypedDict, total=False):
    """Minimal LangGraph state shape for the Agent workflow."""

    user_message: str
    response: str
    pending_action: SerializedPendingState | None
    pending_follow_up: SerializedPendingState | None


def serialize_pending_action(pending_action: PendingAction | None) -> SerializedPendingState | None:
    """Convert internal pending action objects into JSON-friendly graph state."""
    if pending_action is None:
        return None

    return {
        "kind": pending_action.kind.value,
        "task_id": pending_action.task_id,
        "title": pending_action.title,
        "due_date": pending_action.due_date,
    }


def deserialize_pending_action(raw_state: object) -> PendingAction | None:
    """Convert JSON-friendly graph state back into the internal pending action object."""
    if raw_state is None:
        return None

    if not isinstance(raw_state, dict):
        return None

    raw_kind = raw_state.get("kind")
    if not isinstance(raw_kind, str):
        return None

    try:
        kind = PendingActionKind(raw_kind)
    except ValueError:
        return None

    task_id = raw_state.get("task_id")
    return PendingAction(
        kind=kind,
        task_id=int(task_id) if task_id is not None else None,
        title=str(raw_state["title"]) if raw_state.get("title") is not None else None,
        due_date=str(raw_state["due_date"]) if raw_state.get("due_date") is not None else None,
    )


def serialize_pending_follow_up(pending_follow_up: PendingFollowUp | None) -> SerializedPendingState | None:
    """Convert internal follow-up objects into JSON-friendly graph state."""
    if pending_follow_up is None:
        return None

    return {
        "kind": pending_follow_up.kind.value,
        "due_date": pending_follow_up.due_date,
    }


def deserialize_pending_follow_up(raw_state: object) -> PendingFollowUp | None:
    """Convert JSON-friendly graph state back into the internal follow-up object."""
    if raw_state is None:
        return None

    if not isinstance(raw_state, dict):
        return None

    raw_kind = raw_state.get("kind")
    if not isinstance(raw_kind, str):
        return None

    try:
        kind = PendingFollowUpKind(raw_kind)
    except ValueError:
        return None

    return PendingFollowUp(
        kind=kind,
        due_date=str(raw_state["due_date"]) if raw_state.get("due_date") is not None else None,
    )


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
        "pending_action": serialize_pending_action(turn_result.pending_action),
        "pending_follow_up": serialize_pending_follow_up(turn_result.pending_follow_up),
    }


def pending_action_node(state: GraphAgentState) -> GraphAgentState:
    """Run the existing confirmation handler inside a graph node."""
    agent_state = AgentState(
        pending_action=deserialize_pending_action(state.get("pending_action")),
    )
    response = handle_pending_action(agent_state, state.get("user_message", ""))
    return {
        "response": response,
        "pending_action": serialize_pending_action(agent_state.pending_action),
        "pending_follow_up": serialize_pending_follow_up(agent_state.pending_follow_up),
    }


def pending_follow_up_node(state: GraphAgentState) -> GraphAgentState:
    """Run the existing follow-up handler inside a graph node."""
    agent_state = AgentState(
        pending_follow_up=deserialize_pending_follow_up(state.get("pending_follow_up")),
    )
    response = handle_pending_follow_up(agent_state, state.get("user_message", ""))
    return {
        "response": response,
        "pending_action": serialize_pending_action(agent_state.pending_action),
        "pending_follow_up": serialize_pending_follow_up(agent_state.pending_follow_up),
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
