import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


TASK_API_BASE_URL = os.getenv("TASK_API_BASE_URL", "http://localhost:8080")

mcp = FastMCP("task-agent-mcp-server")


@mcp.tool()
def health_check() -> str:
    """Return a simple message confirming the MCP server is running."""
    return "Task MCP server is running."


@mcp.tool()
def list_tasks() -> list[dict[str, Any]]:
    """List tasks by calling the Java backend Task REST API."""
    response = httpx.get(f"{TASK_API_BASE_URL}/api/tasks", timeout=10.0)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_task(task_id: int) -> dict[str, Any]:
    """Get one task by id from the Java backend Task REST API."""
    response = httpx.get(f"{TASK_API_BASE_URL}/api/tasks/{task_id}", timeout=10.0)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run()
