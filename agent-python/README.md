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

To use the OpenAI decision-layer demo, set:

```bash
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-4.1-mini
```

## Run

```bash
python main.py
```

Available local commands:

- `tools`: start the MCP Server and list available MCP tools
- `openai-tools`: convert selected MCP tool metadata into OpenAI function tool definitions
- `tasks`: call the MCP `list_tasks` tool and show tasks from the Java backend
- `ask-llm <message>`: ask OpenAI for a structured Agent decision and execute safe read-only tools
- `ask-tools <message>`: ask OpenAI to choose a tool with automatic tool calling, then let the Agent runtime execute or request confirmation
- `exit`: quit the Agent CLI

The Agent also recognizes simple natural-language task listing requests, such as:

```text
show my tasks
list todos
what tasks do I have
```

It can also fetch one task by id:

```text
task 1
show task 1
#1
```

Write operations require confirmation. To complete a task:

```text
complete task 1
yes
```

To create a task:

```text
create task Buy milk
yes
```

Answer `no` to cancel without changing data.

For this step, routing is rule-based. Later, an LLM can replace this rule and choose tools from MCP metadata.

The `ask-llm` command returns a JSON decision. The Agent can execute read-only decisions such as `list_tasks` and `get_task`. Write decisions such as `create_task` and `complete_task` become pending confirmation actions before execution.

The `openai-tools` command shows how MCP tool metadata can be converted into OpenAI tool definitions. This is the bridge toward automatic OpenAI tool calling.

The `ask-tools` command uses those OpenAI tool definitions with `tool_choice="required"`. This command is a tool-calling demo path: OpenAI must request a tool call, but the Agent runtime still decides whether to execute it directly or ask for confirmation first.

Both `ask-llm` and `ask-tools` now pass through the same Agent decision policy, so confirmation rules are centralized instead of duplicated per command.

Every MCP business tool call now prints a simple `TOOL_CALL` log line with timestamp, tool name, status, and arguments. This gives the Agent a basic audit trail before adding production observability tools.
