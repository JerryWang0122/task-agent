import asyncio
import json
import os
import re
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_DIR = PROJECT_ROOT / "mcp-server"


async def list_mcp_tools() -> str:
    """Start the MCP Server and return its available tool metadata."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()

            lines = ["Available MCP tools:"]
            for tool in tools.tools:
                lines.append(f"- {tool.name}: {tool.description}")

            return "\n".join(lines)


async def list_tasks() -> str:
    """Call the MCP list_tasks tool and format the result for the user."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("list_tasks", arguments={})

            structured_content = result.structuredContent or {}
            tasks = structured_content.get("result")
            if tasks is None:
                tasks = [json.loads(content.text) for content in result.content]

            if not tasks:
                return "No tasks found."

            lines = ["Tasks from the Java backend:"]
            for task in tasks:
                due_date = task.get("dueDate") or "no due date"
                lines.append(
                    f"- #{task['id']} {task['title']} "
                    f"[{task['status']}, {task['priority']}, due: {due_date}]"
                )

            return "\n".join(lines)


async def get_task(task_id: int) -> str:
    """Call the MCP get_task tool and format one task for the user."""
    server_python = os.getenv("MCP_SERVER_PYTHON", sys.executable)
    server_parameters = StdioServerParameters(
        command=server_python,
        args=["main.py"],
        cwd=MCP_SERVER_DIR,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_task", arguments={"task_id": task_id})

            structured_content = result.structuredContent or {}
            task = structured_content.get("result")
            if task is None:
                task = json.loads(result.content[0].text)

            due_date = task.get("dueDate") or "no due date"
            description = task.get("description") or "no description"
            return (
                f"Task #{task['id']}: {task['title']}\n"
                f"Status: {task['status']}\n"
                f"Priority: {task['priority']}\n"
                f"Due date: {due_date}\n"
                f"Description: {description}"
            )


def extract_task_id(user_message: str) -> int | None:
    """Extract a task id from simple phrases like 'task 1' or '#1'."""
    match = re.search(r"(?:task\s*#?|#)(\d+)", user_message.lower())
    if not match:
        return None

    return int(match.group(1))


def should_list_tasks(user_message: str) -> bool:
    """Return True when the user is asking to see task records."""
    normalized_message = user_message.lower()
    task_words = {"task", "tasks", "todo", "todos"}
    list_words = {"show", "list", "see", "view", "display", "what"}

    return any(word in normalized_message for word in task_words) and any(
        word in normalized_message for word in list_words
    )


def answer(user_message: str) -> str:
    """Return a placeholder response until MCP and LLM integration are added."""
    return (
        "Agent skeleton received your message: "
        f"{user_message}\n"
        "MCP tool calling will be added in the next steps."
    )


def main() -> None:
    print("Personal Task Agent")
    print("Type a task question, 'tools', 'tasks', or 'exit' to quit.")

    while True:
        user_message = input("> ").strip()

        if user_message.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return

        if not user_message:
            continue

        if user_message.lower() == "tools":
            print(asyncio.run(list_mcp_tools()))
            continue

        if user_message.lower() == "tasks":
            print(asyncio.run(list_tasks()))
            continue

        task_id = extract_task_id(user_message)
        if task_id is not None:
            print(asyncio.run(get_task(task_id)))
            continue

        if should_list_tasks(user_message):
            print(asyncio.run(list_tasks()))
            continue

        print(answer(user_message))


if __name__ == "__main__":
    main()
