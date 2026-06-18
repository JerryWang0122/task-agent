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

## Second Tool: get_task

`get_task` retrieves one task by id.

Purpose:

```text
Return one specific task to the Agent when the task id is known.
```

Backend API it calls:

```text
GET /api/tasks/{id}
```

Tool input:

```text
task_id: integer
```

The MCP tool schema is generated from the Python function signature:

```python
def get_task(task_id: int) -> dict[str, Any]:
```

The tool description is generated from the Python docstring:

```python
"""Get one task by id from the Java backend Task REST API."""
```

Data flow:

```text
Agent
  -> get_task MCP tool with task_id
  -> Java REST API GET /api/tasks/{id}
  -> TaskService
  -> TaskJpaRepository
  -> H2 database
```

Why this tool matters:

```text
An Agent often lists tasks first, then fetches one task for detail before answering or deciding what to do next.
```

Verified result:

```text
The MCP client listed get_task as an available tool.
The generated input schema required task_id as an integer.
The MCP client called get_task with task_id = 1.
The tool called GET http://localhost:8080/api/tasks/1 successfully.
```

## Third Tool: create_task

`create_task` creates a new task through the Java backend.

Purpose:

```text
Allow the Agent to create a task after it has enough user-provided task details.
```

Backend API it calls:

```text
POST /api/tasks
```

Tool inputs:

```text
title: string, required
description: string, optional
priority: LOW, MEDIUM, HIGH, or URGENT, optional
due_date: string, optional ISO date such as 2026-06-21
```

Priority schema:

```python
TaskPriority = Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
```

This helps the Agent understand valid priority values from MCP tool metadata.

It is not a replacement for backend validation. The Java API should still reject invalid values because other clients can call the REST API directly.

Request body sent to Java:

```json
{
  "title": "...",
  "description": "...",
  "priority": "LOW",
  "dueDate": "2026-06-21"
}
```

Important boundary:

```text
The MCP Server does not assign status, createdAt, or updatedAt.
TaskService in the Java backend owns those business defaults.
```

Safety note:

```text
create_task is a write operation.
The tutorial tests it directly in Phase 3, but the Agent workflow should require confirmation before using it automatically.
```

Data flow:

```text
Agent
  -> create_task MCP tool
  -> Java REST API POST /api/tasks
  -> TaskService applies defaults
  -> TaskJpaRepository saves to H2
```

Verified result:

```text
The MCP client listed create_task as an available tool.
The generated input schema required title.
The generated input schema constrained priority to LOW, MEDIUM, HIGH, or URGENT.
The MCP client called create_task with title, description, priority, and due_date.
The tool called POST http://localhost:8080/api/tasks successfully.
The Java backend returned HTTP 201 and created task id 5.
```
