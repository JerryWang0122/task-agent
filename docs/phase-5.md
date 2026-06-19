# Phase 5: LLM-Powered Agent

## Goal

Replace the temporary rule-based routing with an LLM decision layer.

The intended flow is:

```text
User natural language
  -> LLM decision layer
  -> Agent runtime
  -> MCP tool execution
  -> Java backend
```

## Step 5.1: OpenAI Decision Layer Skeleton

The Agent now has an `ask-llm` command.

Example:

```text
ask-llm show my tasks
```

This calls OpenAI and asks for a structured JSON decision.

The expected decision shape is:

```json
{
  "action": "respond|call_tool",
  "tool_name": null,
  "arguments": {},
  "requires_confirmation": false,
  "response": null
}
```

Why this step does not execute tools yet:

```text
The LLM should decide what should happen.
The Agent runtime should decide whether and how to execute it.
```

This separation matters for safety.
For example, the LLM may suggest `complete_task`, but the Agent policy still requires user confirmation before calling the MCP tool.

## OpenAI Configuration

Set these environment variables before using `ask-llm`:

```bash
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-4.1-mini
```

If `OPENAI_API_KEY` is missing, the Agent prints a clear setup message instead of crashing.

## Current Boundary

Temporary rule-based commands still exist so the Agent remains usable while the LLM layer is introduced.

## Step 5.2: Execute Read-Only LLM Decisions

The Agent now parses the LLM decision JSON and passes it through an execution policy.

Supported read-only decisions:

```json
{
  "action": "call_tool",
  "tool_name": "list_tasks",
  "arguments": {},
  "requires_confirmation": false,
  "response": null
}
```

```json
{
  "action": "call_tool",
  "tool_name": "get_task",
  "arguments": {
    "task_id": 1
  },
  "requires_confirmation": false,
  "response": null
}
```

For these tools, the Agent executes the MCP call and returns the result.

Write tools are intentionally blocked for now:

```text
LLM suggested write tool complete_task. Confirmation flow will be added next.
```

Why this matters:

```text
The LLM can propose an action.
The Agent policy decides whether that action is allowed now.
```

This is the first step where natural language can flow through the LLM into MCP tool execution.

## LLM Output Normalization

LLM output should be treated as untrusted structured data.

For example, the prompt asks for:

```json
{
  "action": "call_tool",
  "tool_name": "get_task"
}
```

But a model may return:

```json
{
  "action": "get_task",
  "tool_name": "get_task"
}
```

The Agent runtime now normalizes known tool names in the `action` field back to:

```json
{
  "action": "call_tool",
  "tool_name": "get_task"
}
```

This teaches an important production rule:

```text
Prompting helps, but runtime validation and normalization are still required.
```

## Step 5.3: Write Decisions Become Confirmations

The Agent can now accept LLM decisions for write tools, but it still does not execute them immediately.

Example LLM decision:

```json
{
  "action": "call_tool",
  "tool_name": "complete_task",
  "arguments": {
    "task_id": 1
  },
  "requires_confirmation": true,
  "response": null
}
```

The Agent converts this into a pending confirmation action:

```text
Confirm: mark task #1 as completed? Type 'yes' or 'no'.
```

Only after the user answers `yes` does the Agent call the MCP `complete_task` tool.

This keeps the safety boundary in the Agent runtime:

```text
LLM proposes write action.
Agent asks user for confirmation.
User confirms.
Agent executes MCP tool.
```

## Later: OpenAI Tool Calling

This phase currently uses an explicit JSON decision contract because it makes the Agent loop visible.

Later, we can map MCP tool metadata into OpenAI tool definitions and let OpenAI return tool calls directly.

Even then, the same boundary remains:

```text
The model may request a tool call.
The Agent runtime still validates, applies safety policy, and executes the MCP tool.
```

## Step 5.4: Convert MCP Tools To OpenAI Tools

The Agent now has an `openai-tools` command.

This command does not call OpenAI yet. It only shows the schema bridge between MCP and OpenAI.

The flow is:

```text
Agent starts MCP Server
  -> Agent calls MCP list_tools()
  -> MCP returns tool names, descriptions, and input schemas
  -> Agent converts selected tools into OpenAI function tool definitions
```

Example MCP tool metadata:

```text
Tool name: get_task
Description: Get one task by id from the Java backend Task REST API.
Input schema: {"task_id": "integer"}
```

OpenAI expects a function tool shape:

```json
{
  "type": "function",
  "function": {
    "name": "get_task",
    "description": "Get one task by id from the Java backend Task REST API.",
    "parameters": {
      "type": "object",
      "properties": {
        "task_id": {
          "type": "integer"
        }
      },
      "required": ["task_id"]
    }
  }
}
```

Why this matters:

```text
MCP is the source of tool metadata.
OpenAI tool calling needs tool metadata in OpenAI's format.
The Agent runtime performs the conversion and still controls execution.
```

The Agent intentionally exposes only selected tools to the model:

```text
list_tasks
get_task
create_task
complete_task
```

This is a safety and product-design choice. Just because an MCP Server has a tool does not mean every Agent or model should be allowed to see it.

## Step 5.5: OpenAI Automatic Tool Calling

The Agent now has an `ask-tools` command.

This command uses OpenAI's tool calling flow:

```text
User message
  -> Agent fetches MCP tool metadata
  -> Agent converts MCP tools into OpenAI tool definitions
  -> OpenAI requests a tool call
  -> Agent converts the OpenAI tool call into an internal decision
  -> Agent runtime applies safety policy
  -> Agent executes MCP tool or asks for confirmation
```

The important difference from `ask-llm` is where the tool decision comes from.

`ask-llm` asks the model to return our custom JSON shape:

```json
{
  "action": "call_tool",
  "tool_name": "list_tasks",
  "arguments": {}
}
```

`ask-tools` gives OpenAI tool definitions and requires the model to return an OpenAI tool call:

```text
tool_call: list_tasks({})
```

The Agent then normalizes that OpenAI tool call into the same internal decision shape used by the rest of the runtime.

This means both paths share one policy layer:

```text
Read-only tools:
  execute through MCP immediately

Write tools:
  convert to pending action
  ask user for confirmation
  execute through MCP only after yes
```

This is the enterprise pattern to remember:

```text
The model may choose a tool.
The Agent runtime owns execution.
The backend owns business rules and data.
```

For this tutorial step, `ask-tools` uses `tool_choice="required"` instead of `tool_choice="auto"`.

Why:

```text
If the model responds with natural language like "Confirm to proceed?",
the Agent does not have a pending tool action.

The confirmation must belong to the Agent runtime,
so write intents need to become tool calls first.
```

Later, a more complete Agent can use `tool_choice="auto"` together with a richer planner that decides when tool use is optional.

## Step 5.6: Unified Decision Policy Pipeline

The Agent now routes both LLM decision styles through one policy function.

Before this step, the CLI had similar logic in two places:

```text
ask-llm decision
  -> check if write action needs confirmation
  -> otherwise execute read-only tool

ask-tools decision
  -> check if write action needs confirmation
  -> otherwise execute read-only tool
```

That duplication is risky because future safety rules could be added to one path but forgotten in the other.

The Agent now uses a shared pipeline:

```text
LLM decision or OpenAI tool call
  -> normalized internal decision
  -> apply_decision_policy()
  -> pending confirmation or immediate result
```

This keeps the Agent loop simpler:

```text
Decision source can vary.
Policy should stay centralized.
Execution should still go through MCP.
```

This prepares the project for later workflow frameworks such as LangGraph, where this same policy step can become a graph node.

## Step 5.7: Tool Call Logging

The Agent now logs every MCP business tool call.

The first version is intentionally simple. Each tool call prints a line like:

```text
TOOL_CALL timestamp=2026-06-19T12:00:00+00:00 tool=list_tasks status=started arguments={}
TOOL_CALL timestamp=2026-06-19T12:00:01+00:00 tool=list_tasks status=succeeded arguments={}
```

The Agent logs three fields that matter for an audit trail:

```text
Which tool was called?
What arguments were sent?
Did the call start, succeed, or fail?
```

The implementation uses a shared wrapper:

```text
list_tasks()
get_task()
create_task()
complete_task()
  -> call_mcp_tool()
  -> log started
  -> session.call_tool(...)
  -> log succeeded or failed
```

Why this matters in enterprise Agent systems:

```text
Tool calls may read or modify business data.
Users and operators need to know what the Agent attempted.
Logs are the foundation for auditing, debugging, metrics, and tracing.
```

This is not a full production observability solution yet. Later enhancements could replace `print()` logs with structured logging, OpenTelemetry spans, LangSmith traces, or persistent audit records.
