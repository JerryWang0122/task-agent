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
