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

The next step is to let the Agent take the LLM decision and execute read-only tools such as `list_tasks` and `get_task`.
