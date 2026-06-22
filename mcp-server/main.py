import os
from typing import Any, Literal

import httpx
from mcp.server.fastmcp import FastMCP


TASK_API_BASE_URL = os.getenv("TASK_API_BASE_URL", "http://localhost:8080")
TaskPriority = Literal["LOW", "MEDIUM", "HIGH", "URGENT"]

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


@mcp.tool()
def find_overdue_tasks(priority: TaskPriority | None = None) -> list[dict[str, Any]]:
    """Find open overdue tasks, optionally filtered by priority, by calling the Java backend."""
    params = {"priority": priority} if priority is not None else None
    response = httpx.get(f"{TASK_API_BASE_URL}/api/tasks/overdue", params=params, timeout=10.0)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def create_task(
    title: str,
    description: str | None = None,
    priority: TaskPriority | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Create a task by calling the Java backend Task REST API."""
    request_body = {
        "title": title,
        "description": description,
        "priority": priority,
        "dueDate": due_date,
    }

    response = httpx.post(f"{TASK_API_BASE_URL}/api/tasks", json=request_body, timeout=10.0)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def complete_task(task_id: int) -> dict[str, Any]:
    """Mark one task as completed by calling the Java backend Task REST API."""
    response = httpx.patch(f"{TASK_API_BASE_URL}/api/tasks/{task_id}/complete", timeout=10.0)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    mcp.run()
