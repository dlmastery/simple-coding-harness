# Step 02 - Tool calls and shared state

<!-- genui-orientation -->
**Lesson 6 of 23.** [Course](../../README.md) · [Theme](../README.md) · [Previous lesson](../step_01_ag_ui_server/README.md) · [Next lesson](../step_03_ag_ui_from_the_harness/README.md)

<!-- /genui-orientation -->

**What this step adds:** two more parts of the AG-UI vocabulary. Tool
calls stream as `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` and
`TOOL_CALL_RESULT`. Shared state travels as `STATE_SNAPSHOT` (the whole
object) and `STATE_DELTA` (a JSON Patch). The server tools do not draw
anything: each returns a patch to a `dashboard` object, and the page
renders that object with three small renderers. One tool,
`confirm_purchase`, belongs to the page: the server streams the call, the
page runs it, and its answer comes back as a tool message on the next run.

## Why: what breaks without it

Step 01 could only stream text. A dashboard is not text: it is components
with props, and it changes. Sending "render a metric" commands (sub-theme
01's way) works until the page reloads or a second view needs the same
data, because nobody holds the object. Putting the UI in the shared state
gives it one owner and one wire shape: the server sends a patch, the page
applies it and re-renders, and sends the whole object back on the next run
so the agent continues from what the user sees. And a tool the page owns
(`confirm_purchase`) is what lets the agent ask the user something and
wait, without the server holding a connection open.

## Quick demo

```bash
python demo.py
```

```text
> Show me a dashboard for a lemonade stand.
  RUN_STARTED
  STATE_SNAPSHOT       0 metrics, 0 purchases
  TOOL_CALL_START      show_metric
  TOOL_CALL_ARGS       13 events: {"title": "Total Revenue", "value": "$2,450", "delta": "+8%"
  TOOL_CALL_END
  STATE_DELTA          add /dashboard/metrics/-
  TOOL_CALL_RESULT     ok
  TOOL_CALL_START      show_table
  TOOL_CALL_ARGS       64 events: {"columns":["Day","Lemonades Sold","Revenue"],"rows":[["Mond
  TOOL_CALL_END
  STATE_DELTA          replace /dashboard/table
  TOOL_CALL_RESULT     ok
  TOOL_CALL_START      show_chart
  TOOL_CALL_ARGS       34 events: {"kind":"bar","labels":["Monday","Tuesday","Wednesday","Thur
  TOOL_CALL_END
  STATE_DELTA          replace /dashboard/chart
  TOOL_CALL_RESULT     ok
  TEXT_MESSAGE_START
  TEXT_MESSAGE_CONTENT 20 events: Here's the dashboard for your lemonade stand with key metric
  TEXT_MESSAGE_END
  RUN_FINISHED
> Buy a new cooler for $40.
  RUN_STARTED
  STATE_SNAPSHOT       3 metrics, 0 purchases
  TOOL_CALL_START      confirm_purchase
  TOOL_CALL_ARGS       10 events: {"item":"new cooler","cost":40}
  TOOL_CALL_END
  RUN_FINISHED
> [click Confirm]
  RUN_STARTED
  STATE_SNAPSHOT       3 metrics, 0 purchases
  TOOL_CALL_START      record_purchase
  TOOL_CALL_ARGS       10 events: {"item":"new cooler","cost":40}
  TOOL_CALL_END
  STATE_DELTA          add /dashboard/purchases/-
  TOOL_CALL_RESULT     ok
  TEXT_MESSAGE_CONTENT 13 events: The purchase of the new cooler for $40 has been recorded.
  RUN_FINISHED
dashboard: metrics=['Total Revenue', 'Lemonades Sold', 'Customer Satisfaction'] table=1 chart=1 purchases=['new cooler: $40']
```

The first run had three `show_metric` groups; two are cut here to keep the
listing short, and the two `TEXT_MESSAGE_START`/`END` lines around the
last reply are cut for the same reason.

![demo](demo.png)

## Files

```text
step_02_ag_ui_tools_and_state/
├── server.py             FastAPI app: POST /agent streams the run and closes it when the page leaves, GET / serves the page
├── agent.py              run(): STATE_SNAPSHOT, then at most MAX_TURNS rounds of TEXT_*, TOOL_CALL_*, STATE_DELTA; stops on a client tool
├── tools.py              server tools; each returns JSON Patch operations against the dashboard state; execute() never raises
├── json_patch.py         JSON Patch add/replace/remove with JSON Pointer paths, checked and applied on the server
├── llm.py                streaming chat completion that yields text and tool call fragments
├── sse.py                SSE reader in Python, used by the tests and demo.py
├── index.html            the page shell: prompt, chat, dashboard, the wire panel
├── app.js                hand-written client: keeps state, applies patches, draws tool calls, runs confirm_purchase; rolls a failed run back
├── render.mjs            three renderers (metric, table, chart) from the dashboard object to DOM; array props guarded
├── json-patch.mjs        the same JSON Patch code as json_patch.py, for the page; refuses prototype keys and bad indexes
├── sse.mjs               SSE reader for the page: fetch() body stream to JSON events, LF or CRLF
├── json-patch.test.mjs   node --test for splitPointer and applyPatch
├── sse.test.mjs          node --test for parseBlock and readEvents
├── test_step.py          offline pytest: fake model with tool fragments, state events, patches, client tool hand-off
├── demo.py               starts the server, drives the page through the two runs and the Confirm click, saves demo.png
├── demo.png              the recorded page
├── package.json          npm test = node --test (no dependencies)
└── README.md             this file
```

## Generative UI as state

The report's "static generation" mode has the agent pick a component and
fill its props. Sub-theme 01 sent one JSON message per pick. AG-UI does it
differently: the UI is a piece of *state*, and the agent edits the state.
The page never receives "render a metric". It receives "the dashboard
object now has one more metric", as a JSON Patch, and re-renders.

This changes three things. The client owns the object, so it can send it
back on the next run and the agent continues from the same dashboard. A
patch can be as small as the change: this step's tools replace a whole
table or chart, but a `replace` of `/dashboard/table/rows/3/1` would
update one cell of a fifty-row table without resending it. And any part
of the UI that reads the state stays in sync, because there is one object,
not a stream of commands.

Client tools close the other direction. The page declares
`confirm_purchase` in `RunAgentInput.tools`. The model sees it next to the
server tools and calls it the same way. The server cannot run it, so it
streams the call and finishes the run. The page shows two buttons, turns
the click into a tool message, and starts a new run with no user text.
The model then sees `confirmed` and calls `record_purchase`.

## The code, piece by piece

### 1. Tools that return patches

`tools.py`:

```python
def show_metric(title: str, value: str, delta: str = "") -> list:
    """Add one metric card to the dashboard."""
    return [{"op": "add", "path": "/dashboard/metrics/-", "value": {"title": title, "value": value, "delta": delta}}]


def show_table(columns: list, rows: list) -> list:
    """Set the dashboard table (one table, replaced each time)."""
    return [{"op": "replace", "path": "/dashboard/table", "value": {"columns": columns, "rows": rows}}]
```

`/dashboard/metrics/-` is JSON Pointer for "append". Each tool is a pure
function from arguments to operations; the agent decides what to do with
them.

### 2. Streaming tool calls from the model

`llm.py`:

```python
        for piece in delta.tool_calls or []:
            if open_call and open_call[0] != piece.index:
                yield ("tool_end", open_call[1])
                open_call = None
            if open_call is None:
                function = getattr(piece, "function", None)
                open_call = (piece.index, piece.id or f"call_{piece.index}")
                yield ("tool_start", open_call[1], (function and function.name) or "")
            if piece.function and piece.function.arguments:
                yield ("tool_args", open_call[1], piece.function.arguments)
    if open_call:
        yield ("tool_end", open_call[1])
```

The model streams a tool call as fragments keyed by index: the first one
carries the id and name, the rest carry pieces of the JSON arguments. The
generator turns that into the same three-part shape AG-UI uses, so the
agent can map each tuple to one event. OpenAI's endpoint sends one call
at a time; an endpoint that leaves the id off the first fragment gets
`call_<index>` instead, so `ToolCallStartEvent` always has an id.

### 3. The loop, with state

`agent.py`:

```python
    state = copy.deepcopy(input.state) if input.state else initial_state()
    yield StateSnapshotEvent(snapshot=state)
...
        for turn in range(MAX_TURNS + 1):
            if turn == MAX_TURNS:
                raise RuntimeError(f"stopped after {MAX_TURNS} tool rounds")
...
            for call_id, call in calls.items():
                if call["name"] in client_tools:
                    waiting_on_client = True  # the page runs it; its result opens the next run
                    continue
                result, operations = execute(call["name"], call["arguments"])
                if operations:
                    apply_patch(state, operations)
                    yield StateDeltaEvent(delta=operations)
                yield ToolCallResultEvent(message_id=str(uuid4()), tool_call_id=call_id, content=result, role="tool")
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            if waiting_on_client:
                break
```

The snapshot at the start is the state the client sent, or the empty
dashboard. Every server tool call applies its patch on the server first,
so the two copies stay equal, then sends it. A client tool call sets a flag
and the loop stops calling the model: the run ends, and the page has the
call.

The loop has three exits: the model answers without tool calls, a client
tool is called, or `MAX_TURNS` (8) model calls have been made, which ends
the run with `RUN_ERROR` instead of a bill. A tool that cannot run is not
an exit: `execute` turns a bad name, arguments that are not a JSON object,
a missing argument or an exception inside the tool into an `Error: ...`
result, one per call, and the model reads it on the next round.

`tools.py`:

```python
def execute(name, arguments):
    """Run one server tool on the JSON arguments the model wrote.

    Returns (result text for the model, patch operations) and never raises:
    a bad name, arguments that are not a JSON object, a missing argument or
    a tool that fails all come back as an "Error: ..." result, so the model
    can try again and the run goes on.
    """
    if name not in TOOLS:
        return f"Error: no tool named {name!r}.", []
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError as error:
        return f"Error: the arguments of {name} are not a JSON object: {error}", []
```

One more ordering rule: when the model writes text and then calls tools in
the same reply, `TEXT_MESSAGE_END` is sent before the first
`TOOL_CALL_START`. The vendored `@ag-ui/client` 0.0.59 would accept the
other order, but earlier clients refused any non-text event while a text
message was open, and step 03's bridge keeps the same rule.

### 4. Tool calls and results in the history

`agent.py`:

```python
        if m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
        elif m.role == "assistant":
            entry = {"role": "assistant", "content": m.content or None}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in m.tool_calls
                ]
            out.append(entry)
```

For the client tool to work, the next run's history must contain the
assistant message with the call and the tool message with the answer.
AG-UI messages carry both, in the same shape OpenAI expects.

### 5. Applying a patch in the page

`json-patch.mjs`:

```js
export function applyPatch(document, operations) {
  for (const operation of operations) {
    if (!OPS.has(operation.op)) throw new Error(`unsupported op ${operation.op}`);
    const parts = splitPointer(operation.path ?? "");
    if (parts.length === 0) throw new Error("the root cannot be patched in place");
    let parent = document;
    for (const part of parts.slice(0, -1)) parent = step(parent, part);
    const key = parts[parts.length - 1];
    if (FORBIDDEN.has(key)) throw new Error(`refused path segment ${key}`);
```

Three operations, `add`, `replace`, `remove`, are all this step's state
deltas use. AG-UI's `STATE_DELTA` is full RFC 6902 (the reference client
applies it with `fast-json-patch`), so a `move`, `copy` or `test` from
another agent makes this `applyPatch` throw, and the page reports the run
as failed. The path is data from the wire, so it is checked before it is
followed: `__proto__`, `constructor` and `prototype` are refused (a patch
could otherwise reach `Object.prototype`), a list index must be digits,
and a parent that does not exist is an error. `json_patch.py` is the same
code for the server and the tests, with the same verdicts.

### 6. State events and the client tool in the page

`app.js`:

```js
        case "STATE_SNAPSHOT":
          state = event.snapshot;
          showState();
          break;
        case "STATE_DELTA":
          applyPatch(state, event.delta);
          showState();
          break;
...
        case "TOOL_CALL_END": {
          const call = findCall(event.toolCallId);
          if (!call) break;
          toolElements[call.id].textContent += ")";
          if (CLIENT_TOOLS.some((t) => t.name === call.function.name)) pendingClientCalls.push(call);
          break;
        }
```

`showState()` rebuilds the dashboard from the state object on every
change. When a run ends with a pending client call, `askToConfirm` draws
the buttons; the click pushes a tool message and calls `runAgent()` with
no text.

The history is the part that must stay valid. The assistant message is
pushed as soon as its first event arrives, so tool results land after
it; if the run then fails, that message would carry tool calls with no
results, and the API refuses such a history on every later run. So the
whole run sits in a `try`, and on `RUN_ERROR`, a non-200 answer, a dead
server or a stream that ends without a terminal event, everything pushed
during the run is rolled back:

```js
  } catch (error) {
    // A RUN_ERROR, a 4xx/5xx, a dead server, a cut stream: the run is rolled
    // back. Its half-built assistant message would carry tool calls with no
    // results, and the API refuses such a history on every later run.
    messages.length = mark;
    status.textContent = `error: ${error.message ?? error}`;
  } finally {
    running = false;
  }
```

The same rule covers the confirm panel: a prompt typed while a panel
waits answers it `declined` first, so the tool call gets its result before
the new user message.

### 7. Rendering from state

`render.mjs`:

```js
export function renderDashboard(dashboard) {
  const root = el("div", "dashboard");
  const metrics = el("div", "metrics");
  for (const metric of list(dashboard.metrics)) metrics.appendChild(renderMetric(metric || {}));
  root.appendChild(metrics);
  if (dashboard.table) root.appendChild(renderTable(dashboard.table));
  if (dashboard.chart) root.appendChild(renderChart(dashboard.chart));
```

The renderers are the sub-theme 01 idea, reduced to what this step needs:
one function per component, props in, DOM out. Array props go through
`list()` (an array or nothing), because the state came over the wire and
the tool schemas are not enforced by every endpoint.

## Run it

Prerequisites: step 01's (`ag-ui-protocol`, `fastapi`, `uvicorn`,
`openai`); Node 22 for `npm test`; `playwright` and `httpx` for `demo.py`.

```bash
python server.py
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."     # or OPENAI_API_KEY=... in ~\.simple-harness\env
python server.py
```

Open http://127.0.0.1:8022. Run the default prompt, then type "Buy a new
cooler for $40" and press Confirm when the panel appears.

Expected output: the chat panel shows each tool call as `show_metric({"ti`
growing character by character, then `) -> ok`; the dashboard fills in as
the `STATE_DELTA`s land; the status line goes `running` then `finished`.
The second prompt ends in a yellow confirm panel; Confirm starts a third
run with no user message, and the purchase list appears. The quick demo
above is the same three runs, folded.

Tests, offline:

```bash
python -m pytest -q test_step.py
npm test
```

`demo.py` uses the fixed port 8022 and stops with an error if the port is
in use.

## Error handling

- The model call fails: `RUN_ERROR` with the exception text, no
  `RUN_FINISHED`; the page shows `error: ...` and rolls the run's messages
  back, so the next prompt starts from a valid history.
- The model calls tools for eight rounds without stopping: `RUN_ERROR`
  `stopped after 8 tool rounds`; every call made got its result first.
- A tool call with arguments that are not JSON, an unknown tool name, a
  missing argument, an exception inside the tool: one `TOOL_CALL_RESULT`
  carrying `Error: ...`, no `STATE_DELTA`, and the run goes on.
- A patch the page cannot apply (an unknown op, a prototype key): the page
  throws, the run is reported as failed and rolled back; the server's copy
  of the state has the patch, the page's does not, until the next
  `STATE_SNAPSHOT`.
- The server is down or answers 4xx/5xx: `error: ...` from the page
  itself; a stream that ends without a terminal event is
  `error: the stream ended without RUN_FINISHED`.
- A prompt while a confirm panel waits: the panel is answered `declined`,
  then the prompt runs. A submit while a run streams is dropped.
- The browser leaves mid-run: the endpoint closes the generator, and with
  it the model stream.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- The state is one object per browser tab, sent in full on every run; the
  server keeps nothing between runs. Two tabs are two dashboards.
- The tool schemas are sent to the model but not enforced by the server:
  `execute` checks the argument names against the function signature, and
  the renderers guard array props. A string where a number belongs is
  drawn as a string.
- `confirm_purchase` is one client tool with one hard-coded panel. A
  general client-tool dispatcher is what `@ag-ui/client` gives you in
  step 03.
- No authentication, one process, 127.0.0.1: a local demo.

## What to notice

- `TOOL_CALL_ARGS` streams the JSON arguments in pieces. The page shows
  them as they arrive; the server parses them only at `TOOL_CALL_END`.
- The state snapshot at the start of the second run says `3 metrics`: the
  page sent the dashboard back, and the server continued from it.
- The run that calls `confirm_purchase` has no `TOOL_CALL_RESULT`. The
  result exists only in the page's history, as a tool message.
- Nothing in the wire says "metric card". The component vocabulary lives
  in the state shape and the renderers, not in the protocol.
- In the demo's first run the model wrote its sentence after the tool
  calls, so `TEXT_MESSAGE_START` comes last. When it writes text first,
  `TEXT_MESSAGE_END` is sent before the first `TOOL_CALL_START`.

## What the next step adds

The same protocol from a real coding agent: step 21's harness behind an
AG-UI bridge, and `@ag-ui/client`'s `HttpAgent` reading it in the page
instead of this hand-written reader.

## Diff from the previous step

- `tools.py` and `json_patch.py` are new: server tools return patches.
- `llm.py` streams tool call fragments as well as text.
- `agent.py` loops over model calls (at most `MAX_TURNS`), emits state and
  tool events, and stops when a client tool is called.
- `app.js` keeps `state`, applies patches, draws tool calls and the
  confirm panel; `render.mjs` and `json-patch.mjs` are new.
