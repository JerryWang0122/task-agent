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

## Step 7.3: Extract Pending Workflow Handlers

### Goal

Step 7.2 introduced `AgentState`.

Step 7.3 moves the pending workflow logic out of the CLI loop and into dedicated handler functions.

Before this step, the CLI loop directly handled:

```text
waiting for yes/no confirmation
waiting for a missing task title
turning a follow-up answer into a pending confirmation
```

That made the main loop responsible for too many workflow details.

### Files We Touched

- `agent-python/main.py`: adds pending workflow handler functions.
- `agent-python/README.md`: explains that pending workflows now have explicit handlers.
- `docs/phase-7.md`: records how pending handlers map to future workflow nodes.

### Concept

Once an Agent has state, the next question is:

```text
Who handles each state?
```

In a graph workflow, each state often maps to a node or edge.

For our manual version, we now have two handlers:

```python
handle_pending_action(state, user_message)
handle_pending_follow_up(state, user_message)
```

These handlers are responsible for state transitions.

### Implementation

`handle_pending_action` handles confirmation replies:

```text
yes / y / confirm
  -> execute pending write tool
  -> clear pending_action

no / n / cancel
  -> clear pending_action
  -> do not call tool

anything else
  -> ask the user to answer yes or no
```

`handle_pending_follow_up` handles missing information replies:

```text
cancel / no / n
  -> clear pending_follow_up
  -> do not change data

task title text
  -> clear pending_follow_up
  -> create pending_action
  -> ask for confirmation
```

The CLI loop now delegates to these handlers:

```python
if state.pending_action is not None:
    print(handle_pending_action(state, user_message))
    continue

if state.pending_follow_up is not None:
    print(handle_pending_follow_up(state, user_message))
    continue
```

### Why This Matters

This change makes the workflow shape easier to see:

```text
normal message handler
pending follow-up handler
pending action handler
```

That is close to how we will think about LangGraph nodes later:

```text
Intent Node
Follow-up Node
Confirmation Node
Tool Execution Node
Response Node
```

The code is still simple Python, but the architecture is becoming graph-shaped.

### How To Run Or Test

Run a syntax check:

```bash
cd agent-python
python -m py_compile main.py
```

You can test the handler behavior without starting the backend by checking the follow-up-to-confirmation transition:

```text
create a task for tomorrow
Buy milk
```

Expected result:

```text
The first message creates pending_follow_up.
The second message clears pending_follow_up and creates pending_action.
The Agent asks for confirmation.
```

### What You Learned

You learned that state and state handlers are separate ideas.

`AgentState` stores what the Agent is waiting for.

The pending handlers decide what to do with the next user message.

### Next Step

Next, we can make normal message output richer by returning a small result object instead of raw tuples.

That will reduce positional tuple mistakes and move us closer to typed workflow transitions.

## Step 7.4: Introduce AgentTurnResult

### Goal

Step 7.4 replaces the normal-message raw tuple result with an explicit result object.

Before this step, `handle_agent_message` and `handle_local_agent_message` returned:

```python
(pending_action, pending_follow_up, response)
```

That works, but it is easy to accidentally put values in the wrong position.

This already happened once during Step 7.1 when a follow-up value was placed where a pending action belonged.

### Files We Touched

- `agent-python/main.py`: adds `AgentTurnResult` and uses it for normal message handling.
- `agent-python/README.md`: documents that Agent turns now return a named result object.
- `docs/phase-7.md`: explains why named transition results are safer than positional tuples.

### Concept

An Agent turn is one pass through the runtime:

```text
user message
  -> runtime decision
  -> optional pending state update
  -> user-facing response
```

That result has named fields:

```text
response
pending_action
pending_follow_up
```

Using a named result object makes the workflow easier to read and safer to change.

### Implementation

The Agent now has:

```python
@dataclass
class AgentTurnResult:
    response: str
    pending_action: dict[str, object] | None = None
    pending_follow_up: dict[str, object] | None = None
```

Local and unified message handlers now return `AgentTurnResult` instead of a three-value tuple.

Example:

```python
return AgentTurnResult(
    response="What is the task title?",
    pending_follow_up={"type": "create_task_missing_title", "due_date": due_date},
)
```

The CLI loop now applies the result by name:

```python
turn_result = asyncio.run(handle_agent_message(user_message))
state.pending_action = turn_result.pending_action
state.pending_follow_up = turn_result.pending_follow_up
print(turn_result.response)
```

### Why This Matters

This is a small type-safety improvement, but it teaches an important enterprise Agent pattern.

As workflows grow, transitions should have explicit shapes.

Compare:

```python
return None, {"type": "create_task_missing_title"}, response
```

with:

```python
return AgentTurnResult(
    response=response,
    pending_follow_up={"type": "create_task_missing_title"},
)
```

The second version is easier to review, test, and later map into LangGraph state updates.

### How To Run Or Test

Run a syntax check:

```bash
cd agent-python
python -m py_compile main.py
```

You can test without the backend by checking a missing-title create request:

```text
create a task for tomorrow
```

Expected runtime result:

```text
response: asks for the task title
pending_follow_up: create_task_missing_title
pending_action: none
```

### What You Learned

You learned why Agent workflow transitions should use named result objects instead of positional tuples.

This prepares the code for stronger typing and future graph state updates.

### Next Step

Next, we can introduce explicit action/follow-up types instead of plain dictionaries.

That would make `pending_action["type"]` and `pending_follow_up["type"]` safer and easier to test.

## Step 7.5: Introduce Explicit Pending Types

### Goal

Step 7.5 replaces pending workflow dictionaries with typed dataclasses.

Before this step, pending state looked like this:

```python
{"type": "create_task", "title": "Buy milk", "due_date": "2026-06-25"}
```

That shape is flexible, but too easy to mistype.

After this step, pending state uses explicit classes:

```python
PendingAction(kind="create_task", title="Buy milk", due_date="2026-06-25")
PendingFollowUp(kind="create_task_missing_title", due_date="2026-06-25")
```

### Files We Touched

- `agent-python/main.py`: adds typed pending state classes and replaces dict access.
- `agent-python/README.md`: documents that pending runtime state now uses typed objects.
- `docs/phase-7.md`: explains why typed pending state is safer.

### Concept

Agent workflow state should have a schema.

Plain dictionaries are useful early in a tutorial because they are quick to write:

```python
pending_action["type"]
pending_action["title"]
```

But as workflow complexity grows, dictionaries become fragile:

```text
misspelled keys
missing fields
unclear expected shape
harder tests
harder refactoring
```

Typed pending objects make the state contract explicit.

### Implementation

The Agent now has:

```python
@dataclass
class PendingAction:
    kind: str
    task_id: int | None = None
    title: str | None = None
    due_date: str | None = None


@dataclass
class PendingFollowUp:
    kind: str
    due_date: str | None = None
```

`AgentState` now stores:

```python
pending_action: PendingAction | None
pending_follow_up: PendingFollowUp | None
```

Handlers now read named attributes:

```python
pending_action.kind
pending_action.task_id
pending_action.title
pending_action.due_date
```

instead of dictionary keys.

### Why This Matters

This is a small step toward production-grade workflow state.

Later, LangGraph will need a state schema. The current dataclasses are the manual version of that idea.

The pattern is:

```text
loose dicts early for learning
typed dataclasses when workflow stabilizes
graph state schema when orchestration becomes complex
```

### How To Run Or Test

Run a syntax check:

```bash
cd agent-python
python -m py_compile main.py
```

You can test the typed follow-up transition without the backend:

```text
create a task for tomorrow
Buy milk
```

Expected internal state:

```text
PendingFollowUp(kind="create_task_missing_title")
then PendingAction(kind="create_task", title="Buy milk")
```

### What You Learned

You learned that Agent state should move from flexible dictionaries to explicit schemas as workflows become more stable.

This makes confirmation and follow-up behavior easier to test and safer to refactor.

### Next Step

Next, we can introduce `Enum` values for pending kinds, replacing string literals like `"create_task"` and `"create_task_missing_title"`.

## Step 7.6: Introduce Pending Kind Enums

### Goal

Step 7.6 replaces internal pending-state kind strings with enums.

Before this step, typed pending state still used string values:

```python
PendingAction(kind="create_task")
PendingFollowUp(kind="create_task_missing_title")
```

After this step, the Agent uses enum values:

```python
PendingAction(kind=PendingActionKind.CREATE_TASK)
PendingFollowUp(kind=PendingFollowUpKind.CREATE_TASK_MISSING_TITLE)
```

### Files We Touched

- `agent-python/main.py`: adds pending kind enums and replaces internal pending kind string comparisons.
- `agent-python/README.md`: documents that pending kind values now use enums.
- `docs/phase-7.md`: explains why enums are useful in workflow state schemas.

### Concept

Enums are useful when a field can only be one of a known set of values.

For pending write actions, the current allowed values are:

```text
complete_task
create_task
```

For pending follow-up questions, the current allowed value is:

```text
create_task_missing_title
```

Using enum values makes the allowed state transitions easier to review and harder to mistype.

### Implementation

The Agent now has:

```python
class PendingActionKind(Enum):
    COMPLETE_TASK = "complete_task"
    CREATE_TASK = "create_task"


class PendingFollowUpKind(Enum):
    CREATE_TASK_MISSING_TITLE = "create_task_missing_title"
```

`PendingAction` now stores:

```python
kind: PendingActionKind
```

`PendingFollowUp` now stores:

```python
kind: PendingFollowUpKind
```

Handlers compare enum values:

```python
if action_type == PendingActionKind.CREATE_TASK:
    ...
```

instead of comparing strings.

### Important Boundary

This step only changes internal Agent runtime state.

MCP tool names remain strings:

```text
create_task
complete_task
find_overdue_tasks
```

That is correct because MCP tool names are part of the external tool contract between Agent and MCP Server.

### Why This Matters

This continues the workflow-state hardening path:

```text
dict state
  -> dataclass state
  -> enum-constrained state
  -> graph state schema later
```

Enums reduce typo risk and make it clearer which state transitions are supported.

### How To Run Or Test

Run a syntax check:

```bash
cd agent-python
python -m py_compile main.py
```

You can test without the backend by checking the follow-up transition:

```text
create a task for tomorrow
Buy milk
```

Expected internal state:

```text
PendingFollowUpKind.CREATE_TASK_MISSING_TITLE
then PendingActionKind.CREATE_TASK
```

### What You Learned

You learned that internal workflow state can be safer than external string contracts.

The Agent still calls MCP tools by string name, but its own pending workflow state now uses typed enum values.

### Next Step

Next, we can start introducing LangGraph by mapping the manual runtime pieces to graph concepts:

```text
AgentState -> graph state
handle_agent_message -> intent/tool decision node
handle_pending_follow_up -> follow-up node
handle_pending_action -> confirmation node
```

## Step 7.7: Map Manual Runtime To LangGraph Concepts

### Goal

Step 7.7 explains how the manual Agent runtime maps to LangGraph concepts.

We are not adding LangGraph yet.

Instead, we are making the transition understandable:

```text
manual stateful runtime
  -> graph-shaped runtime
  -> LangGraph implementation later
```

This matters because adding a graph library too early can hide the core idea. The core idea is state plus transitions.

### Files We Touched

- `agent-python/main.py`: adds small comments marking future graph node boundaries.
- `agent-python/README.md`: explains that the runtime is now graph-shaped, but not yet LangGraph-based.
- `docs/phase-7.md`: maps current code to LangGraph concepts.

### Concept

LangGraph is useful when an Agent workflow has:

```text
state
nodes
edges
checkpoints
conditional routing
human-in-the-loop pauses
```

We already built the manual version of these ideas.

### Manual Runtime To LangGraph Mapping

Current manual runtime:

```text
AgentState
AgentTurnResult
handle_agent_message
handle_pending_follow_up
handle_pending_action
apply_decision_policy
call_mcp_tool
```

LangGraph concept mapping:

```text
AgentState
  -> Graph state schema

AgentTurnResult
  -> State update returned by a node

handle_agent_message
  -> Intent and tool-decision node

handle_pending_follow_up
  -> Follow-up collection node

handle_pending_action
  -> Confirmation node

apply_decision_policy
  -> Safety policy node or guard

call_mcp_tool
  -> Tool execution node
```

### Current Control Flow

The current CLI does this manually:

```text
read user message
  -> if pending_action exists: handle confirmation
  -> else if pending_follow_up exists: handle missing information
  -> else handle normal message
  -> update AgentState
  -> print response
```

In graph terms, this is conditional routing.

The condition is:

```text
Does state.pending_action exist?
Does state.pending_follow_up exist?
Otherwise, is this a normal message?
```

### Why We Did Manual First

The manual runtime taught the important Agent patterns without hiding them behind a framework:

```text
write tools need confirmation
missing fields need follow-up
LLM output must pass through runtime policy
tool calls need logging and error handling
relative dates need deterministic normalization
state must survive across turns
```

Now LangGraph can be introduced as a way to organize known workflow states, not as magic.

### What LangGraph Would Add

LangGraph would give us a more formal place for:

```text
state schema
node definitions
conditional edges
checkpointing
resume after human input
retry/error paths
observability of workflow steps
```

The most important future upgrade is checkpointing.

Right now, `AgentState` is in memory inside one CLI process. If the process exits, pending confirmations disappear.

With a graph/checkpoint setup, we can eventually persist state and resume workflows more safely.

### What Not To Change Yet

We should not replace everything with LangGraph in one jump.

The safer next implementation path is:

```text
1. Add LangGraph dependency.
2. Create a minimal graph state schema.
3. Move normal message handling into one graph node.
4. Add conditional routing for pending follow-up and pending action.
5. Keep MCP tool execution and safety policy behavior unchanged.
```

The rule is: change orchestration structure without changing business behavior.

### How To Run Or Test

This step only adds documentation and comments.

Run a syntax check:

```bash
cd agent-python
python -m py_compile main.py
```

Expected result:

```text
No syntax errors.
```

### What You Learned

You learned how to recognize LangGraph concepts before installing LangGraph.

The key lesson:

```text
LangGraph is not the Agent intelligence.
LangGraph is the workflow orchestration structure around Agent state and transitions.
```

### Next Step

Next, we can introduce LangGraph in the smallest possible way:

```text
Phase 7 Step 7.8: Add LangGraph Dependency And Minimal Graph Skeleton
```

That step should not change user-visible Agent behavior yet.
