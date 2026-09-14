"""Step 47 - the codelab's coding tools as a remote MCP server.

The five tools of stages 2 to 5 (read_file, list_dir, write_file,
str_replace, bash) served over streamable HTTP by FastMCP. Every tool is
rooted at one project directory and carries MCP annotations: the two
readers are `readOnlyHint`, the three writers are `destructiveHint`.
TrueForge reads those hints to decide which calls pause for approval.
Results are strings and errors are results, as in stage 5.

    python tools_server.py --project DIR [--host 127.0.0.1] [--port 8931]
"""

import argparse
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

SERVER_NAME = "s47-tools"
PROJECT = Path.cwd().resolve()

# TrueForge resolves `@read-only`, `@write` and `@destructive` from these hints.
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)


def resolve(path: str) -> Path:
    """Map a tool path onto the project. Raise ValueError when it escapes."""
    target = (PROJECT / path).resolve()
    if target != PROJECT and PROJECT not in target.parents:
        raise ValueError(f"{path} is outside the project {PROJECT}")
    return target


def read_file(path: str) -> str:
    """Read a file inside the project and return its contents."""
    try:
        return resolve(path).read_text(encoding="utf-8")
    except (OSError, ValueError) as error:
        return f"Error: {error}"


def list_dir(path: str = ".") -> str:
    """List a directory inside the project, one entry per line, directories with a trailing slash."""
    try:
        entries = sorted(resolve(path).iterdir(), key=lambda p: p.name)
    except (OSError, ValueError) as error:
        return f"Error: {error}"
    return "\n".join(f"{p.name}/" if p.is_dir() else p.name for p in entries) or "(empty)"


def write_file(path: str, content: str) -> str:
    """Create a file inside the project, or overwrite it if it already exists."""
    try:
        target = resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as error:
        return f"Error: {error}"
    return f"Wrote {path}"


def str_replace(path: str, old_str: str, new_str: str, allow_multi_edit: bool = False) -> str:
    """Replace exact text in a file. old_str must appear exactly once unless allow_multi_edit is set."""
    try:
        target = resolve(path)
        content = target.read_text(encoding="utf-8")
    except (OSError, ValueError) as error:
        return f"Error: {error}"
    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Add surrounding lines to make it unique, or set allow_multi_edit to replace them all."
        )
    target.write_text(content.replace(old_str, new_str), encoding="utf-8")
    return f"Replaced {count} match(es) in {path}"


def bash(command: str) -> str:
    """Run a shell command in the project directory and return its combined stdout and stderr."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60, cwd=PROJECT)
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 60 seconds"
    return (result.stdout + result.stderr) or "(no output)"


TOOLS = [
    (read_file, READ_ONLY),
    (list_dir, READ_ONLY),
    (write_file, DESTRUCTIVE),
    (str_replace, DESTRUCTIVE),
    (bash, DESTRUCTIVE),
]


def build_server(project: Path, host: str = "127.0.0.1", port: int = 8931) -> FastMCP:
    """Root the tools at `project` and return a FastMCP server with all five registered."""
    global PROJECT
    PROJECT = Path(project).resolve()
    server = FastMCP(SERVER_NAME, host=host, port=port, log_level="WARNING")
    for function, hints in TOOLS:
        server.tool(annotations=hints)(function)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the coding tools over MCP streamable HTTP.")
    parser.add_argument("--project", default=".", help="directory the tools are rooted at")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8931)
    args = parser.parse_args()
    server = build_server(Path(args.project), host=args.host, port=args.port)
    print(f"{SERVER_NAME}: serving {PROJECT} at http://{args.host}:{args.port}/mcp")
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
