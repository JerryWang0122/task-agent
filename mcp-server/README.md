# mcp-server

This folder contains the MCP Server for the Personal Task Management Agent tutorial.

The MCP Server exposes selected backend capabilities as tools for the Agent, such as:

- `list_tasks`
- `get_task`
- `create_task`
- `complete_task`

It should call the Java backend API. It should not connect to the database directly.

## Role in the architecture

```text
Python Agent
  -> MCP Server
  -> Java Spring Boot Task API
  -> H2 database
```

The MCP Server is the AI-facing boundary. It gives the Agent a small set of safe, documented tools instead of exposing the database or Java internals directly.

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -e .
```

## Run

Start the Java backend first:

```bash
cd ../backend-java
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mvn spring-boot:run
```

Then start the MCP Server in another terminal:

```bash
python main.py
```

The server exposes these tools:

- `health_check`: confirms the MCP Server is running
- `list_tasks`: calls `GET /api/tasks` on the Java backend

By default, the MCP Server calls:

```text
http://localhost:8080
```

To point it at another backend URL, set:

```bash
export TASK_API_BASE_URL=http://localhost:8080
```

## Tool flow

```text
Agent
  -> list_tasks MCP tool
  -> GET http://localhost:8080/api/tasks
  -> Java TaskController
  -> TaskService
  -> TaskJpaRepository
  -> H2 database
```

This keeps the MCP Server thin. It exposes an Agent-friendly tool, but the Java backend still owns the task business logic and persistence.

## Manual MCP client test

With the Java backend running, call the MCP tool through a small MCP client script:

```bash
python manual_test.py
```

If your shell does not provide a `python` command, use the virtual environment Python directly:

```bash
.venv/bin/python manual_test.py
```

Expected result:

```text
Available tools: health_check, list_tasks
list_tasks result:
...
```

The task data should match the response from:

```bash
curl http://localhost:8080/api/tasks
```
