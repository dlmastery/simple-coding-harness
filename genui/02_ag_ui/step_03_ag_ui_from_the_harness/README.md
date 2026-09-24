# Step 03 - The harness codelab's loop over AG-UI

<!-- genui-orientation -->
**Lesson 7 of 23.** [Course](../../README.md) · [Theme](../README.md) · [Previous lesson](../step_02_ag_ui_tools_and_state/README.md) · [Next lesson](../../03_a2ui/step_01_a2ui_messages_by_hand/README.md)

<!-- /genui-orientation -->

**What this step adds:** the coding agent from the harness codelab, driven
from a browser. `harness/` is a verbatim copy of `step_21_streaming_headless`
(the stage 15 loop with streaming). `bridge.py` runs that loop and turns
every model delta, tool call, tool result, permission question and todo
update into an AG-UI event. On the page, the hand-written SSE reader and
message bookkeeping are gone: `@ag-ui/client`'s `HttpAgent` does the
request, the parsing, the verification and the state, and the page only
subscribes to what it draws.

> **Local use only.** This server runs shell commands in its work
> directory for anyone who can reach the port, and the harness's "ask"
> permission tier is auto-approved by `bridge.py` (only `deny` still
> holds). It binds to 127.0.0.1 and has no authentication. Never expose
> it; a product ends the run with an interrupt and asks the user instead.

## Why: what breaks without it

Steps 01 and 02 wrote small agents for the protocol. The agent worth
having is the one the harness codelab spent twenty steps on: tools,
permissions, todos, streaming. Rewriting it for a browser would fork it,
and every later harness step would need porting twice. The claim of a
transport is that it needs none of that: the same loop, unchanged, and a
thin layer that turns its side effects into events. This step is that
claim tested, including the parts that do not fit (a permission prompt
with nobody at the terminal, a server-side todo list with one browser per
process).

## Quick demo

```bash
python demo.py
```

```text
> Create hello.py that prints 'hello from AG-UI', then run it with python and report the output.
  RUN_STARTED
  STATE_SNAPSHOT       0 todos
  TOOL_CALL_START      write_file
  TOOL_CALL_ARGS       1 events: {"path":"hello.py","content":"print('hello from AG-UI')\n"}
  TOOL_CALL_END
  TOOL_CALL_RESULT     Wrote hello.py
  TOOL_CALL_START      bash
  TOOL_CALL_ARGS       1 events: {"command":"python hello.py"}
  TOOL_CALL_END
  CUSTOM               permission: run: python hello.py -> allow
  TOOL_CALL_RESULT     hello from AG-UI
  TEXT_MESSAGE_START
  TEXT_MESSAGE_CONTENT 27 events: I have created hello.py that prints 'hello from AG-UI' and r
  TEXT_MESSAGE_END
  RUN_FINISHED         usage 1148 in, 28 out
> Plan this with write_todos first: add a function greet(name) to hello.py, call it with 'AG-UI', run the file again.
  RUN_STARTED
  STATE_SNAPSHOT       0 todos
  TOOL_CALL_START      write_todos
  TOOL_CALL_ARGS       1 events: {"todos":[{"content":"Add a function greet(name) to hello.py
  TOOL_CALL_END
  TOOL_CALL_RESULT     [ ] Add a function greet(name) to hello.py | [ ] Call greet(
  STATE_DELTA          replace /todos (3 todos)
  TOOL_CALL_START      read_file
  TOOL_CALL_ARGS       1 events: {"path":"hello.py"}
  TOOL_CALL_END
  TOOL_CALL_RESULT     print('hello from AG-UI')
  TOOL_CALL_START      bash
  TOOL_CALL_ARGS       1 events: {"command":"python hello.py"}
  TOOL_CALL_END
  CUSTOM               permission: run: python hello.py -> allow
  TOOL_CALL_RESULT     hello from AG-UI
  RUN_FINISHED         usage 2053 in, 50 out
status: finished; todos: ['[x] Add a function greet(name) to hello.py', "[x] Call greet('AG-UI') in hello.py", '[~] Run hello.py again and report output']
workdir: ['hello.py']
saved demo.png
```

The second run had 46 event lines: three more `write_todos` groups (each
followed by a `STATE_DELTA`), two `write_file` calls and the final text
message are cut here to keep the listing short.

![demo](demo.png)

## Files

```text
step_03_ag_ui_from_the_harness/
├── server.py               FastAPI app: moves into the work directory, then POST /agent runs one harness turn as events; closes the run when the page leaves
├── bridge.py               the harness loop as an event generator: deltas, tool calls, permissions and todos as AG-UI events; capped, keepalives, tool errors as results
├── llm.py                  settings only; loads API_KEY, BASE_URL and MODEL before any harness module is imported
├── sse.py                  SSE reader in Python, used by the tests and demo.py
├── harness/                verbatim copy of the harness codelab's step 21 (call_llm, execute, todos, permissions, sandbox)
├── index.html              the page shell: prompt, chat, the todo panel
├── app.js                  HttpAgent from @ag-ui/client; the page subscribes to events and draws them; rolls a failed run back
├── client-entry.mjs        the one line esbuild bundles into vendor/ag-ui-client.js
├── http-agent.test.mjs     node --test: the real HttpAgent against a fake server replaying the bridge's stream
├── test_step.py            offline pytest: fake model, bridge events, real harness tools in a temp dir, endpoint; runs npm
├── demo.py                 bundles the client if needed, starts the server, drives one coding task, saves demo.png
├── demo.png                the recorded page
├── package.json            @ag-ui/client and esbuild; npm run build bundles, npm test = node --test
├── package-lock.json       pinned npm dependency tree
├── .gitignore              node_modules/, vendor/ (the bundle), workdir/ (the agent's files)
└── README.md               this file
```

## Two codelabs, one loop

The harness codelab built an agent loop for a terminal. Its `call_llm`
streams text through an `on_delta` callback and assembles tool calls;
`tools.execute` runs one call through the permission rules; `write_todos`
keeps a plan that is injected into every request. None of that is about
the terminal. The terminal is one *transport*, in the report's word, and
AG-UI is another.

So the bridge does not touch `harness/`. It calls the same functions and
translates their side effects. A text delta becomes `TEXT_MESSAGE_CONTENT`.
An assembled tool call becomes `TOOL_CALL_START`, `TOOL_CALL_ARGS`,
`TOOL_CALL_END`. The result of `execute` becomes `TOOL_CALL_RESULT`. The
plan becomes shared state: `STATE_SNAPSHOT {"todos": [...]}` at the start
and `STATE_DELTA replace /todos` after every `write_todos`. The token
usage the harness already collects rides on `RUN_FINISHED`. And a
permission question, which the terminal harness asks at the prompt,
becomes a `CUSTOM` event named `permission`, because the browser has no
prompt to ask at.

On the other side, `@ag-ui/client` is what a product would use. It sends
the `RunAgentInput`, verifies that the events arrive in a legal order,
rebuilds the message list from `TEXT_*` and `TOOL_*` events, applies
`STATE_*` events with JSON Patch, and calls a subscriber method per event
with useful extras such as the text buffered so far.

## The code, piece by piece

### 1. A callback turned into a generator

`bridge.py`:

```python
def streamed(messages):
    """call_llm as a generator: ("delta", text) while it streams, then ("message", (message, usage)).

    call_llm blocks and reports text through a callback. A worker thread runs
    it and pushes every callback onto a queue; this generator drains the queue.
    """
    items = queue.Queue()

    def worker():
        try:
            result = call_llm(messages, on_delta=lambda text: items.put(("delta", text)))
            items.put(("message", result))
        except Exception as error:  # noqa: BLE001 - re-raised on the generator side
            items.put(("error", error))

    threading.Thread(target=worker, daemon=True).start()
    while True:
        try:
            kind, payload = items.get(timeout=KEEPALIVE_AFTER)
        except queue.Empty:
            yield "keepalive", None  # the model is thinking; say so on the wire
            continue
        if kind == "error":
            raise payload
        yield kind, payload
        if kind == "message":
            return
```

`call_llm` pushes; an event stream pulls. A queue between two threads
joins them without changing the harness. A model that thinks for a while
sends nothing, and a proxy drops a stream that says nothing for too long:
after `KEEPALIVE_AFTER` (15 s) of silence the generator yields
`KEEPALIVE`, the SSE comment `: keepalive`, which `server.py` writes raw
(there is no AG-UI event for it) and every SSE reader ignores.

### 2. The loop, event by event

`bridge.py`:

```python
        for calls in range(MAX_CALLS + 1):
            if calls == MAX_CALLS:
                raise RuntimeError(f"stopped after {MAX_CALLS} model calls in one run")
...
            for tool_call in message.tool_calls:
                # the parent is the text message, when there was one
                yield ToolCallStartEvent(tool_call_id=tool_call.id, tool_call_name=tool_call.function.name, parent_message_id=message_id if started else None)
                yield ToolCallArgsEvent(tool_call_id=tool_call.id, delta=tool_call.function.arguments)
                yield ToolCallEndEvent(tool_call_id=tool_call.id)

                ASKED.clear()
                result = run_tool(tool_call)
                for reason in ASKED:
                    yield CustomEvent(name="permission", value={"reason": reason, "decision": "allow"})
                yield ToolCallResultEvent(message_id=str(uuid4()), tool_call_id=tool_call.id, content=result, role="tool")
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                if tool_call.function.name == "write_todos":
                    yield StateDeltaEvent(delta=[{"op": "replace", "path": "/todos", "value": copy.deepcopy(todos.TODOS)}])
```

The harness assembles a tool call before the loop sees it, so the
arguments go out as one `TOOL_CALL_ARGS` delta. Step 02 streamed them
piece by piece; both are legal. The loop is capped at `MAX_CALLS` (40)
model calls, the same cap the harness's own loop has; past it the run
ends with `RUN_ERROR`, and every call made before that has its result.

`run_tool` is `execute`, the harness's own function with the permission
layer, wrapped so that nothing it raises can end the run without a
result for the call:

```python
def run_tool(tool_call):
    """tools.execute with every failure as a result: the page gets one TOOL_CALL_RESULT per call."""
    name = tool_call.function.name
    if name not in TOOLS:
        return f"Error: no tool named {name!r}."
    try:
        _, result = execute(tool_call)
    except json.JSONDecodeError as error:
        return f"Error: the arguments of {name} are not a JSON object: {error}"
    except Exception as error:  # noqa: BLE001 - the tool failed; the model reads why and goes on
        return f"Error: {type(error).__name__}: {error}"
```

A client that received `TOOL_CALL_END` and then `RUN_ERROR` would hold a
transcript with a call and no result, which the API refuses on every
later run; this is why the error goes to the model as text instead.

### 3. Permission without a prompt

`bridge.py`:

```python
def approve_for_the_page(reason):
    """Stands in for ui.approve: the browser has no prompt, so record and allow."""
    ASKED.append(reason)
    return True


ui.approve = approve_for_the_page
```

The harness asks `ui.approve(reason)` when a bash command is not on the
allow list. The bridge answers yes and tells the page what was asked. A
real product would end the run with an interrupt outcome and let the page
answer on the next run; the harness codelab's step 35 covers that pattern
on the terminal side. Until then, this is the warning at the top of this
file: `python -c ...`, `pip install ...` and every other "ask" command
runs. `ASKED`, like the harness's `todos.TODOS`, is a module global: one
user per process, and two tabs would interleave their permission reports
and todo lists.

### 4. The harness works in a directory

`server.py`:

```python
STEP = Path(__file__).resolve().parent
WORKDIR = Path(os.environ.get("HARNESS_WORKDIR", STEP / "workdir")).resolve()
WORKDIR.mkdir(parents=True, exist_ok=True)
os.chdir(WORKDIR)  # before the harness is imported: it takes the cwd as its project
```

`permissions.py`, `sandbox.py` and the system prompt all read the current
directory when they are imported. The server moves first, imports second.

### 5. Bundling the client

`client-entry.mjs`:

```js
export { HttpAgent } from "@ag-ui/client";
```

`@ag-ui/client` imports `rxjs`, `zod` and others by bare name. A browser
cannot resolve those without a bundler. One `esbuild` call (`npm run
build`) flattens the package into `vendor/ag-ui-client.js`; it is the only
build step in this sub-theme, and it exists because the library under
study needs it.

### 6. Subscribing instead of parsing

`app.js`:

```js
const agent = new HttpAgent({ url: "/agent" });
...
agent.subscribe({
  onEvent({ event }) {
    wire.textContent += JSON.stringify(event) + "\n";
  },
  onTextMessageStartEvent() {
    textElement = addMessage("assistant", "");
  },
  onTextMessageContentEvent({ textMessageBuffer }) {
    textElement.textContent = textMessageBuffer; // the client keeps the buffer
  },
```

`agent.addMessage(...)` then `await agent.runAgent()` is the whole run.
After it, `agent.messages` holds the user message, the assistant messages
with their tool calls and the tool results, and `agent.state` holds the
todos; the next run sends all of it.

What `runAgent()` does on failure is worth knowing exactly (checked
against `@ag-ui/client` 0.0.59). A non-200 answer, a dead server or an
illegal event order rejects the promise. A `RUN_ERROR` does not: the
promise resolves, `onRunErrorEvent` fires, and `agent.messages` keeps the
half-built assistant message, tool calls without results included. So
the page notes the message count before the run and cuts back to it
whenever the status did not reach `finished`:

```js
  } finally {
    if (status.textContent !== "finished") agent.messages = agent.messages.slice(0, mark);
    running = false;
  }
```

### 7. The client tested against the bridge's stream

`http-agent.test.mjs`:

```js
  const agent = new HttpAgent({ url: `http://127.0.0.1:${server.address().port}/agent`, threadId: "t" });
  agent.addMessage({ id: "u1", role: "user", content: "write hello.py" });
...
  assert.deepEqual(seen, SCRIPT.map((e) => e.type));
  assert.deepEqual(tools, [["write_file", "hello.py"]]);
  assert.deepEqual(agent.state, { todos: [{ content: "write it", status: "completed" }] });
  assert.deepEqual(agent.messages.map((m) => m.role), ["user", "assistant", "tool", "assistant"]);
```

A Node `http` server replays the exact event sequence `bridge.py`
produces, keepalive comment first. The test runs offline and proves the
two ends agree. A second test replays a run that ends in `RUN_ERROR`
after a tool call and shows what the client keeps. One thing the replay
found: the client splits events on `\n\n` only, so the bridge's frames
must use LF (they do; `EventEncoder` writes `\n`).

## Run it

Prerequisites: step 02's Python packages plus the harness's
(`rich`, `pyyaml`; see the harness codelab's `requirements.txt`), Node 22
and npm for the bundle, `playwright` for `demo.py`.

```bash
npm install
npm run build
python server.py
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."
npm install
npm run build
python server.py
```

Open http://127.0.0.1:8023. The agent works in `./workdir`; set
`HARNESS_WORKDIR` to point it elsewhere.

Expected output: `python server.py` prints the work directory and the
local-use warning, then uvicorn's start line. In the page, a tool call
appears as `write_file({"path":"hello.py",...})` with its result
underneath, a `permission: run: python hello.py -> allow` line when bash
needed one, the todo panel fills after `write_todos`, and the status line
ends in `finished` with the token usage beside it. The quick demo above
is the same two prompts, folded.

Tests, offline:

```bash
python -m pytest -q test_step.py
npm test
```

`test_step.py` runs `npm install`, `npm test` and `npm run build` itself
when `node` is on the PATH. To confirm that `harness/` is the codelab's
step 21 unchanged:

```bash
diff -r ../../../step_21_streaming_headless/harness harness -x __pycache__
```

## Error handling

- The model call fails: `RUN_ERROR` with the exception text; the page
  shows `error: ...` and cuts its history back to before the run.
- The model keeps calling tools: after 40 model calls the run ends with
  `RUN_ERROR stopped after 40 model calls in one run`; every call made
  has its `TOOL_CALL_RESULT`.
- A tool call the harness cannot run (arguments that are not JSON, an
  unknown name, a missing argument, an exception in the tool): the
  `TOOL_CALL_RESULT` is `Error: ...` and the model reads it on the next
  round. A `deny` rule is `Blocked by policy: ...` the same way.
- The model is silent for 15 s: a `: keepalive` comment on the wire, not
  an event.
- The server is down or answers 4xx/5xx (a 422 for a body that is not a
  `RunAgentInput`): `runAgent()` rejects, the page shows the error.
- A submit while a run streams, or an empty prompt: dropped.
- The browser leaves mid-run: the endpoint closes the generator at the
  next event; a tool already running finishes.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- Not safe to expose: see the warning at the top. `deny` rules still
  apply (`rm -rf`, `git push`, `curl`...), everything else runs.
- One user per process: `ASKED`, the todo list and the work directory are
  process globals.
- The harness's `history.strip` and compaction do not run: the page owns
  the transcript and sends it whole. Long sessions grow without bound
  until the page reloads.
- The harness's tool named `bash` runs the command through `shell=True`,
  which is `cmd.exe` on Windows, and `sandbox.py` has no sandbox there
  (seatbelt on macOS, bubblewrap on Linux when installed, none otherwise).
- `@ag-ui/client` 0.0.59 does not reject on `RUN_ERROR`; the page's
  rollback is what keeps the history valid.

## What to notice

- `harness/` has no diff against the harness codelab. The bridge is about
  180 lines and the page about 100; that is the cost of a second
  transport.
- The client owns the transcript. The harness's `history.strip` and
  compaction, which edit the server-side list, do not apply: the page
  sends the full history every run. A product would move that logic to
  the client or keep a server-side thread store.
- `STATE_SNAPSHOT` says `0 todos` at the start of the second run because
  the first task was a single step and the harness skips the plan for
  those. A third run would start from three: the todo list is a module
  global on the server, and the snapshot refreshes the page's copy.
- The `usage` on `RUN_FINISHED` is the same dict the terminal prints
  after every reply, in the protocol's `TokenUsage` shape.

## What the next sub-theme adds

A2UI: instead of a text reply, the agent's output *is* the UI, as a
stream of component messages a renderer draws; sub-theme 03 starts with
those messages written by hand.

## Diff from the previous step

- `harness/` is new: the harness codelab's step 21, copied.
- `bridge.py` replaces `agent.py`, `tools.py` and `json_patch.py`: the
  loop is the harness's, the tools are the harness's, the state is the
  harness's plan.
- `llm.py` only loads settings; the model call lives in `harness/llm.py`.
- `app.js` uses `HttpAgent` from `@ag-ui/client`; `sse.mjs`,
  `json-patch.mjs` and `render.mjs` are gone.
- `package.json` gains `@ag-ui/client`, `esbuild` and a `build` script;
  `http-agent.test.mjs` tests the real client against a fake server.
