import asyncio
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


def answer(user_message: str) -> str:
    """Return a placeholder response until MCP and LLM integration are added."""
    return (
        "Agent skeleton received your message: "
        f"{user_message}\n"
        "MCP tool calling will be added in the next steps."
    )


def main() -> None:
    print("Personal Task Agent")
    print("Type a task question, 'tools' to list MCP tools, or 'exit' to quit.")

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

        print(answer(user_message))


if __name__ == "__main__":
    main()
