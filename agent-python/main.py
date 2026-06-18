import asyncio
import json
import os
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

        print(answer(user_message))


if __name__ == "__main__":
    main()
