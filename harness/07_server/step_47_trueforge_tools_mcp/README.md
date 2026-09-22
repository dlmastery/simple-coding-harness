# Step 47 - Tools and permissions as MCP

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Move the loop behind a service**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 46 - The loop on TrueForge](../step_46_trueforge_loop/README.md). Next: [Step 48 - Sandbox, skills and code mode](../step_48_trueforge_sandbox_skills/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** the codelab's five coding tools served to TrueForge
as a remote MCP server, and the permission rules of stage 11 expressed as
MCP annotations. `tools_server.py` is FastMCP over streamable HTTP on port
8931, rooted at one project directory. `register.py` tells TrueForge where
the server is and lists what TrueForge sees. `client/approve.py` streams a
turn, answers the approval pauses on the terminal, and resumes. `demo.py`
runs one coding task end to end.

This step is standalone. It needs the server from
[step 46](../step_46_trueforge_loop/README.md) (setup and the WSL note are
there) and no other step.

## Why tools become a server, and what breaks without a guard on the pause

In the hand-built harness the tools are Python functions in the same
process as the loop. TrueForge's loop runs in a server, so it cannot call a
function in your process. It calls MCP servers over HTTP instead. Step 26
made the harness an MCP *client*; this step makes the tools an MCP
*server*. The functions do not change. What changes is who calls them and
how the permission rules travel.

Stage 11 kept the rules in a table next to the loop: `read_file` allowed,
`write_file` asks, `rm` denied. TrueForge never sees that table. It sees
the MCP `tools/list` reply, and that reply carries **annotations**: each
tool says whether it is read-only or destructive. TrueForge's default
approval policy is `require_approval_for_tools: ["@write", "@destructive"]`,
resolved from those hints. So the rules move from the loop into the tool
definitions, and every client of the server inherits them.

A gated call ends the turn, and the client resumes it with the answer. That
is where a client goes wrong if it is careless: a turn can stream a
`tool.approval_required` event and *then* end in `error` (the model went
away, the iteration limit tripped). Answering that pause means prompting
the user for a call that will never run and POSTing an approval to a dead
turn. The loop here resumes only a turn that ended in `done`, caps the
number of rounds, and treats a closed stdin as a denial.

## Quick demo

```bash
python demo.py "add a docstring to hello.py"
```

```text
project: ~/AppData/Local/Temp/s47_xrcdij6m
registered s47-tools with 5 tools:
  read_file    runs                 destructiveHint=false, openWorldHint=false, readOnlyHint=true
  list_dir     runs                 destructiveHint=false, openWorldHint=false, readOnlyHint=true
  write_file   asks (@destructive)  destructiveHint=true, openWorldHint=false, readOnlyHint=false
  str_replace  asks (@destructive)  destructiveHint=true, openWorldHint=false, readOnlyHint=false
  bash         asks (@destructive)  destructiveHint=true, openWorldHint=false, readOnlyHint=false
session: 01m2g5ynegmjn2wh2vc1pe6zm1
> add a docstring to hello.py
  [tool.response] s47-tools:
  read_file, list_dir, write_file, str_replace, bash
  [tool.response] {"result":"def hello():\n    print(\"hello\")\n"}
  allow? str_replace {"path": "hello.py", "old_str": "def hello():", "new_str": "def hello():\n    \"\"\"Prints 'hello' to the console.\"\"\"", "allow_multi_edit": false} (y/n/a=always)> y
  [tool.response] {"result":"Replaced 1 match(es) in hello.py"}
I have added a docstring to the hello() function in hello.py that says: Prints 'hello' to the console.
[turn done] in=6648 out=115
hello.py now:
def hello():
    """Prints 'hello' to the console."""
    print("hello")
```

Three tool calls. The first is the `list_tools` meta tool of deferred
loading (its response is the server's tool names), the second is the
read-only `read_file`; both run on their own. The third is destructive,
so the turn stops, the terminal asks, and a second turn carries the
answer. Answer `n` instead and the model reads
`User denied tool call: The user denied this tool call.` as the tool
result, exactly like stage 11.

## Files

```text
step_47_trueforge_tools_mcp/
├── client/          the TrueForge connection and the approval loop
│   ├── __init__.py  package marker
│   ├── connect.py   one place that builds the client; truststore on Windows; the error line
│   └── approve.py   stream a turn, answer its approval pauses, resume; capped and status-aware
├── tools_server.py  the five coding tools as a FastMCP server on port 8931
├── register.py      registers the tools server with TrueForge and lists its tools
├── demo.py          one coding task end to end, with the approval prompt
├── test_step.py     offline tests: the MCP server in-process, a fake SSE server
└── README.md        this file
```

## The code, piece by piece

### 1. Five tools, two annotation sets

`tools_server.py`:

```python
# TrueForge resolves `@read-only`, `@write` and `@destructive` from these hints.
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)
```

```python
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
```

| Tool          | `readOnlyHint` | `destructiveHint` | Default policy | Stage 11 rule            |
| ------------- | -------------- | ----------------- | -------------- | ------------------------ |
| `read_file`   | true           | false             | runs           | `allow`                  |
| `list_dir`    | true           | false             | runs           | `ls*` is `allow`         |
| `write_file`  | false          | true              | asks           | asks outside the project |
| `str_replace` | false          | true              | asks           | asks outside the project |
| `bash`        | false          | true              | asks           | `"*": "ask"`             |

`destructiveHint` defaults to true in the MCP specification when a tool says
nothing. The readers set it to false on purpose, so a client that only
reads that hint still lets them run. There is no `deny` tier in MCP
annotations. Stage 11's `rm *` and `sudo *` rules have no equivalent here;
the sandbox of step 48 is the answer to those.

### 2. Every path is rooted at the project

`tools_server.py`:

```python
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
```

Stage 11 asked when a path left the project. Here the server refuses it,
and the refusal is a tool result, so the model reads `Error: ../x is
outside the project` and adapts. Results are strings and errors are
results, as in stage 5. `str_replace` refuses an empty `old_str` the same
way.

`bash` is stage 2.1's subprocess with the same three guards every `bash`
in this codelab carries: no stdin, UTF-8 decoding, and a process group so a
timeout kills the whole tree, not just the shell:

```python
def bash(command: str) -> str:
    """Run a shell command in the project directory and return its combined stdout and stderr.

    `shell=True` is the OS shell: /bin/sh on Linux and macOS, cmd.exe on
    Windows, where single quotes are not quotes. Step 50 resolves a real bash.
    """
    proc = subprocess.Popen(
        command, shell=True, cwd=PROJECT,
        stdin=subprocess.DEVNULL,  # no stdin: an interactive command ends, it does not wait
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",  # never a UnicodeDecodeError on odd output
        env=BASH_ENV, **NEW_GROUP,
    )
    try:
        out, err = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        out, err = proc.communicate()  # what it printed before the kill
        return f"Timed out after {TIMEOUT}s and was killed. Output so far:\n{out + err}"
    return (out + err) or "(no output)"
```

### 3. Registering the server

`register.py`:

```python
def register(client, url: str = TOOLS_URL) -> dict:
    """Create or replace the `s47-tools` entry. Returns the saved manifest as a dict."""
    manifest = RemoteMcpServerManifest(name=SERVER_NAME, url=url, description=DESCRIPTION)
    saved = client.settings.mcp_servers.create_or_update(manifest=manifest)
    return saved.data.manifest.model_dump(exclude_none=True)


def list_tools(client) -> list:
    """The tools TrueForge sees on the server, each with its annotations."""
    return client.mcp_servers.list_tools(name=SERVER_NAME).data
```

`create_or_update` is `PUT /api/v1/settings/mcp-servers` with
`{"manifest": {"type": "remote", "name": "s47-tools", "url": ..., "description": ...}}`.
The manifest has no `auth` key because the tools server needs none.
`list_tools` is `GET /api/v1/mcp-servers/s47-tools/tools`; TrueForge
connects to the server, runs MCP `tools/list`, and passes the entries
through verbatim, annotations included. That is the table in the demo.

The URL says `localhost`, and the tools server binds `127.0.0.1`. On this
machine TrueForge runs inside WSL with mirrored networking, so `localhost`
in WSL reaches a Windows service on the same port.

### 4. The agent spec: attached, deferred, default policy

`client/approve.py`:

```python
PRELOAD_TOOLS = ["read_file", "str_replace"]
```

```python
    if preload_tools is None:
        preload_tools = PRELOAD_TOOLS
    tools = McpServer(name=TOOLS_SERVER, preload=False, preload_tools=preload_tools)
    spec = AgentSpec(
        model=Model(name=model),
        instructions=instructions,
        mcp_servers=[tools],
        config=RuntimeConfig(
            iteration_limit=iteration_limit,
            # both default to on; this client handles neither questions nor subagent threads
            ask_user_questions=AskUserQuestionsConfig(enabled=False),
            dynamic_sub_agents=DynamicSubAgentsConfig(enabled=False),
        ),
    )
    return SessionAgentSpecBody(spec=spec)
```

`require_approval_for_tools` is not set, so the default `["@write",
"@destructive"]` applies. `preload: false` is step 32's deferred tools: the
model starts with the server's name and description only, and discovers
tool schemas through the meta tools `list_tools`, `get_tool_info`,
`get_tool_output_schema` and `call_tool`. The first `[tool.response]` in
the demo is `list_tools`.

`preload_tools` is the selective form: the two tools every coding turn
uses are loaded upfront, the other three stay deferred. Fully deferred,
`gpt-4.1-mini` looped on `list_tools` or invented tool names in two of
three runs on this machine; the preloaded pair fixed that. Step 32 deferred
by schema size (over 300 tokens); TrueForge defers by server and lets you
name exceptions. `iteration_limit` is step 34's `MAX_CALLS`, set low here
so a confused model stops after twelve calls.

Two server features are switched off on purpose. `ask_user_questions` and
`dynamic_sub_agents` are on by default in every TrueForge agent; this
client has no code for a `tool.response_required` pause or for a second
thread's deltas, so a question would end the turn with an empty reply and
a subagent would print unlabelled text. Step 49 handles questions and step
50 handles threads; here both are off so the spec promises only what the
client can do.

### 5. Merging deltas, so the prompt can show the arguments

`client/approve.py`:

```python
def merge_delta(message: dict, delta) -> None:
    """Fold one `model.message.delta` into its base message: append text, merge tool calls by index."""
    if delta.content:
        message["content"] = (message.get("content") or "") + delta.content
    for piece in delta.tool_calls or []:
        calls = message.setdefault("tool_calls", [])
        while len(calls) <= piece.index:
            calls.append({"id": None, "name": "", "arguments": ""})
        call = calls[piece.index]
        call["id"] = piece.id or call["id"]
        if piece.function:
            call["name"] += piece.function.name or ""
            call["arguments"] += piece.function.arguments or ""
```

On a live stream the `model.message` arrives empty and fills in through
`model.message.delta` events that share its id. This is step 21's
accumulator: text appends, tool calls merge by `index`. The approval event
points at the message by id, so the loop keeps every message in a dict
and merges as it goes.

### 6. The approval loop

`client/approve.py`:

```python
@dataclass
class TurnResult:
    """What one streamed turn produced."""

    text: str = ""
    pending: list = field(default_factory=list)
    metrics: dict | None = None
    status: str = "incomplete"  # only turn.done sets it; a dropped stream stays incomplete
```

```python
def approvals_for(pending: list, events: dict, approver: Approver) -> list:
    """Turn the pending approval events into `user.tool_approval` inputs, one decision per call."""
    inputs = []
    for event in pending:
        for ref in event.tool_calls:
            message = events.get(ref.source_event_id, {})
            call = next((c for c in message.get("tool_calls", []) if c["id"] == ref.id), None)
            label = describe_call(call) if call else ref.id
            inputs.append(
                UserToolApprovalEvent(thread_id=event.thread_id, tool_call_id=ref.id, approval=approver.decide(label))
            )
    return inputs
```

```python
    inputs = [UserMessage(content=prompt)]
    for _round in range(MAX_ROUNDS):
        result = run_turn(client, session_id, inputs, events, out)
        for key, value in (result.metrics or {}).items():
            totals[key] = totals.get(key, 0) + value
        if result.status != "done" or not result.pending:
            result.metrics = totals or None
            return result
        inputs = approvals_for(result.pending, events, approver)
    result.status = "approval-loop"  # MAX_ROUNDS pauses in one chat: something keeps re-asking
    result.metrics = totals or None
    return result
```

A gated call ends the turn: `tool.approval_required` names the call id and
the `source_event_id` of the message that made it, then `turn.done` arrives
with `output: null`. The loop looks the call up, asks, and starts a **new
turn** whose input is one `user.tool_approval` per call, `{"status":
"allow"}` or `{"status": "deny", "reason": ...}`. A turn's input cannot mix
a user message with approvals, which is why the resume carries no text.

Three guards keep the loop honest. `status` starts as `"incomplete"` and
only `turn.done` changes it, so a connection that drops mid-turn is not
reported as `done`. A pause is answered only when the turn ended in
`done`: an `error` or `cancelled` turn that streamed an approval event is
returned as such, without a prompt and without a resume POST. And
`MAX_ROUNDS = 20` bounds the number of resume turns one `chat()` may run,
so a server that re-pauses on every resume cannot keep an `always`
approver busy forever; the result then says `approval-loop`.

`Approver` answers `y`, `n` or `a`; `a` remembers the tool name for the
session, step 35's "always". A closed stdin or ctrl-c at the prompt is a
denial, never an allow:

```python
        while True:
            try:
                answer = self.ask(f"  allow? {label} (y/n/a=always)> ").strip().lower()
            except (EOFError, KeyboardInterrupt):  # stdin closed or ctrl-c: never allow by accident
                print()
                return ApprovalDeny(reason="The user gave no answer.")
```

`describe_call` unwraps the meta tool: when the model calls
`call_tool(mcp_server="s47-tools", tool_name="bash", input={...})`, the
prompt shows `bash {...}`, not `call_tool`. The recorded demo paused on the
preloaded `str_replace`, so the `call_tool` shape (`tool_name`, `input`) is
taken from the docs and covered by a unit test, not by a recording.

### 7. The demo's exit code

`demo.py`:

```python
        result = approve.chat(client, session.data.id, args.prompt, approve.Approver(ask))
        m = result.metrics or {}
        print(f"[turn {result.status}] in={m.get('total_input_tokens')} out={m.get('total_output_tokens')}")
        if temporary:
            print("hello.py now:")
            print((project / "hello.py").read_text(encoding="utf-8").rstrip())
        return 0 if result.status == "done" else 1
    except REQUEST_ERRORS as error:  # server down or a refused request: one line, exit 1
        print(f"request failed: {describe_error(error, args.base_url)}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.terminate()
        if temporary:
            shutil.rmtree(project, ignore_errors=True)
```

`REQUEST_ERRORS` and `describe_error` live in `client/connect.py` next to
the client constructor: `httpx.HTTPError` for a server that cannot be
reached, `ApiError` for one that answered with an error status. The tools
server child process is started inside the `try`, so a failure to come up
still terminates it and removes the temp project.

## Run it

Prerequisites: the TrueForge server of step 46 (in WSL on Windows) with
the model registered; `pip install mcp uvicorn` for the tools server
(the root `requirements.txt` lists both). From this directory:

bash:

```bash
python demo.py "add a docstring to hello.py"
```

PowerShell:

```powershell
python demo.py "add a docstring to hello.py"
```

Expected output: the Quick demo above. Type `y` at the prompt. Pass
`--project DIR` to work on a directory of your own; it is kept afterwards.
The exit code is 0 when the turn ended in `done`, 1 otherwise.

The pieces also run on their own:

```bash
python tools_server.py --project . --port 8931     # serve the tools for this directory
python register.py                                 # register s47-tools and print the tool table
```

The API has no delete for MCP server settings, so `s47-tools` stays
registered after the demo. Registering again replaces it in place.

Tests are offline: the tools server runs in-process over an in-memory MCP
transport, and the approval loop talks to a fake TrueForge in a thread
that answers with hand-written SSE, including a turn that errors after
its approval event, a cut stream, a server that re-pauses forever, and a
closed stdin at the prompt.

```bash
python -m pytest -q test_step.py
```

## Error handling

- **Server down or a refused request.** `request failed: http://localhost:8790 is not answering (ConnectError: ...)`
  on stderr, exit 1; the tools server child is terminated and the temp
  project removed.
- **A turn that ends in `error` or `cancelled`.** `[turn error] in=... out=...`
  is printed and the exit code is 1. If an approval event arrived before
  the error, it is not answered.
- **A dropped stream.** `[turn incomplete] in=None out=None`, exit 1. The
  turn may still be running on the server.
- **A tool that fails.** Every tool returns `Error: ...` as its result;
  `bash` returns `Timed out after 60s and was killed. Output so far:` plus
  the partial output after killing the command's process group. The
  model reads the string and adapts; nothing raises on the server side.
- **ctrl-c or ctrl-d (ctrl-z then enter on Windows) at the `allow?`
  prompt.** The call is denied with the reason `The user gave no answer.`
  and the turn resumes. ctrl-c while a turn streams ends the demo with a
  `KeyboardInterrupt`; the turn keeps running on the server.
- **The server keeps asking.** After `MAX_ROUNDS` (20) resume turns the
  result is `[turn approval-loop]`, exit 1.

## Gotchas / what this is not

- The tool named `bash` runs the OS shell: `/bin/sh` on Linux and macOS,
  **cmd.exe on Windows**, where single quotes are not quotes and `rg
  'pattern'` fails. Step 50 resolves a real bash for its eval; this step
  keeps stage 2.1's `shell=True` so its diff stays about annotations.
- The tools run on *this* machine, in the process started by `demo.py`.
  TrueForge (in WSL) reaches them over `localhost:8931`, which mirrored
  networking makes work; a hosted TrueForge could not reach a laptop.
- There is no `deny` tier: annotations say read-only or destructive, and
  the policy says run or ask. `rm -rf` asks like any other write.
- The remembered `a` (always) lives in the `Approver` object, so it lasts
  one `demo.py` run, not the session on the server.
- Questions and subagents are switched off in the spec; a prompt that
  needs either gets a plain answer or a refusal.

## What to notice

- **The policy lives with the tool.** Stage 11's table sat next to the
  loop. Here `readOnlyHint` and `destructiveHint` ride along with the tool
  definition, and any MCP client can read them. TrueForge's default policy
  gates the same three tools stage 11 gated.
- **An approval is a turn boundary.** In the hand-built loop the prompt
  blocked inside the tool dispatch. In TrueForge the turn ends, the client
  answers whenever it likes, and a new turn resumes. The session, not the
  process, holds the paused state. Step 34's durability comes for free,
  and so does the new failure mode: a pause and an error can arrive in
  the same turn, and only a `done` turn is worth resuming.
- **Modes map to two fields.** Step 39's `auto` mode is
  `require_approval_for_tools: []`; `read-only` is `enable_tools:
  ["@read-only"]`; `default` is the default. Step 39 rewrote verdicts in
  the client; TrueForge filters the tool list and the approval list on the
  server, per MCP server.
- **Deferred loading is a server setting.** `preload: false` costs a
  `list_tools` round trip on the first call and saves the schemas on every
  call after. `preload_tools` names the exceptions. Step 32 made the same
  trade by schema size.
- **Denials are results.** `n` sends `deny` with a reason; the model reads
  it as the tool's output and explains itself, as it did with `Blocked by
  policy` in stage 11.

## Capability table

| Capability          | This codelab                                                      | TrueForge                                                                                                  |
| ------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Tools               | Stage 2 to 5: Python functions and `TOOL_SCHEMAS` in `tools.py`  | An MCP server registered under `PUT /api/v1/settings/mcp-servers`, attached by name in `mcp_servers`      |
| Permissions         | Stage 11: `BASH_RULES` and `check()` in `permissions.py`         | Tool annotations (`readOnlyHint`, `destructiveHint`) plus `require_approval_for_tools` per MCP server      |
| Approval prompt     | Stage 11 `ui.approve`, step 35 `y/n/a/never`                     | `tool.approval_required` event, resumed with a `user.tool_approval` input on a new turn                    |
| Approval modes      | Step 39: `auto`, `read-only`, `default` rewrite verdicts          | `require_approval_for_tools: []` (auto), `enable_tools: ["@read-only"]` (read-only), default (default)     |
| Deferred tools      | Step 32: schemas over 300 tokens become stubs until `load_tool`   | `preload: false` per server with `list_tools` / `get_tool_info` / `call_tool`; `preload_tools` exceptions |
| Path fence          | Stage 11: edits outside the project ask                           | The tools server refuses paths outside `--project`; the refusal is the tool result                         |
| Call budget         | Step 34 `MAX_CALLS`, step 41 stop conditions                      | `config.iteration_limit`; `MAX_ROUNDS` on the client side for approval rounds                              |

## What the next step adds

Step 48 turns on TrueForge's sandbox: the model gets a shell and a file
system on the server, a `sandbox.created` event says when, and the client
downloads what the agent produced. It also registers the stage 4 skill
from a git URL.
