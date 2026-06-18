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
