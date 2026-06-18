# Phase 4: Python Agent

## Goal

Create the Python Agent orchestration layer.

The Agent will eventually:

- receive natural-language user input
- decide which MCP tool to call
- call the MCP Server through an MCP client
- interpret tool results
- produce a helpful final answer

## Current Skeleton

The first Agent step creates a minimal CLI:

```text
python main.py
```

The CLI currently:

- prompts for user input
- exits on `exit` or `quit`
- returns a placeholder response

It does not call MCP tools yet.

## Responsibility Boundary

The Agent should not:

- connect to the database directly
- call Java repositories
- duplicate Java business rules
- silently perform write operations without confirmation

The intended data flow is:

```text
User
  -> Python Agent
  -> MCP Client
  -> MCP Server
  -> Java REST API
  -> Database
```

## Why Start With a Skeleton

Starting with a minimal CLI keeps the learning path clear.

Before adding LLMs or LangGraph-style workflows, we want to understand:

- where user input enters the system
- where tool calling will be added
- where final response generation belongs

This prevents the Agent from becoming a large black box too early.

## First MCP Client Connection

The Agent now has a `tools` command.

When the user types:

```text
tools
```

the Agent:

- starts `mcp-server/main.py` as a subprocess
- creates an MCP `ClientSession`
- calls `list_tools()`
- prints tool names and descriptions

This proves the Agent can discover tools through MCP metadata.

It still does not use an LLM yet.

Why this matters:

```text
Before an Agent can choose tools, it must be able to discover what tools exist.
```

Python executable note:

```text
The Agent uses MCP_SERVER_PYTHON when set.
Otherwise, it uses the same Python executable that started the Agent.
```

This matters when the Agent and MCP Server have separate virtual environments.

Verified result:

```text
The Agent CLI accepted the tools command.
The Agent started the MCP Server over stdio.
The Agent called list_tools().
The response included health_check, list_tasks, get_task, create_task, and complete_task.
```

## First MCP Tool Execution

The Agent now has a `tasks` command.

When the user types:

```text
tasks
```

the Agent:

- starts `mcp-server/main.py` as a subprocess
- creates an MCP `ClientSession`
- calls `call_tool("list_tasks", arguments={})`
- receives task data from the MCP Server
- formats the returned JSON into a readable task list

This proves the Agent can execute a read-only MCP tool.

The full runtime path is:

```text
User
  -> Python Agent tasks command
  -> MCP Client call_tool("list_tasks")
  -> MCP Server list_tasks tool
  -> Java GET /api/tasks
  -> H2 database
```

Why this matters:

```text
Tool discovery tells the Agent what it can do.
Tool execution lets the Agent actually use backend capabilities.
```

For now, the command is explicit.
Later, natural-language input such as "show my tasks" can map to this same tool call.

## First Natural-Language Routing Rule

The Agent now recognizes simple task-listing requests, such as:

```text
show my tasks
list todos
what tasks do I have
```

These requests call the same `list_tasks` MCP tool as the explicit `tasks` command.

The routing logic is intentionally simple:

```text
If the user message contains a task-related word and a list-related word,
then call list_tasks.
```

Why use a rule before an LLM:

- it makes the Agent control flow visible
- it keeps tool execution deterministic while learning
- it shows exactly where LLM-based tool selection will fit later

The updated flow is:

```text
User natural language
  -> Python Agent rule-based router
  -> MCP Client call_tool("list_tasks")
  -> MCP Server
  -> Java Task API
```

## First Tool Call With Arguments

The Agent now recognizes simple single-task requests, such as:

```text
task 1
show task 1
#1
```

These requests call the MCP `get_task` tool with an argument:

```text
call_tool("get_task", arguments={"task_id": 1})
```

This is a new Agent responsibility compared with `list_tasks`.
The Agent now has to do two things:

- choose the right tool
- extract the argument needed by that tool

The runtime path is:

```text
User says "show task 1"
  -> Python Agent extracts task_id = 1
  -> MCP Client call_tool("get_task", {"task_id": 1})
  -> MCP Server get_task tool
  -> Java GET /api/tasks/1
  -> H2 database
```

For now, argument extraction is rule-based with a small regular expression.
Later, an LLM can produce the same structured argument from natural language.

## First Confirmation Flow For A Write Tool

The Agent now recognizes task completion requests, such as:

```text
complete task 1
mark task 1 done
finish task 1
```

Unlike `list_tasks` and `get_task`, `complete_task` changes backend data.
The Agent therefore does not call the tool immediately.

Instead, it stores a pending action:

```text
pending_action = {"task_id": 1}
```

Then it asks the user to confirm:

```text
Confirm: mark task #1 as completed? Type 'yes' or 'no'.
```

Only after the user answers `yes` does the Agent call:

```text
call_tool("complete_task", arguments={"task_id": 1})
```

If the user answers `no`, the Agent clears the pending action and does not call the tool.

This is the first safety boundary in the Agent:

```text
Read-only tools can run directly.
Write tools require explicit confirmation.
```

Enterprise Agent systems need this pattern because tool calls can modify real business data.
