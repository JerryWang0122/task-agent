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
