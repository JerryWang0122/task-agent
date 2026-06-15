# mcp-server

This folder will contain the MCP Server.

The MCP Server exposes selected backend capabilities as tools for the Agent, such as:

- `list_tasks`
- `get_task`
- `create_task`
- `complete_task`

It should call the Java backend API. It should not connect to the database directly.
