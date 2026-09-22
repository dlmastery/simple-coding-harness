"""Step 26 - MCP client: tools served by other processes, over stdio.

The Model Context Protocol lets a tool live in its own process. The harness
starts each configured server, asks it for its tools, and registers them
in the tool registry as mcp__<server>__<tool>, with the server's own JSON
schema as the parameters. The model calls them like any other tool.

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
import re
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
STOP_TIMEOUT = 10     # seconds a server gets to close on its own before its task is cancelled

SERVERS = {}  # name -> {"status": "connected" | "failed: ...", "tools": [names]}

_client = None
_client_lock = threading.Lock()  # tool calls come from a pool: one client, not two


# --- configuration -----------------------------------------------------------


def load_config(paths=None):
    """Merge the server tables of every config file that exists.

    A later file overrides an earlier one, server by server. The command
    `python` becomes this interpreter, and a relative argument that names an
    existing file becomes its absolute path, so a shipped server starts
    from any working directory and on Windows. The table may be called
    `servers` or, as in other clients' files, `mcpServers`. A file that is
    not JSON is noted and skipped; the session goes on without it.
    """
    from .ui import ui

    servers = {}
    for path in paths or CONFIG_PATHS:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            table = data.get("servers") or data.get("mcpServers") or {}
        except (OSError, ValueError, AttributeError) as failed:
            ui.note(f"mcp config {path} skipped: {type(failed).__name__}: {failed}")
            continue
        for name, spec in table.items():
            if not isinstance(spec, dict):
                continue
            command = spec.get("command", "")
            if command in ("python", "python3"):
                command = sys.executable
            args = [resolve_arg(str(arg)) for arg in spec.get("args", [])]
            env = {str(k): os.path.expandvars(str(v)) for k, v in (spec.get("env") or {}).items()}
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
        self.tasks = {}     # server name -> the task, so stop() can cancel one that will not end

    def submit(self, coro, timeout):
        """Run a coroutine on the loop thread and wait here for its result.

        A call that outlives the timeout is cancelled, so it does not keep
        running on the loop and hold up the next call to the same server.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout)
        except TimeoutError:
            future.cancel()
            raise TimeoutError(f"no answer within {timeout}s")

    async def serve(self, name, spec, ready, stop):
        """The one task that owns a server: connect, report the tools, wait, close."""
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client

        try:
            # the server sees a minimal environment plus what the config names,
            # never the harness's own keys: ${VAR} in a value is expanded from ours
            params = StdioServerParameters(command=spec["command"], args=spec["args"], env={**get_default_environment(), **(spec.get("env") or {})})
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
            if isinstance(error, asyncio.CancelledError):
                raise  # a cancelled task must say so, or asyncio thinks it ended on its own
        finally:
            self.sessions.pop(name, None)

    async def start(self, name, spec):
        ready = self.loop.create_future()
        stop = asyncio.Event()
        task = self.loop.create_task(self.serve(name, spec, ready, stop))
        self.stops[name] = stop
        self.tasks[name] = task
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

    async def stop(self, name):
        """Ask the server's task to end, and cancel it when it does not.

        A server that ignores the closed stdin would otherwise be left
        running after the harness exits; cancelling the task makes
        stdio_client terminate the process on its way out.
        """
        self.stops[name].set()
        try:
            await asyncio.wait_for(self.tasks.pop(name), STOP_TIMEOUT)  # cancels the task on timeout
        except (asyncio.TimeoutError, asyncio.CancelledError, Exception):  # noqa: BLE001 - shutting down
            pass

    def close(self):
        """Stop every server, then the loop and its thread."""
        for name in list(self.stops):
            try:
                self.submit(self.stop(name), STOP_TIMEOUT + 5)
            except Exception:  # noqa: BLE001 - shutting down; nothing left to report to
                pass
        self.stops.clear()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)


def client():
    global _client
    with _client_lock:
        if _client is None:
            _client = Client()
    return _client


# --- registration ------------------------------------------------------------


def tool_name(server, tool):
    """mcp__<server>__<tool>, made of the characters a function name may hold.

    The API accepts ^[a-zA-Z0-9_-]{1,64}$; a server name with a space or a
    tool name with a dot would fail every request of the session.
    """
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", f"mcp__{server}__{tool}")
    return name[:64]


def describe(error):
    """The first concrete message inside an error, or an error group."""
    while isinstance(error, BaseExceptionGroup) and error.exceptions:
        error = error.exceptions[0]
    lines = str(error).strip().splitlines()
    return f"{type(error).__name__}: {lines[0]}" if lines else type(error).__name__


def call_tool(server, tool, args):
    """Run one MCP tool and flatten its reply to a string.

    Text parts are joined with newlines; other parts are named by type. A
    result the server marks as an error, or a failure to reach the server at
    all, comes back as a string starting with Error:.
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
    return history.cap(text)


def register(server, tools):
    """Add each tool to TOOLS and TOOL_SCHEMAS as mcp__<server>__<tool>."""
    from . import tools as registry  # here, not at the top: tools is imported first and imports this module

    names = []
    for tool in tools:
        name = tool_name(server, tool.name)
        if name in registry.TOOLS:  # two tools that sanitise to the same name
            name = f"{name[:60]}_{len(names) + 1}"

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
