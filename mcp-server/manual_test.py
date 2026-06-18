import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["main.py"],
        cwd=Path(__file__).parent,
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print("  Name:", tool.name)
                print("  Description:", tool.description)
                print("  Input schema:", tool.inputSchema)
                print("=============")

            result = await session.call_tool("list_tasks", arguments={})
            print("list_tasks result:")

            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)
                else:
                    print(json.dumps(content.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
