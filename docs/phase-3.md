# Phase 3: MCP Server

## Goal

Expose selected Java backend capabilities as MCP tools that an Agent can call.

The MCP Server should stay thin:

```text
MCP tool
  -> calls Java REST API
  -> returns structured data to the Agent
```

It should not:

- connect to the database directly
- duplicate Java business logic
- bypass `TaskService`
- know JPA or H2 details

## Language Choice Note

The company context for this learning project is Java-heavy.

For the tutorial, we are starting the MCP Server in Python because:

- the future Agent layer will also be Python
- Python `FastMCP` makes the MCP concept easy to learn
- the MCP layer stays clearly separate from the Java business backend
- we can focus on tool design before framework integration details

This does not mean MCP Servers should always be Python.

In a Java-heavy enterprise environment, a Java MCP Server can be a strong production choice because it can reuse:

- Spring Boot deployment patterns
- Java observability and logging standards
- existing authentication and authorization libraries
- existing CI/CD pipelines
- team Java knowledge

Planned follow-up after the first Python MCP path works:

```text
Compare Python MCP Server vs Java MCP Server for enterprise usage.
```

The key architectural rule remains the same in either language:

```text
MCP Server calls the Java REST API.
The Java backend owns task business logic and persistence.
```

## First Tool: list_tasks

`list_tasks` is the first real MCP tool in this project.

Purpose:

```text
Return the current task list to the Agent.
```

Backend API it calls:

```text
GET /api/tasks
```

Default backend base URL:

```text
http://localhost:8080
```

Environment variable override:

```text
TASK_API_BASE_URL
```

Data flow:

```text
Agent
  -> list_tasks MCP tool
  -> Java REST API GET /api/tasks
  -> TaskService
  -> TaskJpaRepository
  -> H2 database
```

Important design point:

```text
The MCP tool does not query the database directly.
It only calls the Java API and returns that API result.
```

## Manual Test Client

`manual_test.py` is a small MCP client used for local verification.

It does three things:

- starts `main.py` as an MCP Server over stdio
- lists available MCP tools
- calls `list_tasks`

Implementation note:

```text
The script uses the same Python executable that runs manual_test.py.
This avoids assuming that a shell-level python command exists.
```

Why this matters:

```text
Running python main.py only starts the server and waits.
manual_test.py proves that a client can actually call the MCP tool.
```

Expected local test flow:

```text
Terminal 1: start Java backend
Terminal 2: run python manual_test.py
```

Expected output includes:

```text
Available tools: health_check, list_tasks
list_tasks result:
```

Verified result:

```text
The MCP client called list_tasks successfully.
The tool called GET http://localhost:8080/api/tasks.
The response included the 4 seeded tasks from the Java backend.
```
