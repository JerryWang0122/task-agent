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

```bash
python main.py
```

For this first skeleton step, the server only exposes a simple `health_check` tool. In the next step, we will add `list_tasks` and connect it to the Java backend API.
