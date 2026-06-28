## Phase 8: Durable Workflow State And Checkpointing

Phase 8 focuses on making the Agent workflow durable.

In Phase 7, LangGraph became an opt-in runtime. The graph can route between normal messages, follow-up questions, and confirmation replies. However, the graph state still lived only in memory.

The next learning goal is to prepare that state for checkpointing.

## Step 8.1: Make Graph State Serializable

### Goal

Make LangGraph state JSON-friendly.

This is required before adding durable checkpointing because checkpoint storage should save simple values such as strings, numbers, booleans, lists, and dictionaries. It should not depend on live Python dataclass or enum objects.

### Files We Touched

- `agent-python/graph_runtime.py`: converts pending workflow objects to and from serializable dictionaries at the graph boundary.
- `docs/phase-8.md`: explains the durability concept and verification path.

### Concept

The Agent still uses typed internal objects:

```text
PendingAction
PendingFollowUp
PendingActionKind
PendingFollowUpKind
```

Those are useful inside Python code because they give us named fields and safer comparisons.

The graph state now stores JSON-friendly shapes instead:

```text
pending_action:
  kind: "create_task"
  task_id: null
  title: "Buy milk"
  due_date: "2026-06-29"

pending_follow_up:
  kind: "create_task_missing_title"
  due_date: "2026-06-29"
```

This separates two responsibilities:

```text
internal Agent objects
  convenient for Python logic

serialized graph state
  safe for checkpointing and resume
```

### Implementation

The graph runtime now has conversion helpers:

```text
serialize_pending_action
deserialize_pending_action
serialize_pending_follow_up
deserialize_pending_follow_up
```

Graph nodes use these helpers at the boundary:

```text
normal_message_node
  internal AgentTurnResult
  -> serialized graph state

pending_action_node
  serialized graph state
  -> internal AgentState
  -> serialized graph state

pending_follow_up_node
  serialized graph state
  -> internal AgentState
  -> serialized graph state
```

The important design choice is that `main.py` did not need to change. The existing Agent runtime can keep using dataclasses and enums. Only the graph runtime owns the checkpoint-friendly state shape.

### How To Run Or Test

Run syntax checks:

```bash
cd agent-python
python -m py_compile main.py graph_runtime.py
```

Run the graph demo:

```bash
OPENAI_API_KEY= python graph_runtime.py
```

Expected behavior:

```text
The Agent asks for a missing task title.
The Agent then asks for confirmation after receiving the title.
```

Run the opt-in graph CLI:

```bash
OPENAI_API_KEY= USE_LANGGRAPH_RUNTIME=1 python main.py
```

Try:

```text
create a task for tomorrow
Buy milk
no
exit
```

Expected behavior:

```text
The Agent asks for the title.
The Agent asks for confirmation.
The Agent cancels without changing data.
```

### What You Learned

You learned the difference between runtime objects and persisted workflow state.

Runtime objects make code readable. Serialized state makes workflow checkpointing possible.

### Next Step

Next, we can add a LangGraph checkpointer and introduce the idea of `thread_id` for resuming a workflow.
