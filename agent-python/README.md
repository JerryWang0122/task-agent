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

## Run

```bash
python main.py
```

For this first skeleton step, the Agent only echoes that it received your message. MCP client integration will be added next.
