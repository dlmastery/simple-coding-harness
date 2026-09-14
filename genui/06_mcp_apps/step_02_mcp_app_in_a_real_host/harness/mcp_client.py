"""Step 02 - the harness as an MCP Apps host, in text.

Step 26 of the harness codelab made this module: the harness starts each
configured MCP server, asks it for its tools, and registers them as
mcp__<server>__<tool>. This step adds what a host does with a tool that
carries a user interface. At registration, a tool's _meta.ui.resourceUri
is remembered. After a call to such a tool, the harness reads the ui://
resource once, then draws the result's structuredContent in the terminal
as a text card. The model still gets only the result's text content: the
data the view would render never enters the context window.

The harness does not declare the MCP Apps extension at initialize. That
capability is a promise to mount HTML in a sandboxed frame, and a terminal
cannot keep it. The server's text content is the fallback the spec asks
every UI tool to provide, and it is what the model reads here.

The mcp package is asyncio-only, and the harness is synchronous: it runs
the tool calls of one reply from a thread pool. So this module keeps one
background thread that runs an asyncio loop, and every MCP call is sent
there and awaited from the calling thread. Each server has one task on
that loop. The task opens the connection, hands the tool list back, then
sleeps until told to stop. It has to be that way: the contexts the mcp
package opens must be closed by the task that opened them.

The mcp package is imported inside functions, not at the top: it is an
optional dependency, and the rest of the harness must import without it.
"""

import asyncio
import json
import os
import sys
import threading
from pathlib import Path

from . import history

try:  # Python 3.11+ has it built in
    BaseExceptionGroup
except NameError:  # Python 3.10: anyio ships the backport
    from exceptiongroup import BaseExceptionGroup

CONFIG_PATHS = [
    Path.home() / ".simple-harness" / "mcp.json",  # every project
    Path.cwd() / ".agents" / "mcp.json",           # this project; wins on a clash
]

CONNECT_TIMEOUT = 30  # seconds a server may take to start and list its tools
CALL_TIMEOUT = 120    # seconds one tool call may take

SERVERS = {}  # name -> {"status": "connected" | "failed: ...", "tools": [names]}

UI_MIME_TYPE = "text/html;profile=mcp-app"
UI_TOOLS = {}      # mcp__<server>__<tool> -> the ui:// resource its result should render with
UI_RESOURCES = {}  # (server, uri) -> {"title", "mimeType", "size", "csp"}, read once per session
PENDING_APPS = []  # (mcp__<server>__<tool>, server, uri, result): cards to draw after the tool panel

_client = None


# --- configuration -----------------------------------------------------------


def load_config(paths=None):
    """Merge the server tables of every config file that exists.

    A later file overrides an earlier one, server by server. The command
    `python` becomes this interpreter, and a relative argument that names an
    existing file becomes its absolute path, so a shipped server starts
    from any working directory and on Windows.
    """
    servers = {}
    for path in paths or CONFIG_PATHS:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for name, spec in data.get("servers", {}).items():
            command = spec.get("command", "")
            if command in ("python", "python3"):
                command = sys.executable
            args = [resolve_arg(arg) for arg in spec.get("args", [])]
            env = {**os.environ, **spec["env"]} if spec.get("env") else None
            servers[name] = {"command": command, "args": args, "env": env}
    return servers


def resolve_arg(arg):
    """A relative path that exists becomes absolute; anything else is left alone."""
    candidate = Path.cwd() / arg
    if not Path(arg).is_absolute() and candidate.exists():
        return str(candidate.resolve())
    return arg


# --- the background loop -----------------------------------------------------


class Client:
    """One asyncio loop on one thread, and one task per connected server."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, name="mcp", daemon=True)
        self.thread.start()
        self.sessions = {}  # server name -> ClientSession, while connected
        self.stops = {}     # server name -> the Event that ends its task

    def submit(self, coro, timeout):
        """Run a coroutine on the loop thread and wait here for its result."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    async def serve(self, name, spec, ready, stop):
        """The one task that owns a server: connect, report the tools, wait, close."""
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        try:
            params = StdioServerParameters(command=spec["command"], args=spec["args"], env=spec.get("env"))
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                    self.sessions[name] = session
                    ready.set_result(tools)
                    await stop.wait()
        except BaseException as error:  # noqa: BLE001 - the caller decides what a failure means
            if not ready.done():
                ready.set_exception(error)
        finally:
            self.sessions.pop(name, None)

    async def start(self, name, spec):
        ready = self.loop.create_future()
        stop = asyncio.Event()
        task = self.loop.create_task(self.serve(name, spec, ready, stop))
        self.stops[name] = stop
        try:
            return await asyncio.wait_for(ready, CONNECT_TIMEOUT)
        except asyncio.TimeoutError:
            task.cancel()
            raise TimeoutError(f"no answer within {CONNECT_TIMEOUT}s")

    def connect(self, name, spec):
        """Start a server and return its tool list. Raises if it cannot start."""
        return self.submit(self.start(name, spec), CONNECT_TIMEOUT + 5)

    def call(self, server, tool, args):
        """Call one tool and return the raw result object."""
        session = self.sessions.get(server)
        if session is None:
            raise RuntimeError(f"MCP server {server} is not connected")
        return self.submit(session.call_tool(tool, args), CALL_TIMEOUT)

    def read(self, server, uri):
        """Read one resource and return the raw result object."""
        session = self.sessions.get(server)
        if session is None:
            raise RuntimeError(f"MCP server {server} is not connected")
        return self.submit(session.read_resource(uri), CALL_TIMEOUT)

    async def stop(self, name):
        self.stops[name].set()
        while name in self.sessions:
            await asyncio.sleep(0.01)

    def close(self):
        """Stop every server, then the loop and its thread."""
        for name in list(self.stops):
            try:
                self.submit(self.stop(name), 10)
            except Exception:  # noqa: BLE001 - shutting down; nothing left to report to
                pass
        self.stops.clear()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)


def client():
    global _client
    if _client is None:
        _client = Client()
    return _client


# --- registration ------------------------------------------------------------


def tool_name(server, tool):
    return f"mcp__{server}__{tool}"


def describe(error):
    """The first concrete message inside an error, or an error group."""
    while isinstance(error, BaseExceptionGroup) and error.exceptions:
        error = error.exceptions[0]
    lines = str(error).strip().splitlines()
    return f"{type(error).__name__}: {lines[0]}" if lines else type(error).__name__


def ui_resource_uri(tool):
    """The ui:// resource a tool asks to be rendered with, from _meta.ui.resourceUri, or None."""
    meta = getattr(tool, "meta", None) or {}
    return (meta.get("ui") or {}).get("resourceUri") or meta.get("ui/resourceUri")


def call_tool(server, tool, args):
    """Run one MCP tool and flatten its reply to a string.

    Text parts are joined with newlines; other parts are named by type. A
    result the server marks as an error, or a failure to reach the server at
    all, comes back as a string starting with Error:. A tool with a UI
    resource also gets its structuredContent drawn in the terminal; the
    string the model reads is the same either way.
    """
    try:
        result = client().call(server, tool, args)
    except Exception as error:  # noqa: BLE001 - the model reads the message and moves on
        return f"Error: {describe(error)}"
    parts = []
    for part in result.content:
        text = getattr(part, "text", None)
        parts.append(text if text is not None else f"[{getattr(part, 'type', 'content')} part]")
    text = "\n".join(parts) or "(no content)"
    if getattr(result, "isError", False):
        text = f"Error: {text}"
    uri = UI_TOOLS.get(tool_name(server, tool))
    if uri and not getattr(result, "isError", False):
        PENDING_APPS.append((tool_name(server, tool), server, uri, result))
    return history.cap(text)


def show_pending(name):
    """Draw the card queued for one tool call, if any. The loop calls this after the tool panel."""
    for entry in PENDING_APPS:
        if entry[0] == name:
            PENDING_APPS.remove(entry)
            show_app(*entry[1:])
            return True
    return False


def read_ui_resource(server, uri):
    """What a host learns from resources/read, kept per session: title, MIME type, size, CSP."""
    from . import ui_text

    if (server, uri) not in UI_RESOURCES:
        contents = client().read(server, uri).contents[0]
        html = getattr(contents, "text", None) or ""
        meta = getattr(contents, "meta", None) or {}
        UI_RESOURCES[(server, uri)] = {
            "title": ui_text.title_of(html) or uri,
            "mimeType": contents.mimeType,
            "size": len(html.encode("utf-8")),
            "csp": (meta.get("ui") or {}).get("csp") or {},
        }
    return UI_RESOURCES[(server, uri)]


def show_app(server, uri, result):
    """The terminal's version of mounting the view: the resource's facts and the data as text."""
    from . import ui_text
    from .ui import ui

    try:
        resource = read_ui_resource(server, uri)
    except Exception as error:  # noqa: BLE001 - a missing resource is the server's bug, not the turn's
        ui.note(f"ui resource {uri} could not be read ({describe(error)})")
        return
    if resource["mimeType"] != UI_MIME_TYPE:
        ui.note(f"ui resource {uri} is {resource['mimeType']}, not {UI_MIME_TYPE}; not rendered")
        return
    data = getattr(result, "structuredContent", None)
    body = ui_text.lines(data) if data is not None else ["(no structuredContent: the text above is all there is)"]
    domains = sum(len(value) for value in resource["csp"].values())
    policy = f"{domains} declared domain(s)" if domains else "restrictive default"
    subtitle = f"{uri} | {resource['mimeType']} | {resource['size']:,} bytes | csp: {policy} | rendered as text"
    ui.app(resource["title"], subtitle, body)


def register(server, tools):
    """Add each tool to TOOLS and TOOL_SCHEMAS as mcp__<server>__<tool>."""
    from . import tools as registry  # here, not at the top: tools is imported first and imports this module

    names = []
    for tool in tools:
        name = tool_name(server, tool.name)
        if ui_resource_uri(tool):
            UI_TOOLS[name] = ui_resource_uri(tool)

        def wrapper(_tool=tool.name, **args):
            return call_tool(server, _tool, args)

        registry.TOOLS[name] = wrapper
        registry.TOOL_SCHEMAS.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool.description or f"{tool.name} from the {server} MCP server",
                "parameters": tool.inputSchema or {"type": "object", "properties": {}},
            },
        })
        names.append(name)
    return names


def connect_all(config=None):
    """Start every configured server and register its tools. Failures are notes."""
    from .ui import ui

    for name, spec in (config if config is not None else load_config()).items():
        try:
            tools = client().connect(name, spec)
        except Exception as error:  # noqa: BLE001 - one bad server must not stop the session
            SERVERS[name] = {"status": f"failed: {describe(error)}", "tools": []}
            ui.note(f"mcp server {name!r} failed to start ({describe(error)}); skipped")
            continue
        SERVERS[name] = {"status": "connected", "tools": register(name, tools)}
    return SERVERS


def close_all():
    """Stop every server. A no-op when none was started."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
