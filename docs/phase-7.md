# Phase 7: Productizing The Agent Workflow

## Step 7.1: Consolidate Agent Entrypoint

### Goal

In Phase 6, the Agent had several teaching entrypoints:

```text
tasks
overdue
weekly
ask-llm <message>
ask-tools <message>
rule-based natural-language routing
```

Those commands were useful because each one exposed one concept at a time.

In this step, we start turning the tutorial Agent into a product-style Agent by adding one normal natural-language entrypoint.

The user should be able to type:

```text
show overdue tasks
summarize my weekly workload
tasks due by Friday
create a task for tomorrow
complete task 1
```

without choosing whether the implementation should use a local rule, JSON decision, or OpenAI tool-calling.

### Files We Touched

- `agent-python/main.py`: adds a unified message handler for normal user input.
- `agent-python/README.md`: documents the new primary interaction style.
- `docs/phase-7.md`: records the Phase 7 workflow direction.

### Concept

The important productization idea is this:

```text
The user should describe the goal.
The Agent runtime should choose the workflow path.
```

Phase 5 and Phase 6 intentionally exposed multiple internals:

```text
ask-llm     -> show explicit JSON decisions
ask-tools   -> show OpenAI automatic tool calling
tasks       -> show direct MCP tool execution
weekly      -> show Agent-side summarization
```

That is good for learning, but not ideal for product usage.

A product Agent should hide those internal choices behind one entrypoint:

```text
User message
  -> unified Agent handler
  -> deterministic workflow checks
  -> OpenAI tool-calling when available
  -> local fallback when OpenAI is not configured
  -> shared safety policy
  -> MCP tool execution
```

### Implementation

The Agent now has two important functions:

```python
handle_local_agent_message(user_message)
handle_agent_message(user_message)
```

`handle_local_agent_message` keeps the tutorial fallback rules in one function.

`handle_agent_message` is the new unified entrypoint for normal user messages.

Its flow is:

```text
1. Keep deterministic local handling for workflows that need special formatting or follow-up.
2. If OPENAI_API_KEY exists, use OpenAI tool-calling.
3. Apply the same Agent decision policy as before.
4. If OpenAI is not configured, use the local tutorial fallback.
```

This is a small but important architectural cleanup.

The CLI loop no longer owns all routing decisions directly. Instead, it delegates normal messages to the Agent runtime handler.

### Why We Keep Local Fallback

The local fallback remains useful for two reasons.

First, this is a tutorial project. You should still be able to run the Agent without an OpenAI API key.

Second, not every workflow should be blindly delegated to the LLM. Some behavior is deterministic runtime policy:

```text
group overdue tasks by priority
summarize weekly workload
ask a follow-up question when create_task is missing a title
```

These are examples of Agent orchestration, not backend business rules.

### How To Run Or Test

Start the Java backend first:

```bash
cd backend-java
JAVA_HOME="$(/usr/libexec/java_home -v 17)" mvn spring-boot:run
```

In another terminal, run the Agent:

```bash
cd agent-python
source .venv/bin/activate
export MCP_SERVER_PYTHON=../mcp-server/.venv/bin/python
python main.py
```

Try normal natural-language input:

```text
show overdue tasks
summarize my weekly workload
tasks due by Friday
create a task for tomorrow
```

If `OPENAI_API_KEY` is set, normal messages can use OpenAI tool-calling automatically.

If `OPENAI_API_KEY` is not set, the Agent uses the local fallback rules.

### What You Learned

You learned the difference between a teaching CLI and a product Agent interface.

The user-facing interface should be simple:

```text
type a goal in natural language
```

The Agent runtime can still contain multiple internal strategies:

```text
deterministic workflow code
OpenAI tool-calling
local fallback rules
safety policy
MCP tool execution
```

### Next Step

Next, we can make the workflow state more explicit.

That means replacing scattered variables like:

```text
pending_action
pending_follow_up
```

with a clearer Agent workflow state object before introducing LangGraph.

## Step 7.2: Extract Workflow State

### Goal

Step 7.1 gave the Agent one main message entrypoint.

Step 7.2 makes the Agent's workflow state explicit.

Before this step, the CLI loop tracked state with two loose variables:

```text
pending_action
pending_follow_up
```

That worked, but it hid an important Agent concept: a conversational Agent is not just a function call. It often waits across turns.

Examples:

```text
User: create a task for tomorrow
Agent: What is the task title?

User: Buy milk
Agent: Confirm: create task 'Buy milk' due tomorrow?

User: yes
Agent: Created task #5: Buy milk
```

The Agent has to remember what it is waiting for between messages.

### Files We Touched

- `agent-python/main.py`: adds `AgentState` and updates the CLI loop to store pending workflow state there.
- `agent-python/README.md`: explains that the Agent runtime now has explicit workflow state.
- `docs/phase-7.md`: records why explicit state matters before LangGraph.

### Concept

Enterprise Agent workflows are state machines.

A simple request may finish in one turn:

```text
User asks for overdue tasks
  -> Agent calls tool
  -> Agent responds
```

A safer write workflow takes multiple turns:

```text
User asks to create task
  -> Agent may ask follow-up question
  -> Agent waits for missing information
  -> Agent asks for confirmation
  -> Agent waits for yes/no
  -> Agent executes tool
  -> Agent responds
```

The important learning point is that `pending_action` and `pending_follow_up` are not random variables. They are workflow state.

### Implementation

The Agent now has a small dataclass:

```python
@dataclass
class AgentState:
    pending_action: dict[str, object] | None = None
    pending_follow_up: dict[str, object] | None = None
```

The CLI loop now creates one state object:

```python
state = AgentState()
```

Then it reads and writes:

```python
state.pending_action
state.pending_follow_up
```

instead of standalone local variables.

This does not change behavior yet. It changes the structure so future workflow steps have a clear place to live.

### Why This Comes Before LangGraph

LangGraph is useful when the workflow has nodes and state.

Before adding LangGraph, we should be able to name the state ourselves:

```text
No pending state
Waiting for follow-up answer
Waiting for confirmation
Executing tool
Returning final answer
```

`AgentState` is the simple, manual version of that idea.

Later, LangGraph can manage the same state transitions more formally.

### How To Run Or Test

Run a syntax check:

```bash
cd agent-python
python -m py_compile main.py
```

You can also test a stateful flow in the CLI:

```text
create a task for tomorrow
Buy milk
yes
```

Expected behavior:

```text
Agent asks for title
Agent asks for confirmation
Agent creates the task only after yes
```

### What You Learned

You learned that Agent runtime state should be explicit.

This is the bridge from a simple CLI loop to a graph-based workflow engine.

### Next Step

Next, we can make workflow transitions explicit with helper functions such as:

```text
handle_pending_action
handle_pending_follow_up
```

That will make the CLI loop even smaller and prepare the code for LangGraph nodes.
