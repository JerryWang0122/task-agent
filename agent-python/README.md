# agent-python

This folder contains the Python Agent orchestration layer.

The Agent will:

- Receive natural-language input
- Decide which MCP tool to call
- Interpret tool results
- Produce a user-friendly answer

It should not duplicate backend business rules or access the database directly.

## Role in the architecture

```text
User
  -> Python Agent
  -> MCP Client
  -> MCP Server
  -> Java Spring Boot Task API
  -> H2 database
```

The Agent is responsible for workflow orchestration. It receives natural-language input, decides what tool is needed, calls MCP tools, and turns tool results into a useful answer.

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install -e .
```

Phase 7 introduces a minimal LangGraph skeleton. The graph now routes between normal-message, follow-up, and confirmation nodes. After installing dependencies, you can check it with:

```bash
python graph_runtime.py
```

Expected output:

```text
What is the task title? I will set the due date to <tomorrow's date>.
Confirm: create task 'Buy milk' due <tomorrow's date>? Type 'yes' or 'no'.
```

The Agent starts the MCP Server as a subprocess. If the MCP Server dependencies are installed in a different virtual environment, point the Agent at that Python executable:

```bash
export MCP_SERVER_PYTHON=../mcp-server/.venv/bin/python
```

To use the OpenAI decision-layer demo, set:

```bash
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-4.1-mini
```

## Run

```bash
python main.py
```

The primary Phase 7 interaction style is normal natural-language input:

```text
show overdue tasks
summarize my weekly workload
tasks due by Friday
create a task for tomorrow
complete task 1
```

If `OPENAI_API_KEY` is configured, normal messages can use OpenAI tool-calling automatically. If it is not configured, the Agent falls back to local tutorial routing so the project remains runnable without an LLM key.

To try the LangGraph runtime from the CLI, opt in with:

```bash
USE_LANGGRAPH_RUNTIME=1 python main.py
```

This routes normal task messages through the graph while keeping the manual runtime available as the default fallback.

Debug and teaching commands:

- `tools`: start the MCP Server and list available MCP tools
- `openai-tools`: convert selected MCP tool metadata into OpenAI function tool definitions
- `ask-llm <message>`: ask OpenAI for a structured Agent decision and execute safe read-only tools
- `ask-tools <message>`: ask OpenAI to choose a tool with automatic tool calling, then let the Agent runtime execute or request confirmation
- `exit`: quit the Agent CLI

The Agent also recognizes simple natural-language task listing requests, such as:

```text
show my tasks
list todos
what tasks do I have
```

It can also fetch one task by id:

```text
task 1
show task 1
#1
```

It can find overdue tasks:

```text
overdue
show overdue tasks
show high priority overdue tasks
show overdue tasks grouped by priority
```

It can summarize this week's workload:

```text
weekly
what tasks are due this week
summarize my weekly workload
```

It can normalize simple vague dates into backend date-range queries:

```text
tasks due today
tasks due tomorrow
tasks due next week
tasks due by Friday
```

The Agent runtime calculates these dates. The LLM may choose the tool, but the runtime owns deterministic date values.

Write operations require confirmation. To complete a task:

```text
complete task 1
yes
```

To create a task:

```text
create task Buy milk
yes
```

If the create request is missing the title, the Agent asks a follow-up question before confirmation:

```text
create a task for tomorrow
What is the task title? I will set the due date to <tomorrow's date>.
Buy milk
Confirm: create task 'Buy milk' due <tomorrow's date>? Type 'yes' or 'no'.
yes
```

Answer `no` to cancel without changing data.

Normal messages now go through a unified Agent handler. When `OPENAI_API_KEY` is set, the handler can use OpenAI tool-calling; otherwise it uses the local tutorial fallback rules.

The CLI keeps workflow state in an `AgentState` object. For now it tracks pending follow-up questions and pending confirmation actions. This makes the stateful Agent flow explicit before moving to a graph-based workflow.

Pending workflows are handled by dedicated functions: `handle_pending_action` for confirmation replies and `handle_pending_follow_up` for missing-information replies. This keeps the CLI loop focused on routing messages instead of owning every state transition.

Normal message handling now returns an `AgentTurnResult` object with named fields for `response`, `pending_action`, and `pending_follow_up`. This avoids positional tuple mistakes and makes future workflow transitions easier to model.

Pending state now uses typed dataclasses: `PendingAction` for write confirmations and `PendingFollowUp` for missing-information prompts. This replaces loose dictionaries such as `pending_action["type"]` with named attributes such as `pending_action.kind`.

Pending state kinds now use enums: `PendingActionKind` and `PendingFollowUpKind`. MCP tool names remain strings because they are external tool contract names; the enums are only for internal Agent workflow state.

The runtime is now graph-shaped and LangGraph is available as an opt-in path. Manual runtime remains the default; set `USE_LANGGRAPH_RUNTIME=1` to route normal task messages through LangGraph.

The `ask-llm` command returns a JSON decision. The Agent can execute read-only decisions such as `list_tasks` and `get_task`. Write decisions such as `create_task` and `complete_task` become pending confirmation actions before execution.

The `openai-tools` command shows how MCP tool metadata can be converted into OpenAI tool definitions. This is the bridge toward automatic OpenAI tool calling.

The `ask-tools` command uses those OpenAI tool definitions with `tool_choice="required"`. This command is a tool-calling demo path: OpenAI must request a tool call, but the Agent runtime still decides whether to execute it directly or ask for confirmation first.

Both `ask-llm` and `ask-tools` now pass through the same Agent decision policy, so confirmation rules are centralized instead of duplicated per command.

Every MCP business tool call now prints a simple `TOOL_CALL` log line with timestamp, tool name, status, and arguments. This gives the Agent a basic audit trail before adding production observability tools.

If a business tool call fails, the Agent prints a clear message instead of crashing. For example, if the Java backend is not running, the Agent tells you to check the backend and tool arguments.

The Agent forwards its environment variables to the MCP Server subprocess, so settings such as `TASK_API_BASE_URL` are honored when the Agent starts MCP tools.

The current CLI still keeps multiple demo commands:

- `ask-llm`: shows the explicit JSON decision layer
- `ask-tools`: shows OpenAI tool calling with MCP-derived tools
- `tasks`, `overdue`, and `weekly`: still work as simple natural-language shortcuts
- rule-based task commands: provide a simple comparison path while learning follow-up and confirmation

These commands are useful for learning because each one exposes a different part of the Agent runtime. They are not the final product shape.

Phase 7 should consolidate these into one normal natural-language Agent entrypoint with shared decision policy, follow-up state, confirmation state, and tool execution.
