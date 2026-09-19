"""Step 03 - an MCP App whose view is a hybrid: a catalog, plus one region the model writes.

Step 01's server returned rows for a view that drew them. This server's
tool, `lemonade_report`, returns two things in `structuredContent`:

1. `components`: a small declarative spec, the shape of sub-theme 01's
   static step, that the view renders with four registered renderers;
2. `generated`: one open-ended HTML document, written by the model, for a
   region the catalog does not cover. The server makes that model call:
   MCP Apps keeps credentials on the server side.

The view mounts the generated document in a nested sandboxed iframe with
its own content security policy, one boundary deeper than the app itself.
The resource, the `_meta` link and the app's policy are step 01's.

The resource must be one document: the app's policy allows no external
script. `view.html` imports two modules for the tests' sake, so `bundle`
inlines them when the resource is read (a fifteen-line bundler).

    python server.py            # streamable HTTP on http://127.0.0.1:8767/mcp
    python server.py --stdio    # stdio, for desktop hosts and the harness
"""

import argparse
import re
from pathlib import Path

import anyio
from mcp import types
from mcp.server.fastmcp import FastMCP

import data
import report

HERE = Path(__file__).parent
VIEW_URI = "ui://lemonade/report.html"
VIEW_FILE = HERE / "view.html"
MIME_TYPE = "text/html;profile=mcp-app"
PORT = 8767

# Unchanged from step 01: no external connections, no external scripts, and
# no frame-src either. A srcdoc frame has no URL to match, so the nested
# region loads under this policy and inherits it.
VIEW_META = {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": True}}

server = FastMCP("lemonade", host="127.0.0.1", port=PORT, json_response=True, log_level="WARNING")


@server.tool(meta={"ui": {"resourceUri": VIEW_URI}})
async def lemonade_report(days: int = 7, focus: str = report.DEFAULT_FOCUS) -> types.CallToolResult:
    """Sales report for the lemonade stand over the last `days` days (1 to 28), with one interactive region about `focus`, such as 'a what-if price slider'."""
    days = max(1, min(int(days), 28))
    rows = data.sales(days)
    # the server's own model call takes seconds: on a worker thread, so the host's parallel
    # resources/read (and every other client) is answered while it runs
    generated = await anyio.to_thread.run_sync(report.generate_region, days, rows, focus)
    text = data.as_text(days, rows) + f"\nThe interface also shows {focus} ({generated['source']})."
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structuredContent={"days": days, "focus": focus, "components": report.components_for(days, rows), "generated": generated},
    )


IMPORT = re.compile(r'^\s*import\s*\{[^}]*\}\s*from\s*"\./([\w.-]+\.mjs)";?[ \t]*$', re.M)
MODULE_SCRIPT = re.compile(r'<script type="module">(.*?)</script>', re.S)


def bundle(html, folder=HERE):
    """view.html with its module imports inlined: one classic script, every module once, exports stripped."""
    seen = set()

    def inline(name):
        if name in seen:
            return ""
        seen.add(name)
        source = (folder / name).read_text(encoding="utf-8")
        return IMPORT.sub(lambda m: inline(m.group(1)), source).replace("export ", "")

    return MODULE_SCRIPT.sub(lambda m: "<script>" + IMPORT.sub(lambda i: inline(i.group(1)), m.group(1)) + "</script>", html)


@server.resource(VIEW_URI, name="lemonade_report_view", mime_type=MIME_TYPE, meta=VIEW_META)
def report_view() -> str:
    """The report's HTML document, self-contained. Static: the data arrives later, over postMessage."""
    return bundle(VIEW_FILE.read_text(encoding="utf-8"))


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
