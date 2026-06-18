from mcp.server.fastmcp import FastMCP


mcp = FastMCP("task-agent-mcp-server")


@mcp.tool()
def health_check() -> str:
    """Return a simple message confirming the MCP server is running."""
    return "Task MCP server is running."


if __name__ == "__main__":
    mcp.run()
