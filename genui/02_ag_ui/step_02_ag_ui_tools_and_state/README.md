# Step 02 - Tool calls and shared state

**What this step adds:** two more parts of the AG-UI vocabulary. Tool
calls stream as `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` and
`TOOL_CALL_RESULT`. Shared state travels as `STATE_SNAPSHOT` (the whole
object) and `STATE_DELTA` (a JSON Patch). The server tools do not draw
anything: each returns a patch to a `dashboard` object, and the page
renders that object with three small renderers. One tool,
`confirm_purchase`, belongs to the page: the server streams the call, the
page runs it, and its answer comes back as a tool message on the next run.

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

## Generative UI as state

The report's "static generation" mode has the agent pick a component and
fill its props. Sub-theme 01 sent one JSON message per pick. AG-UI does it
differently: the UI is a piece of *state*, and the agent edits the state.
The page never receives "render a metric". It receives "the dashboard
object now has one more metric", as a JSON Patch, and re-renders.

This changes three things. The client owns the object, so it can send it
back on the next run and the agent continues from the same dashboard. A
patch is small, so a table with fifty rows updates one cell at a time.
And any part of the UI that reads the state stays in sync, because there
is one object, not a stream of commands.

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
                open_call = (piece.index, piece.id)
                yield ("tool_start", piece.id, piece.function.name)
            if piece.function and piece.function.arguments:
                yield ("tool_args", open_call[1], piece.function.arguments)
    if open_call:
        yield ("tool_end", open_call[1])
```

The model streams a tool call as fragments keyed by index: the first one
carries the id and name, the rest carry pieces of the JSON arguments. The
generator turns that into the same three-part shape AG-UI uses, so the
agent can map each tuple to one event.

### 3. The loop, with state

`agent.py`:

```python
    state = copy.deepcopy(input.state) if input.state else initial_state()
    yield StateSnapshotEvent(snapshot=state)
...
            for call_id, call in calls.items():
                if call["name"] in client_tools:
                    waiting_on_client = True  # the page runs it; its result opens the next run
                    continue
                result, operations = execute(call["name"], json.loads(call["arguments"] or "{}"))
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
    const parts = splitPointer(operation.path);
    if (parts.length === 0) throw new Error("the root cannot be patched in place");
    let parent = document;
    for (const part of parts.slice(0, -1)) parent = Array.isArray(parent) ? parent[Number(part)] : parent[part];
    const key = parts[parts.length - 1];
```

Three operations, `add`, `replace`, `remove`, are all AG-UI state deltas
use here. `json_patch.py` is the same code for the server and the tests.

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
        const call = assistant.toolCalls.find((c) => c.id === event.toolCallId);
        toolElements[call.id].textContent += ")";
        if (CLIENT_TOOLS.some((t) => t.name === call.function.name)) pendingClientCalls.push(call);
        break;
      }
```

`showState()` rebuilds the dashboard from the state object on every
change. When a run ends with a pending client call, `askToConfirm` draws
the buttons; the click pushes a tool message and calls `runAgent()` with
no text.

### 7. Rendering from state

`render.mjs`:

```js
export function renderDashboard(dashboard) {
  const root = el("div", "dashboard");
  const metrics = el("div", "metrics");
  for (const metric of dashboard.metrics || []) metrics.appendChild(renderMetric(metric));
  root.appendChild(metrics);
  if (dashboard.table) root.appendChild(renderTable(dashboard.table));
  if (dashboard.chart) root.appendChild(renderChart(dashboard.chart));
```

The renderers are the sub-theme 01 idea, reduced to what this step needs:
one function per component, props in, DOM out.

## Run it

```bash
python server.py
```

Open http://127.0.0.1:8022. Run the default prompt, then type "Buy a new
cooler for $40" and press Confirm when the panel appears.

Tests, offline:

```bash
python -m pytest -q test_step.py
npm test
```

## What to notice

- `TOOL_CALL_ARGS` streams the JSON arguments in pieces. The page shows
  them as they arrive; the server parses them only at `TOOL_CALL_END`.
- The state snapshot at the start of the second run says `3 metrics`: the
  page sent the dashboard back, and the server continued from it.
- The run that calls `confirm_purchase` has no `TOOL_CALL_RESULT`. The
  result exists only in the page's history, as a tool message.
- Nothing in the wire says "metric card". The component vocabulary lives
  in the state shape and the renderers, not in the protocol.

## Diff from the previous step

- `tools.py` and `json_patch.py` are new: server tools return patches.
- `llm.py` streams tool call fragments as well as text.
- `agent.py` loops over model calls, emits state and tool events, and
  stops when a client tool is called.
- `app.js` keeps `state`, applies patches, draws tool calls and the
  confirm panel; `render.mjs` and `json-patch.mjs` are new.
