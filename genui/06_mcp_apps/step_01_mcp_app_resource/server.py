"""Step 01 - an MCP server whose tool result comes with a user interface.

MCP Apps (SEP-1865) adds three things to a plain MCP server:

1. a resource with a `ui://` URI and the MIME type `text/html;profile=mcp-app`,
   whose text is a complete HTML document (the "view");
2. a tool that points at that resource through `_meta.ui.resourceUri`;
3. a tool result with `content` (text, for the model) and `structuredContent`
   (data, for the view).

The host does the rest: it reads the resource, renders it in a sandboxed
iframe and hands it the tool result over postMessage. A host that does not
know MCP Apps ignores the metadata and shows the text. That is the whole
extension; the server stays a normal FastMCP server.

    python server.py            # streamable HTTP on http://127.0.0.1:8765/mcp
    python server.py --stdio    # stdio, for desktop hosts and the harness
"""

import argparse
from pathlib import Path

from mcp import types
from mcp.server.fastmcp import FastMCP

import data

VIEW_URI = "ui://lemonade/dashboard.html"
VIEW_FILE = Path(__file__).parent / "view.html"
MIME_TYPE = "text/html;profile=mcp-app"
PORT = 8765

# Restrictive by default: no external connections, no external scripts. The
# view is self-contained, so nothing needs to be declared. A view that loads
# a chart library from a CDN would list it under resourceDomains.
VIEW_META = {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": True}}

server = FastMCP("lemonade", host="127.0.0.1", port=PORT, json_response=True, log_level="WARNING")


@server.tool(meta={"ui": {"resourceUri": VIEW_URI}})
def lemonade_dashboard(days: int = 7) -> types.CallToolResult:
    """Sales dashboard for the lemonade stand over the last `days` days (1 to 28)."""
    days = max(1, min(int(days), 28))
    rows = data.sales(days)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=data.as_text(days, rows))],
        structuredContent={"days": days, "rows": rows, "summary": data.summary(rows)},
    )


@server.resource(VIEW_URI, name="lemonade_dashboard_view", mime_type=MIME_TYPE, meta=VIEW_META)
def dashboard_view() -> str:
    """The dashboard's HTML document. Static: the data arrives later, over postMessage."""
    return VIEW_FILE.read_text(encoding="utf-8")


def http_app():
    """The ASGI app: the MCP endpoint at /mcp, open to browser hosts on other origins."""
    from starlette.middleware.cors import CORSMiddleware

    app = server.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"],  # the browser must read this one back
    )
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stdio", action="store_true", help="speak MCP over stdin/stdout instead of HTTP")
    parser.add_argument("--port", type=int, default=PORT)
    cli = parser.parse_args()
    if cli.stdio:
        server.run(transport="stdio")
        return
    import uvicorn

    server.settings.port = cli.port
    print(f"lemonade MCP server on http://127.0.0.1:{cli.port}/mcp", flush=True)
    uvicorn.run(http_app(), host="127.0.0.1", port=cli.port, log_level="warning")


if __name__ == "__main__":
    main()
