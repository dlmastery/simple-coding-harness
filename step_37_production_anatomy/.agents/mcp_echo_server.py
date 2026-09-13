"""Step 26 - a tiny MCP server: two tools, stdio transport.

The harness starts this file as a child process, per .agents/mcp.json, and
talks to it over stdin and stdout. FastMCP derives each tool's JSON schema
from the type hints, and the docstring becomes the description the model
reads. Logging is turned down so the server's stderr stays quiet in the
harness terminal.
"""

try:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:  # mcp 2.x renamed it
    from mcp.server.mcpserver import MCPServer as FastMCP

server = FastMCP("echo", log_level="WARNING")


@server.tool()
def echo(text: str) -> str:
    """Return the text unchanged."""
    return text


@server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


if __name__ == "__main__":
    server.run()
