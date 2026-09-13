# Step 26 - MCP client

**What this step adds:** the harness can start Model Context Protocol
servers and use their tools. `harness/mcp_client.py` reads a config file,
starts each server as a child process over stdio, asks it for its tools,
and registers them as `mcp__<server>__<tool>`. The model calls them like
any other tool. A `/mcp` command lists the servers, and an `MCP_ALLOW`
list decides which tools may run without asking. A tiny echo server ships
in `.agents/`, so the harness shows real MCP tools out of the box.

## Why MCP

Every tool so far is a Python function in this package. Adding one means
editing `tools.py`. MCP turns that around: a tool lives in its own process,
written in any language, and tells the client what it offers. The client
needs to know one protocol, not one function per tool. A file server, a
database server or a browser server plugs in through the same config file.

The harness stays the same size. The registry gains a way to grow at run
time, and the permission layer gains one rule. Nothing in the turn loop
changes: an MCP tool is a name in `TOOLS` with a schema in `TOOL_SCHEMAS`,
exactly like `read_file`.

## The code, piece by piece

### 1. The config file

`harness/mcp_client.py`:

```python
CONFIG_PATHS = [
    Path.home() / ".simple-harness" / "mcp.json",  # every project
    Path.cwd() / ".agents" / "mcp.json",           # this project; wins on a clash
]
...
def load_config(paths=None):
    ...
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
```

The shape is `{"servers": {"name": {"command": ..., "args": [...], "env":
{...}}}}`, stdio only. Two files are read: one in the home directory for
every project, one in `.agents/` for this project. The project file wins
when both name the same server. Two small rewrites make the shipped
server start anywhere. The command `python` becomes the interpreter that
runs the harness, because on Windows `python` on the PATH is often a
Store alias that opens nothing. A relative argument that names an
existing file becomes an absolute path, so the child process finds it
whatever its own working directory is.

### 2. One loop, one thread, one task per server

`harness/mcp_client.py`:

```python
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
```

The `mcp` package is asyncio-only. The harness is synchronous, and step
22 runs the tool calls of one reply from a thread pool. The browser in
step 23 solved the same shape with one worker thread that owns every
Playwright object. This module does the same with an asyncio loop: one
background thread runs the loop, and `submit` sends a coroutine there and
blocks until it returns. A tool call from any pool thread takes that
path.

Each server gets one task on the loop. That task opens the transport and
the session, reports the tool list through a future, then waits on an
event. The contexts the `mcp` package opens must be closed by the task
that opened them, so `close` sets the event and the same task unwinds.
`start` wraps the wait in a timeout and cancels the task when a process
starts but never speaks the protocol. `mcp` is imported inside the
function: the harness and its tests import without it.

### 3. Registration and the wrapper

`harness/mcp_client.py`:

```python
def call_tool(server, tool, args):
    ...
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
```

A server's tool list comes back as objects with a name, a description and
a JSON schema for the arguments. That schema goes into `TOOL_SCHEMAS` as
`parameters`, unchanged: the model sees exactly what the server wrote.
The wrapper takes keyword arguments, because `tools.run` unpacks the
parsed JSON with `**args`, and hands them to the server as the arguments
dict. The result is a list of content parts. Text parts are joined with
newlines, other parts are named by type, and a result the server flags
as an error becomes an `Error:` string, like a failed browser click. The
text passes through `history.cap`, so a chatty server spills to a temp
file like a chatty command.

### 4. Starting every server

`harness/mcp_client.py`:

```python
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
```

A missing binary, a crash on start or a process that never answers all
end up here as an exception. The server is noted and skipped. `SERVERS`
keeps the outcome for `/mcp`. The `mcp` package wraps failures in
exception groups; `describe` walks down to the first concrete message so
the note reads `FileNotFoundError: ...` rather than `unhandled errors in
a TaskGroup`.

`harness/agent.py`:

```python
    if cli.print:
        ui.headless()
    else:
        ui.banner(sandbox.name())
    mcp_client.connect_all()  # external tools join the registry before the first turn
```

The servers start after the banner and before the first turn, in both
the interactive and the `-p` mode. `main` calls `mcp_client.close_all()`
on the way out, next to `browser_close`, so no child process outlives the
session.

### 5. MCP tools ask

`harness/permissions.py`:

```python
# MCP tools that run without asking, as globs on the full name, e.g. MCP_ALLOW=mcp__echo__*,mcp__fs__read_*
MCP_ALLOW = [pattern.strip() for pattern in os.environ.get("MCP_ALLOW", "").split(",") if pattern.strip()]
...
    if name.startswith("mcp__"):
        if any(fnmatch(name, pattern) for pattern in MCP_ALLOW):
            return "allow", None
        return "ask", f"call MCP tool {name} with {json.dumps(args)[:200]}"
```

An MCP tool is code the harness has never seen. The default is to ask,
with the tool name and its arguments in the prompt. `MCP_ALLOW` is a
comma list of globs on the full name, so `mcp__fs__*` trusts one whole
server and `mcp__fs__read_*` trusts only its read tools. Every other rule
in `check` is untouched.

### 6. The `/mcp` command

`harness/commands.py`:

```python
def mcp(messages):
    """One line per configured server: name, status, and its tool names."""
    if not mcp_client.SERVERS:
        ui.note("no MCP servers configured (see .agents/mcp.json)")
        return messages
    rows = []
    for name, info in mcp_client.SERVERS.items():
        tools = ", ".join(info["tools"]) or "-"
        rows.append(f"{name:<12} {info['status']:<12} {tools}")
    ui.note("\n".join(rows))
    return messages
```

One line per server: its name, `connected` or `failed: ...`, and the
tools it added. A failed server shows why without a restart.

### 7. The shipped server

`.agents/mcp_echo_server.py`:

```python
from mcp.server.fastmcp import FastMCP

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
```

`FastMCP` turns the type hints into the JSON schema and the docstring into
the description, and `run()` serves over stdio. `.agents/mcp.json` points
at this file with the command `python`, which `load_config` rewrites to
the running interpreter. The log level is turned down: the server's
stderr shares the terminal with the harness UI.

## Run it

Install the optional dependency and start the harness from this
directory, so it finds `.agents/mcp.json`:

```bash
pip install -e ".[mcp]"
harness
> /mcp
```

The listing shows `echo  connected  mcp__echo__echo, mcp__echo__add`.
Now ask for a tool call:

```bash
> use the echo server to add 40 and 2
```

The model calls `mcp__echo__add`. The prompt `call MCP tool
mcp__echo__add with {"a": 40, "b": 2}` appears; answer `y`. The tool
panel shows `42.0`, and the model answers from it. Set
`MCP_ALLOW=mcp__echo__*` to skip the prompt.

Add a server of your own to `~/.simple-harness/mcp.json`:

```json
{"servers": {"fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]}}}
```

Restart, and `/mcp` lists its tools as `mcp__fs__...`. Break the command
on purpose and the banner is followed by a note that the server failed
and was skipped; the session goes on without it.

Run the tests from the repository root. Ten of them run offline; the
ones that call a tool go through a fake session object and never start a
process. The last one starts the echo server for real and is skipped
when `mcp` is not installed:

```bash
python run_tests.py 26
```

## What to notice

- The turn loop, the thread pool and `execute_all` did not change. An MCP
  tool is a name in `TOOLS` and a schema in `TOOL_SCHEMAS`, added at run
  time instead of import time. The subagent from step 15 is offered them
  too, because `toolset()` reads the same list.
- Same shape as the browser: one thread owns the objects that cannot
  cross threads, and `submit` is the door. The browser thread runs a
  pool; this one runs an asyncio loop.
- One task per server, because anyio cancel scopes must be entered and
  exited by the same task. A first version that opened the contexts in
  one task and closed them in another failed on shutdown.
- The server's schema goes to the model verbatim. A server that writes a
  poor description gets poor calls; the harness does not paper over it.
- A failed server is a note, not a crash. The rest of the session works
  without it, and `/mcp` shows the reason.
- The fake session in the tests is an object with an async `call_tool`.
  It runs on the real background loop, so the tests cover the
  thread-crossing path and only skip the child process.

## Diff from step 25

```bash
diff -r ../step_25_memory/harness harness
```

New: `harness/mcp_client.py` (config, the loop thread, registration),
`.agents/mcp.json` and `.agents/mcp_echo_server.py` (the shipped server).
Changed: `permissions.py` (`MCP_ALLOW`, the `mcp__` rule), `commands.py`
(`/mcp`), `agent.py` (`connect_all` before the first turn, `close_all`
on exit), `llm.py` (the system prompt names the MCP tools), `tools.py`
(docstring), `pyproject.toml` (optional dependency group `mcp`).
