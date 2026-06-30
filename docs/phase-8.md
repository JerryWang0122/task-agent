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

## Step 8.2: Add LangGraph Checkpointer

### Goal

Connect the serializable graph state from Step 8.1 to a LangGraph checkpointer.

This is the step where Step 8.1 starts to make practical sense. A checkpointer can only safely save workflow state if that state has a stable, serializable shape.

### Files We Touched

- `agent-python/graph_runtime.py`: adds an in-memory LangGraph checkpointer and graph config helper.
- `agent-python/main.py`: changes the opt-in graph CLI to use a `thread_id` instead of manually carrying a graph state dictionary.
- `docs/phase-8.md`: explains checkpointer and thread concepts.

### Concept

LangGraph checkpointing introduces two important ideas:

```text
checkpointer
  stores workflow state after graph execution

thread_id
  identifies which workflow conversation should be resumed
```

In this step we use `MemorySaver`, which means:

```text
state can be resumed within the same Python process
state is lost when the process exits
```

That is enough for learning how checkpointing works. A later step can replace it with a durable checkpointer.

### Implementation

The graph runtime now provides:

```text
graph_config(thread_id)
build_checkpointed_graph()
```

The CLI graph path now invokes the graph like this conceptually:

```text
compiled_graph.invoke(
  {"user_message": user_message},
  config={"configurable": {"thread_id": "default"}}
)
```

The important difference is that the CLI no longer passes the previous `graph_state` dictionary back into every turn.

Instead:

```text
LangGraph checkpointer stores the previous state.
thread_id tells LangGraph which previous state to load.
```

### How To Run Or Test

Run syntax checks:

```bash
cd agent-python
.venv/bin/python -m py_compile main.py graph_runtime.py
```

Run the graph demo:

```bash
OPENAI_API_KEY= .venv/bin/python graph_runtime.py
```

Run the CLI with graph runtime and a named thread:

```bash
OPENAI_API_KEY= USE_LANGGRAPH_RUNTIME=1 AGENT_THREAD_ID=demo-1 .venv/bin/python main.py
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
The first turn stores a pending follow-up in the checkpoint.
The second turn resumes that pending follow-up by thread_id and creates a pending confirmation.
The third turn resumes that pending confirmation and cancels it.
```

### What You Learned

You learned why serializable graph state matters.

Step 8.1 made state safe to save. Step 8.2 actually saves and resumes that state inside LangGraph.

### Next Step

Next, we can inspect checkpoint state more explicitly or move from in-memory checkpointing toward durable checkpoint storage.

## Step 8.3: Inspect Checkpoint State

### Goal

Make checkpointing visible.

Step 8.2 proved that LangGraph can resume state by `thread_id`, but that can still feel hidden. Step 8.3 adds a small inspection path so we can see exactly what the checkpointer saved.

### Files We Touched

- `agent-python/graph_runtime.py`: adds helper functions that read the latest checkpoint values for one thread.
- `agent-python/main.py`: adds a `checkpoint` debug command for the opt-in graph runtime.
- `docs/phase-8.md`: documents how to inspect checkpoint state.

### Concept

LangGraph exposes saved workflow state through:

```text
compiled_graph.get_state(config)
```

That returns a `StateSnapshot`. The most important field for us is:

```text
snapshot.values
```

Those values are the latest saved workflow state for the selected `thread_id`.

This proves that checkpointing is not just remembering the last answer. It remembers the state that controls the next route.

### Implementation

The graph runtime now provides:

```text
checkpoint_values(compiled_graph, thread_id)
format_checkpoint_values(compiled_graph, thread_id)
```

The CLI now supports this command when graph runtime is enabled:

```text
checkpoint
```

### How To Run Or Test

Run the graph CLI:

```bash
cd agent-python
OPENAI_API_KEY= USE_LANGGRAPH_RUNTIME=1 AGENT_THREAD_ID=demo-inspect .venv/bin/python main.py
```

Try:

```text
checkpoint
create a task for tomorrow
checkpoint
Buy milk
checkpoint
no
checkpoint
exit
```

Expected result after the first `checkpoint`:

```text
No checkpoint state found for thread 'demo-inspect'.
```

Expected result after `create a task for tomorrow`:

```json
{
  "pending_action": null,
  "pending_follow_up": {
    "due_date": "2026-06-29",
    "kind": "create_task_missing_title"
  },
  "response": "What is the task title? I will set the due date to 2026-06-29.",
  "user_message": "create a task for tomorrow"
}
```

Expected result after `Buy milk`:

```json
{
  "pending_action": {
    "due_date": "2026-06-29",
    "kind": "create_task",
    "task_id": null,
    "title": "Buy milk"
  },
  "pending_follow_up": null,
  "response": "Confirm: create task 'Buy milk' due 2026-06-29? Type 'yes' or 'no'.",
  "user_message": "Buy milk"
}
```

Expected result after `no`:

```json
{
  "pending_action": null,
  "pending_follow_up": null,
  "response": "Cancelled. No task was changed.",
  "user_message": "no"
}
```

### What You Learned

You learned how to inspect the state that makes workflow resume possible.

The `thread_id` selects the workflow. The checkpoint stores the latest state. The graph uses that state to decide which node should handle the next user message.

### Next Step

Next, we can decide whether to keep using `MemorySaver` for learning or introduce a durable checkpointer that survives process restarts.
