# agent-python

This folder contains the Python Agent orchestration layer.

The Agent will:

- Receive natural-language input
- Decide which MCP tool to call
- Interpret tool results
- Produce a user-friendly answer

It should not duplicate backend business rules or access the database directly.

## Role in the architecture

```text
User
  -> Python Agent
  -> MCP Client
  -> MCP Server
  -> Java Spring Boot Task API
  -> H2 database
```

The Agent is responsible for workflow orchestration. It receives natural-language input, decides what tool is needed, calls MCP tools, and turns tool results into a useful answer.

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install -e .
```

The Agent starts the MCP Server as a subprocess. If the MCP Server dependencies are installed in a different virtual environment, point the Agent at that Python executable:

```bash
export MCP_SERVER_PYTHON=../mcp-server/.venv/bin/python
```

## Run

```bash
python main.py
```

Available local commands:

- `tools`: start the MCP Server and list available MCP tools
- `exit`: quit the Agent CLI

For this step, the Agent can inspect MCP tools but does not yet decide which tool to call for natural-language requests.
