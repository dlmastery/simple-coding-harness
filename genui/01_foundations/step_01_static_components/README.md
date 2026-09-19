# Step 01 - Static components

**What this step adds:** the smallest generative UI there is. Three components
exist before the model runs: a metric, a table, a chart. The model gets them as
tools. Each tool call becomes one JSON message on a server-sent event stream,
and the page renders it with a hand-written renderer keyed by component name.
No framework, no build step: one FastAPI file, one HTML page, one JS module.

## Why: what breaks without it

A chat loop returns a paragraph. Ask it for "a dashboard" and you get a
markdown table and three sentences. The page could parse that prose, but
every reply would parse differently. Giving the model tools whose schema
*is* a component makes the reply structured data the page already knows how
to draw: `{"component": "Metric", "props": {...}}`, never markup. The
whole series keeps that shape: the page renders messages, the model never
sees the DOM.

## Quick demo

```bash
python demo.py
```

```text
prompt: show me a dashboard for a lemonade stand
6 SSE messages in 7.9s:
  {"component": "Metric", "props": {"title": "Lemonades Sold", "value": "1500 cups", "delta": "+8%"}}
  {"component": "Metric", "props": {"title": "Revenue", "value": "$4500", "delta": "+10%"}}
  {"component": "Metric", "props": {"title": "Profit", "value": "$1200", "delta": "+15%"}}
  {"component": "Table", "props": {"columns": ["Date", "Lemonades Sold", "Revenue", "Profit"], "rows": [["202...
  {"component": "Chart", "props": {"kind": "line", "labels": ["Apr 20", "Apr 21", "Apr 22", "Apr 23", "Apr 24...
  {"done": true, "usage": {"prompt_tokens": 249, "completion_tokens": 295}}
saved demo.png
```

![demo](demo.png)

## Files

```text
step_01_static_components/
├── server.py         FastAPI app: POST /api/run streams one SSE message per tool call, an error frame on failure; GET / serves the page
├── llm.py            one streamed call over the OpenAI-compatible API; key from the env or ~/.simple-harness/env
├── catalog.py        the three show_* tools as strict schemas, and message_from_call
├── page/
│   ├── index.html    the page shell: prompt box, dashboard, wire panel
│   ├── app.js        reads the SSE stream, appends one rendered component per message; always ends in data-state=done
│   └── render.mjs    three renderers keyed by component name, every prop through esc(), array props through list()
├── tests/render.test.mjs   node --test for the renderers
├── test_step.py      offline pytest: fake model stream, real server, real page code
├── demo.py           starts the server, runs the prompt headlessly, saves demo.png
├── demo.png          the recorded page
├── package.json      npm test = node --test (no dependencies)
└── README.md         this file
```

## Static generation

The State of Generative UI report separates two choices. **Transport** is
where the UI appears. **Generation** is what the agent emits. This sub-theme
is about generation, and this step is the first of its three modes: static.

Static means the components are built ahead of time. The agent does not
design anything. It selects a component and fills its props. The contract is
a JSON Schema per component, and the model sees that schema as a tool. The
schema is enforced by the API before the server sees the call, so the
renderer never receives a prop it did not expect.

What the agent gives up is layout. It cannot nest a metric inside a card or
put two charts side by side. The page decides that. What the agent gains is
safety and cost: every message is small, every prop is typed, and the page
renders in one function call. Step 02 gives the agent layout. Step 03 gives
it everything, and shows the price.

## The code, piece by piece

`catalog.py`: each tool is one function-calling schema. `strict` makes the
API reject any call that does not match, so the required list and
`additionalProperties: false` are the whole contract.

```python
def tool(name, description, properties):
    """One function-calling schema. Every property is required; nothing else is allowed."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
        },
    }
```

`catalog.py`: the three tools and the mapping to component names. A tool call
that does not fit becomes `None`, never a broken message.

```python
# tool name -> the component the page renders for it
COMPONENTS = {"show_metric": "Metric", "show_table": "Table", "show_chart": "Chart"}


def message_from_call(name, arguments):
    """One finished tool call -> the message the page renders, or None if it does not fit."""
    component = COMPONENTS.get(name)
    if component is None:
        return None
    try:
        props = json.loads(arguments)
    except json.JSONDecodeError:
        return None
    if not isinstance(props, dict):
        return None
    return {"component": component, "props": props}
```

`llm.py`: one streamed request, as a generator of events. A tool call
arrives as pieces that share an index; the pieces of two calls may
interleave, and some endpoints omit the index, so every call is assembled
until the stream ends and then emitted in index order. Nothing is guessed
from the order of arrival.

```python
        for piece in delta.tool_calls or []:
            index = piece.index
            if index is None:  # no index: the piece belongs to the call with its id, else the last one
                index = next((i for i, c in calls.items() if piece.id and c["id"] == piece.id), last_index)
                index = len(calls) if index is None else index
            call = calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
            last_index = index
            if piece.id:
                call["id"] = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call["name"] = function.name
            if function.arguments:
                call["arguments"] += function.arguments

    for index in sorted(calls):
        yield {"type": "tool_call", **calls[index]}
    yield {"type": "usage", **usage_from(final_usage)}
```

`server.py`: the SSE stream. One frame per component, a `note` for any prose
the model wrote instead, and `done` with the usage at the end. A frame is
one `data:` line holding the JSON (`json.dumps` keeps it on one line) and a
blank line; no `event:` or `id:` fields.

```python
def sse(message):
    """One SSE frame: a data line with the JSON, then a blank line."""
    return f"data: {json.dumps(message)}\n\n"


def components(prompt):
    """Run one model turn and yield one message per component the model chose."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    for event in llm.stream_chat(messages, tools=catalog.TOOL_SCHEMAS):
        if event["type"] == "tool_call":
            message = catalog.message_from_call(event["name"], event["arguments"])
            if message is not None:
                yield message
        elif event["type"] == "text":
            yield {"note": event["text"]}  # the model spoke instead of calling a tool
        elif event["type"] == "usage":
            yield {"done": True, "usage": {k: v for k, v in event.items() if k != "type"}}


@app.post("/api/run")
def run(body: Run, request: Request):
    return StreamingResponse(stream(components(body.prompt), request), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
```

`server.py`: the stream is guarded. The 200 and the headers leave before the
model answers, so a failure after that cannot become an HTTP error; it
becomes the last frame instead. And when the page goes away, the server
stops pulling from the model.

```python
def guarded(messages):
    """The messages, then a terminal frame on failure: the page must never wait for one that is not coming."""
    try:
        yield from messages
    except Exception as error:  # noqa: BLE001 - the error is the frame
        yield {"done": True, "error": f"{type(error).__name__}: {error}"}


async def stream(messages, request):
    """Encode the messages as they come; stop pulling from the model when the page has gone."""
    pending = iter(guarded(messages))
    try:
        while (message := await run_in_threadpool(next, pending, None)) is not None:
            if await request.is_disconnected():
                break
            yield sse(message)
    finally:
        pending.close()  # closes the generator chain, and with it the model stream
```

`page/render.mjs`: the renderers. Each is a pure function from props to an
HTML string, so `node --test` covers them without a browser. Every prop
passes through `esc` first: the model wrote it, so the page treats it as
text, never as markup. Array props go through `list`, because `strict`
schemas are enforced by OpenAI's endpoint and not by every compatible one.

```js
export function Metric({ title, value, delta }) {
  const sign = String(delta ?? "").trim().startsWith("-") ? "down" : "up";
  return `<div class="card metric">
    <div class="title">${esc(title)}</div>
    <div class="value">${esc(value)}</div>
    <div class="delta ${sign}">${esc(delta)}</div>
  </div>`;
}
```

```js
export const RENDERERS = { Metric, Table, Chart };

export function render(component, props) {
  // The page never trusts the name: an unknown component becomes a visible stub.
  // hasOwn, not `in`: "constructor" and "toString" are not components.
  if (!Object.hasOwn(RENDERERS, component)) return `<div class="card unknown">unknown component: ${esc(component)}</div>`;
  return RENDERERS[component](props ?? {});
}
```

`page/app.js`: the SSE reader and the loop. Frames are separated by a blank
line (`\r\n` is folded to `\n` first; the SSE spec allows either). Each
parsed message is appended to the dashboard as soon as it arrives. The body
always ends in `data-state="done"`: a non-200 answer or a cut stream is
recorded as an error frame instead of leaving the page "running" forever.

```js
    if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
    for await (const message of readSSE(response)) {
      events.push(message);
      wire.textContent += JSON.stringify(message) + "\n";
      if (message.component) dashboard.insertAdjacentHTML("beforeend", render(message.component, message.props));
    }
  } catch (error) {
    // a dead server or a cut stream: say so instead of staying "running" forever
    events.push({ done: true, error: String(error.message ?? error) });
    wire.textContent += `error: ${error.message ?? error}\n`;
  } finally {
    document.body.dataset.state = "done";
  }
```

## Run it

Prerequisites: Python 3.11+ with `fastapi`, `uvicorn`, `openai` (the
repository's `requirements.txt`); Node 22 for `npm test`; `playwright` plus
`python -m playwright install chromium` for `demo.py` only.

```bash
python server.py            # http://127.0.0.1:8010
python demo.py              # headless: prints the stream, writes demo.png
python -m pytest test_step.py
npm test                    # the renderer tests alone
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."     # or put OPENAI_API_KEY=... in ~\.simple-harness\env
python server.py
python demo.py
python -m pytest test_step.py
npm test
```

The key comes from `API_KEY` or `OPENAI_API_KEY`, in the environment or in
`~/.simple-harness/env`. `BASE_URL` and `MODEL` switch to any
OpenAI-compatible endpoint; the default is `gpt-4.1-mini`.

Expected output: `python server.py` prints uvicorn's start line and one
`POST /api/run` per run; the page shows the components as their frames
arrive and the wire panel lists every frame, ending in
`{"done": true, "usage": {...}}`. The quick demo above is the same run,
driven headlessly.

## Error handling

- No key: the first frame is `{"done": true, "error": "RuntimeError: no API
  key: ..."}`; the page prints it in the wire panel and stops.
- The model call fails or the stream is cut: the same error frame, with the
  exception's type and message. The server never leaves a stream without a
  terminal frame.
- The server is down or answers 4xx/5xx: the page records
  `{"done": true, "error": "..."}` itself and still reaches `data-state=done`.
- The browser navigates away mid-run: the server notices at the next frame,
  closes the generator and with it the model stream.
- The model writes prose instead of calling a tool: one `note` frame per
  delta, no component. A tool call whose arguments are not a JSON object is
  dropped by `message_from_call`.
- `demo.py` raises `RuntimeError` if the server does not come up within ten
  seconds instead of waiting forever.
- Leave `python server.py` with ctrl-c (ctrl-c or ctrl-break on Windows).

## Gotchas / what this is not

- `strict: true` is enforced by OpenAI's endpoint. Another `BASE_URL` may
  ignore it, so the renderers coerce array props with `list()` and treat
  everything else as text; the server does not re-validate props.
- Every tool call is emitted after the stream ends, in index order. The
  page paints one component per frame, but the frames arrive together;
  step 02 is where painting during the stream begins.
- One process, no sessions, no authentication: a local demo bound to
  127.0.0.1.
- On Windows, Python's `mimetypes` reads the registry, which may map `.js`
  to `text/plain`; `server.py` registers `.js` and `.mjs` as
  `text/javascript` so module scripts load.

## What to notice

- The model never writes markup. It emits tool calls, and the API validates
  each one against its schema before the server sees it.
- The stream is one JSON object per component. The page has no idea a model
  exists; it renders messages. That is the shape every later step keeps.
- The renderers are three functions and a lookup table. Adding a component
  means one schema in `catalog.py` and one function in `render.mjs`.
- The model chose the layout only in the order of its calls. It could not
  group the metrics in a row or put the chart first. Step 02 changes that.

## What the next step adds

A catalog of eight components, a JSON Schema built from it, and the model
writing the whole layout as one JSON document that the page renders while
it streams.
