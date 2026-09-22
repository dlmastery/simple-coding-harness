"""Step 47 - register the tools server with TrueForge and list its tools.

`PUT /api/v1/settings/mcp-servers` takes a manifest and creates or replaces
the server by name. The tools server needs no auth, so the manifest has no
`auth` key. `GET /api/v1/mcp-servers/s47-tools/tools` then returns the MCP
`tools/list` entries verbatim, annotations included.

    python register.py [--url http://localhost:8931/mcp]
"""

import argparse

from trueforge_sdk import RemoteMcpServerManifest

from client.connect import BASE_URL, connect

SERVER_NAME = "s47-tools"
TOOLS_URL = "http://localhost:8931/mcp"
DESCRIPTION = (
    "Coding tools rooted at one project. Tools: read_file(path), list_dir(path), "
    "write_file(path, content), str_replace(path, old_str, new_str), bash(command)."
)


def register(client, url: str = TOOLS_URL) -> dict:
    """Create or replace the `s47-tools` entry. Returns the saved manifest as a dict."""
    manifest = RemoteMcpServerManifest(name=SERVER_NAME, url=url, description=DESCRIPTION)
    saved = client.settings.mcp_servers.create_or_update(manifest=manifest)
    return saved.data.manifest.model_dump(exclude_none=True)


def list_tools(client) -> list:
    """The tools TrueForge sees on the server, each with its annotations."""
    return client.mcp_servers.list_tools(name=SERVER_NAME).data


def gate(tool: dict) -> str:
    """What the default approval policy does with a tool, read from its annotations."""
    hints = tool.get("annotations") or {}
    if hints.get("readOnlyHint"):
        return "runs"
    if hints.get("destructiveHint", True):
        return "asks (@destructive)"
    return "asks (@write)"


def print_tools(tools: list) -> None:
    for tool in tools:
        hints = tool.get("annotations") or {}
        flags = ", ".join(f"{key}={str(value).lower()}" for key, value in sorted(hints.items()))
        print(f"  {tool['name']:<12} {gate(tool):<20} {flags}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register s47-tools with TrueForge.")
    parser.add_argument("--url", default=TOOLS_URL, help="the tools server's MCP endpoint")
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    client = connect(args.base_url)
    saved = register(client, args.url)
    print(f"registered {saved['name']} -> {saved['url']}")
    tools = list_tools(client)
    print(f"{len(tools)} tools:")
    print_tools(tools)


if __name__ == "__main__":
    main()
