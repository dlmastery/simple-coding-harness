# Step 26 - MCP client

**What this step adds:** the harness can start Model Context Protocol
servers and use their tools. `harness/mcp_client.py` reads a config file,
starts each server as a child process over stdio, asks it for its tools,
and registers them as `mcp__<server>__<tool>`. The model calls them like
any other tool. A `/mcp` command lists the servers, and an `MCP_ALLOW`
list decides which tools may run without asking. A tiny echo server ships
in `.agents/`, so the harness shows real MCP tools out of the box.

## Why MCP, and what breaks without it

Every tool so far is a Python function in this package. Adding one means
editing `tools.py`. MCP turns that around: a tool lives in its own process,
written in any language, and tells the client what it offers. The client
needs to know one protocol, not one function per tool. A file server, a
database server or a browser server plugs in through the same config file.

Without it, the harness can only ever do what this package does. Say you
want the agent to read GitHub issues. The step 25 harness has no such
tool, so the model falls back to `bash` and `curl`, which the rules rate
`ask`, and you approve a token-bearing command every turn. With this step
you add four lines to `mcp.json`, the GitHub server's tools appear as
`mcp__github__*`, and `MCP_ALLOW=mcp__github__get_*` lets the read-only
ones through without a prompt.

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
```

The shape is `{"servers": {"name": {"command": ..., "args": [...], "env":
{...}}}}`, stdio only. The table may also be called `mcpServers`, the key
Claude Desktop and Cursor use, so a file copied from one of them works
as it is. Two files are read: one in the home directory for every
project, one in `.agents/` for this project. The project file wins when
both name the same server. A file that is not valid JSON is noted and
skipped, and the session starts without it; a typo in `mcp.json` must
not lock you out of the harness.

Two small rewrites make the shipped server start anywhere. The command
`python` becomes the interpreter that runs the harness, because on
Windows `python` on the PATH is often a Store alias that opens nothing.
A relative argument that names an existing file becomes an absolute
path, so the child process finds it whatever its own working directory
is.

`env` is exactly what the server gets on top of a minimal environment;
see section 2. A value like `"${GITHUB_TOKEN}"` is filled in from the
harness's own environment, which is how you hand one variable to one
server without handing it everything.

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
```

The `mcp` package is asyncio-only. The harness is synchronous, and step
22 runs the tool calls of one reply from a thread pool. The browser in
step 23 solved the same shape with one worker thread that owns every
Playwright object. This module does the same with an asyncio loop: one
background thread runs the loop, and `submit` sends a coroutine there and
blocks until it returns. A tool call from any pool thread takes that
path. A call that takes longer than `CALL_TIMEOUT` (120s) is cancelled
on the loop as well as abandoned by the caller, so a hung server does
not also stall the next call to it.

Each server gets one task on the loop. That task opens the transport and
the session, reports the tool list through a future, then waits on an
event. The contexts the `mcp` package opens must be closed by the task
that opened them, so `close` sets the event and the same task unwinds.
`start` wraps the wait in a timeout and cancels the task when a process
starts but never speaks the protocol; `stop` waits `STOP_TIMEOUT` (10s)
for the task to unwind and cancels it when the server ignores its closed
stdin, so the child process is terminated rather than orphaned. `mcp` is
imported inside the function: the harness and its tests import without
it.

The environment is the part to read twice. The `mcp` package starts a
server with a *minimal* environment (`get_default_environment()`: `PATH`,
`HOME`, `USER` and a few more), not the harness's. This module keeps it
that way and adds only the `env` entries from the config, so a server
never sees `API_KEY` by accident. The flip side: a server that needs
`GITHUB_TOKEN` from your shell does not get it until `mcp.json` names it,
as `"env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}`.

### 3. Registration and the wrapper

`harness/mcp_client.py`:

```python
def tool_name(server, tool):
    """mcp__<server>__<tool>, made of the characters a function name may hold.

    The API accepts ^[a-zA-Z0-9_-]{1,64}$; a server name with a space or a
    tool name with a dot would fail every request of the session.
    """
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", f"mcp__{server}__{tool}")
    return name[:64]
...
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
```

A server's tool list comes back as objects with a name, a description and
a JSON schema for the arguments. That schema goes into `TOOL_SCHEMAS` as
`parameters`, unchanged: the model sees exactly what the server wrote.
The name is not passed through unchanged. Chat-completions function names
must match `^[a-zA-Z0-9_-]{1,64}$`, MCP tool names may be longer and hold
dots, and a server name is free text from `mcp.json`. One bad name would
make every request of the session fail with a 400, so `tool_name` swaps
the other characters for `_`, cuts at 64, and `register` numbers a clash.
The wrapper closes over the server's real tool name, so the server still
receives the name it published.

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
the description, and `run()` serves over stdio. The file imports it from
`mcp.server.fastmcp` and falls back to `mcp.server.mcpserver.MCPServer`,
the name `mcp` 2.x gave the same class, so it runs under either major
version. `.agents/mcp.json` points at this file with the command
`python`, which `load_config` rewrites to the running interpreter. The
log level is turned down: the server's stderr shares the terminal with
the harness UI.

## Run it

You need Python 3.11+, an `API_KEY` (and `BASE_URL`/`MODEL` if not
OpenRouter) in the environment or in `~/.simple-harness/env`, and the
optional `mcp` dependency group. Start the harness from this directory,
so it finds `.agents/mcp.json`.

bash:

```bash
cd step_26_mcp_client
pip install -e ".[mcp]"
MCP_ALLOW="mcp__echo__*" harness
```

PowerShell:

```powershell
cd step_26_mcp_client
pip install -e ".[mcp]"
$env:MCP_ALLOW = "mcp__echo__*"
harness
```

Leave `MCP_ALLOW` unset to see the prompt instead.

### Expected output

```text
────────────────────────── coding agent ──────────────────────────
  sandbox: none  ·  /sessions  /rewind  ·  alt-enter for a newline  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> /mcp

  echo         connected    mcp__echo__echo, mcp__echo__add

> use the echo server to add 40 and 2

  ╭──────────────────────────────────────────────────────╮
  │ mcp__echo__add {"a": 40, "b": 2}                     │
  │ ──────────────────────────────────────────────────── │
  │ 42.0                                                 │
  ╰──────────────────────────────────────────────────────╯

  The echo server says 40 + 2 = 42.

  1,812 prompt · 41 completion
```

Without `MCP_ALLOW` the panel is preceded by `call MCP tool
mcp__echo__add with {"a": 40, "b": 2}` and an `allow? (y/n)>` prompt;
answer `y`.

Add a server of your own to `~/.simple-harness/mcp.json`:

```json
{"servers": {"fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]}}}
```

Restart, and `/mcp` lists its tools as `mcp__fs__...`. Break the command
on purpose and the banner is followed by `mcp server 'fs' failed to start
(FileNotFoundError: ...); skipped`; the session goes on without it, and
`/mcp` shows the `failed:` line.

Run the tests from the repository root. All but one run offline; the
ones that call a tool go through a fake session object and never start a
process. `test_live_echo_server_over_stdio` starts the echo server for
real and is skipped when `mcp` is not installed:

```bash
python run_tests.py 26
```

## Error handling

Every failure in this step ends as text the model can read, never as a
traceback:

- **A tool call with broken arguments** (`{"a": 40, ` cut off by the
  stream, or `[1, 2]`): `Error: the arguments of mcp__echo__add are not a
  JSON object: ...` is the tool result, the call never runs, and the model
  retries.
- **A tool name the registry lacks** (the model invents `mcp__echo__mul`):
  `Error: no tool named 'mcp__echo__mul'.`
- **A tool that raises** (wrong argument types, a missing file):
  `Error: TypeError: ...` or `Error: FileNotFoundError: ...`.
- **A server that says no** (`isError`, e.g. `add(a="x")`): `Error: Error
  executing tool add: ...`, the server's own message.
- **A server that hangs**: `Error: TimeoutError: no answer within 120s`
  after `CALL_TIMEOUT`; the call is cancelled on the loop too.
- **A server that dies mid-session**: `Error: RuntimeError: MCP server echo
  is not connected` on every later call; `/mcp` still shows why it
  failed if it failed on start.
- **A failing shell command**: its stdout and stderr, exit code and all,
  as the result; a command past 60s is killed with its whole process tree
  and returns `Timed out after 60s and was killed. Output so far: ...`.
- **A model call that fails** (network, 5xx, an empty reply): the note
  `model call failed: ...`, and the turn ends. Your message stays in the
  transcript, so `continue` or a rephrase picks up where it stopped.
- **ctrl-c during a turn**: the tool calls that had not finished get the
  result `(interrupted before this tool ran)`, the note `interrupted`
  appears, and the prompt comes back. The transcript stays valid.
- **A turn that does not end** (the model keeps calling tools): after 40
  model calls the harness stops it with `stopped after 40 model calls in
  one turn; say 'continue' to go on`.
- **A transcript that ends on an unanswered tool call** (the process was
  killed between the call and its result): `--resume` and `/sessions`
  give each such call the result `(the harness stopped before this tool
  ran; no result was recorded)`, so the next model call is accepted.

To leave: `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or
ctrl-c at the prompt. An empty line is ignored. The MCP servers are
stopped on the way out, after the browser and before the summary.

## Gotchas / What this is not

- **Servers do not inherit your shell.** A server sees the `mcp`
  package's minimal environment plus the `env` entries in its config.
  List every variable it needs, with `"${VAR}"` to copy yours. This is
  deliberate: it keeps `API_KEY` out of third-party processes.
- **Tool names are rewritten.** `mcp__<server>__<tool>` is squeezed into
  `[A-Za-z0-9_-]` and 64 characters; `/mcp` shows the names the model
  sees. A server named `my server` becomes `my_server`.
- **Images and resources are placeholders.** An `ImageContent` part
  becomes the text `[image part]`, an `EmbeddedResource` becomes
  `[resource part]`. The `[[image:PATH]]` channel from step 24 is not
  wired to MCP results here.
- **Subagents get MCP tools too.** `task` offers every non-withheld tool,
  MCP tools included, and each call that is not in `MCP_ALLOW` prompts
  you from the subagent's thread. With a subagent that explores through
  an MCP server, set `MCP_ALLOW` for its read tools first.
- **stdio only.** No HTTP/SSE transport; a remote server needs a local
  stdio bridge.
- **Start-up is serial.** Servers connect one after another, each with a
  `CONNECT_TIMEOUT` of 30s; three slow servers can mean a slow banner.
- **Shutdown order:** `browser_close`, then `close_all` (each server's
  task is asked to end and cancelled after 10s if it will not), then the
  usage summary.
- **`-p` mode with piped stdin never prompts.** Every `ask` verdict is
  denied with a note on stderr, so an un-allow-listed MCP tool in a script
  needs `MCP_ALLOW`. `-p` exits 1 when the reply is empty. `-p` writes a
  session file like a chat does, and ignores `--resume`.
- **Windows:** the tool called `bash` runs `cmd.exe` (there is no OS
  sandbox and the banner says `sandbox: none`); `python` in `mcp.json` is
  rewritten to the running interpreter because the Store alias would
  open nothing; the config paths use `Path.home()`, i.e.
  `C:\Users\you\.simple-harness\mcp.json`.

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

## Files

```text
step_26_mcp_client/
├── harness/
│   ├── llm.py                        the model call; the system prompt names the MCP tools
│   ├── tools.py                      the registry, grown at run time by mcp_client.register()
│   ├── agent.py                      the loop; starts the MCP servers first, stops them last
│   ├── mcp_client.py                 MCP client: starts each server over stdio, registers its tools
│   ├── permissions.py                allow / ask / deny per tool call, MCP tools included
│   ├── commands.py                   slash commands; /mcp lists servers, status and tools
│   ├── context.py                    the late injection block, with the memory index
│   ├── memory.py                     persistent memory: markdown files with front matter
│   ├── compact.py                    the compaction agent; its handoff note is kept
│   ├── history.py                    transcript trimming: cap, strip, fit, image messages
│   ├── subagent.py                   the subagent loop shared by task and browse
│   ├── browse.py                     the browser subagent
│   ├── browser.py                    browser tools: one Chromium page through Playwright
│   ├── computer.py                   computer use: screen size, screenshot, act
│   ├── todos.py                      the plan: write_todos and the todo list
│   ├── skills.py                     skills: SKILL.md discovery and index
│   ├── session.py                    append-only JSONL log, load() with repair, /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash, and the process-group plumbing
│   ├── config.py                     settings: environment first, ~/.simple-harness/env fills gaps
│   ├── prompt.py                     the input line, through prompt_toolkit
│   ├── ui.py                         rich panels; streams the reply, headless() sends panels to stderr
│   └── __init__.py                   package marker
├── .agents/
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.26.0
└── README.md                         this file
```

## What the next step adds

Step 27 adds hooks: user-written commands and Python functions that run
at fixed points of the loop (before and after a tool call, on a prompt,
before compaction, at session start and end) and can block, replace or
annotate what happens there.

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
