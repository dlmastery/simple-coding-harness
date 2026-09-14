# Step 01 - Static components

**What this step adds:** the smallest generative UI there is. Three components
exist before the model runs: a metric, a table, a chart. The model gets them as
tools. Each tool call becomes one JSON message on a server-sent event stream,
and the page renders it with a hand-written renderer keyed by component name.
No framework, no build step: one FastAPI file, one HTML page, one JS module.

## Quick demo

```bash
python demo.py
```

```text
prompt: show me a dashboard for a lemonade stand
6 SSE messages in 6.0s:
  {"component": "Metric", "props": {"title": "Lemonade Sold", "value": "1,250 cups", "delta": "+15%"}}
  {"component": "Metric", "props": {"title": "Revenue", "value": "$625", "delta": "+10%"}}
  {"component": "Metric", "props": {"title": "Profit", "value": "$200", "delta": "+8%"}}
  {"component": "Table", "props": {"columns": ["Date", "Cups Sold", "Revenue", "Profit"], "rows": [["2024-04-...
  {"component": "Chart", "props": {"kind": "line", "labels": ["Apr 20", "Apr 21", "Apr 22", "Apr 23", "Apr 24...
  {"done": true, "usage": {"prompt_tokens": 249, "completion_tokens": 297}}
saved demo.png
```

![demo](demo.png)

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

`llm.py`: one streamed request, as a generator of events. The model writes
tool calls in order, so a piece with a new index means every earlier call is
complete. That is what lets the page draw the first metric while the chart is
still streaming.

```python
        for piece in delta.tool_calls or []:
            if piece.index not in calls:
                yield from finished(calls)
                calls[piece.index] = {"id": "", "name": "", "arguments": ""}
            call = calls[piece.index]
            if piece.id:
                call["id"] = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call["name"] = function.name
            if function.arguments:
                call["arguments"] += function.arguments

    yield from finished(calls)
    yield {"type": "usage", **usage_from(final_usage)}
```

`server.py`: the SSE stream. One frame per component, a `note` for any prose
the model wrote instead, and `done` with the usage at the end.

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
def run(body: Run):
    frames = (sse(message) for message in components(body.prompt))
    return StreamingResponse(frames, media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
```

`page/render.mjs`: the renderers. Each is a pure function from props to an
HTML string, so `node --test` covers them without a browser. Every prop
passes through `esc` first: the model wrote it, so the page treats it as
text, never as markup.

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
  const renderer = RENDERERS[component];
  if (!renderer) return `<div class="card unknown">unknown component: ${esc(component)}</div>`;
  return renderer(props ?? {});
}
```

`page/app.js`: the SSE reader and the loop. Frames are separated by a blank
line. Each parsed message is appended to the dashboard as soon as it arrives.

```js
  for await (const message of readSSE(response)) {
    events.push(message);
    wire.textContent += JSON.stringify(message) + "\n";
    if (message.component) dashboard.insertAdjacentHTML("beforeend", render(message.component, message.props));
  }
  document.body.dataset.state = "done";
```

## Run it

```bash
python server.py            # http://127.0.0.1:8010
python demo.py              # headless: prints the stream, writes demo.png
python -m pytest test_step.py
npm test                    # the renderer tests alone
```

The key comes from `API_KEY` or `OPENAI_API_KEY`, in the environment or in
`~/.simple-harness/env`. `BASE_URL` and `MODEL` switch to any
OpenAI-compatible endpoint; the default is `gpt-4.1-mini`.

## What to notice

- The model never writes markup. It emits tool calls, and the API validates
  each one against its schema before the server sees it.
- The stream is one JSON object per component. The page has no idea a model
  exists; it renders messages. That is the shape every later step keeps.
- The renderers are three functions and a lookup table. Adding a component
  means one schema in `catalog.py` and one function in `render.mjs`.
- The model chose the layout only in the order of its calls. It could not
  group the metrics in a row or put the chart first. Step 02 changes that.
