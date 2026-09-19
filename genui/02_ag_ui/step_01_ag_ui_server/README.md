# Step 01 - An AG-UI server

**What this step adds:** a FastAPI endpoint that speaks AG-UI. It accepts
a `RunAgentInput`, calls a model, and streams five kinds of event back:
`RUN_STARTED`, `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`,
`TEXT_MESSAGE_END`, `RUN_FINISHED`. A page reads that stream with `fetch`
and renders the text as it arrives. No client library yet: the point is to
see the wire.

## Why: what breaks without it

Sub-theme 01's streams were ad hoc: `{"component"}`, `{"delta"}`,
`{"done"}`, invented per step, readable by that step's page and nothing
else. A second front end, a test harness, a product's existing chat
component: each would need its own parser for each server. A transport
fixes the vocabulary once. With AG-UI, the page in this step is
interchangeable with `@ag-ui/client` (step 03), and the server is
interchangeable with any AG-UI agent.

## Quick demo

```bash
python demo.py
```

```text
POST /agent -> 200 text/event-stream; charset=utf-8
data: {"type":"RUN_STARTED","threadId":"d1eb5e4e-2bdd-4d37-b0ad-75372b0f16ee","runId":"3fbf3573-3624-4d9e-9a41-d863a893af63"}
data: {"type":"TEXT_MESSAGE_START","messageId":"430b77a3-89b1-48c5-82a9-c126864974ac","role":"assistant"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"430b77a3-89b1-48c5-82a9-c126864974ac","delta":"Good"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"430b77a3-89b1-48c5-82a9-c126864974ac","delta":" lemonade"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"430b77a3-89b1-48c5-82a9-c126864974ac","delta":" balances"}
... 14 more TEXT_MESSAGE_CONTENT events ...
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"430b77a3-89b1-48c5-82a9-c126864974ac","delta":"."}
data: {"type":"TEXT_MESSAGE_END","messageId":"430b77a3-89b1-48c5-82a9-c126864974ac"}
data: {"type":"RUN_FINISHED","threadId":"d1eb5e4e-2bdd-4d37-b0ad-75372b0f16ee","runId":"3fbf3573-3624-4d9e-9a41-d863a893af63"}
assembled text: Good lemonade balances fresh lemon juice, water, and just enough sugar for a refreshing taste.
page status: finished; rendered: Good lemonade is made with fresh lemons, the right balance of sweetness, and cold, clean water.
saved demo.png
```

![demo](demo.png)

## Files

```text
step_01_ag_ui_server/
├── server.py         FastAPI app: POST /agent streams the run as text/event-stream, GET / serves the page
├── agent.py          run(): one RunAgentInput in, RUN_STARTED, TEXT_MESSAGE_*, RUN_FINISHED (or RUN_ERROR) out
├── llm.py            one streaming chat completion; settings from the env or ~/.simple-harness/env
├── sse.py            SSE reader in Python, used by the tests and demo.py
├── index.html        the page shell: prompt, rendered chat, the wire panel
├── app.js            hand-written AG-UI client: posts RunAgentInput, renders TEXT_MESSAGE_* events, keeps the history, always ends in a final status
├── sse.mjs           SSE reader for the page: fetch() body stream to JSON events, LF or CRLF
├── sse.test.mjs      node --test for parseBlock and readEvents
├── test_step.py      offline pytest: fake model, event sequence, wire format, endpoint, Python SSE reader
├── demo.py           starts the server, posts one run, prints the wire, drives the page, saves demo.png
├── demo.png          the recorded page
├── package.json      npm test = node --test (no dependencies)
└── README.md         this file
```

## Why a transport

The State of Generative UI report (June 2026) separates two choices. One
is *generation*: what the agent emits. The other is *transport*: where the
UI appears and how events move between agent and page. AG-UI is the
transport for a product you own. Sub-theme 01 sent hand-made JSON over an
ad-hoc SSE stream. AG-UI replaces that with a fixed vocabulary of events,
so any AG-UI client can read any AG-UI agent.

The vocabulary is small. A run starts and finishes. Inside a run, a text
message starts, streams deltas and ends. Later steps add tool calls and
state. Each event is one JSON object with a `type` field and camelCase
keys, sent as one `data:` line of a server-sent event stream.

The request side is one object, `RunAgentInput`: a `threadId`, a `runId`,
the message list so far, the tools the client offers, context, forwarded
props and state. The client owns the history and sends all of it every
run. The server is stateless between runs.

## The code, piece by piece

### 1. The event generator

`agent.py`:

```python
def run(input: RunAgentInput):
    """Yield the events of one run. A model failure becomes RUN_ERROR, not a broken stream."""
    yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
    message_id = str(uuid4())
    try:
        yield TextMessageStartEvent(message_id=message_id, role="assistant")
        for delta in stream_text(to_openai(input.messages)):
            yield TextMessageContentEvent(message_id=message_id, delta=delta)
        yield TextMessageEndEvent(message_id=message_id)
    except Exception as error:  # noqa: BLE001 - the client must see a terminal event
        yield RunErrorEvent(message=str(error))
        return
    yield RunFinishedEvent(thread_id=input.thread_id, run_id=input.run_id)
```

The agent is a Python generator. It yields pydantic event objects from
`ag_ui.core` and never touches HTTP. Every run ends with exactly one
terminal event: `RUN_FINISHED` on success, `RUN_ERROR` when the model call
fails. One `message_id` links start, every delta and end.

### 2. From AG-UI messages to model messages

`agent.py`:

```python
def to_openai(messages):
    """AG-UI messages carry an id and camelCase keys; the model wants role and content."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m.role, "content": m.content} for m in messages if m.role in ("user", "assistant", "system")
    ]
```

AG-UI messages look like OpenAI messages with an `id`. The conversion is
a list comprehension. The system prompt lives on the server; the client
never sends it.

### 3. The model call

`llm.py`:

```python
def stream_text(messages):
    """One streamed chat completion. Yields each text delta as it arrives."""
    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
```

Settings come from `API_KEY`, `BASE_URL` and `MODEL`, read from the
environment or from `~/.simple-harness/env`. The tests replace `client`
with a fake that yields scripted chunks.

### 4. The endpoint

`server.py`:

```python
@app.post("/agent")
def agent_endpoint(input: RunAgentInput, request: Request):
    """Encode every event of the run and stream it as text/event-stream."""
    encoder = EventEncoder(accept=request.headers.get("accept"))
    events = run(input)

    async def stream():
        # The generator runs in a worker thread, one event per pull; when the
        # page has gone it is closed, and the model stream with it.
        try:
            while (event := await run_in_threadpool(next, events, None)) is not None:
                if await request.is_disconnected():
                    break
                yield encoder.encode(event)
        finally:
            events.close()

    return StreamingResponse(stream(), media_type=encoder.get_content_type())
```

FastAPI validates the body against `RunAgentInput`. `EventEncoder` from
`ag_ui.encoder` turns each event into `data: {...}\n\n`, with the field
names in camelCase and optional fields left out. The response is a
`StreamingResponse`, so the first event leaves before the model has
finished. The generator is pulled one event at a time from a worker
thread; when the browser navigates away the endpoint closes it, which
closes the model stream instead of leaving it open until garbage
collection.

### 5. Reading the stream in the page

`sse.mjs`:

```js
export async function* readEvents(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n"); // the spec allows either ending
    let cut;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const event = parseBlock(block);
      if (event) yield event;
    }
  }
  const last = parseBlock(buffer);
  if (last) yield last;
}
```

The browser's `EventSource` only does GET. AG-UI needs a POST with a JSON
body, so the page uses `fetch` and reads the body stream by hand. A chunk
can end in the middle of an event; the buffer holds the remainder until
the next blank line. The reader handles `data:` lines and blank-line
framing with either `\n` or `\r\n`; it ignores `event:` and `id:`
fields, which AG-UI does not use.

### 6. Rendering by event type

`app.js`:

```js
    for await (const event of readEvents(response)) {
      wire.textContent += JSON.stringify(event) + "\n";
      switch (event.type) {
        case "TEXT_MESSAGE_START":
          current = { id: event.messageId, role: event.role, content: "" };
          current.element = addMessage(event.role, "", event.messageId);
          break;
        case "TEXT_MESSAGE_CONTENT":
          if (!current) break; // a delta for a message that never started: this page does not verify order
          current.content += event.delta;
          current.element.textContent = current.content;
          break;
        case "TEXT_MESSAGE_END":
          if (current) messages.push({ id: current.id, role: current.role, content: current.content });
          current = null;
          break;
```

The page keeps `messages`, the AG-UI history. A finished assistant message
joins it, so the next run sends the whole conversation back. The whole
run sits in a `try`: a non-200 answer, a dead server or a stream that ends
without a terminal event all become an `error: ...` status, never a page
stuck on `running`.

## Run it

```bash
pip install ag-ui-protocol fastapi uvicorn openai
python server.py
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."     # or OPENAI_API_KEY=... in ~\.simple-harness\env
python server.py
```

Open http://127.0.0.1:8021, type a question and press Run. The left panel
fills in word by word; the right panel shows every event as it arrived.

Expected output: the status line goes `running` then `finished`; the
wire panel lists `RUN_STARTED`, `TEXT_MESSAGE_START`, one
`TEXT_MESSAGE_CONTENT` per delta, `TEXT_MESSAGE_END`, `RUN_FINISHED`, each
as one line of camelCase JSON. The quick demo above shows the same run
posted with `httpx`, raw.

Tests, offline:

```bash
python -m pytest -q test_step.py
npm test
```

`demo.py` needs `playwright` (`python -m playwright install chromium`)
and `httpx`; it uses the fixed port 8021 and stops with an error if the
port is in use.

## Error handling

- The model call fails (wrong key, wrong URL, model down): the run ends
  with `RUN_ERROR` carrying the exception text, no `RUN_FINISHED`; the
  status line shows `error: ...`.
- The server is down or answers 4xx/5xx (a body that is not a
  `RunAgentInput` is a 422): the page sets `error: 422 ...` itself.
- The stream ends without a terminal event (the server process died
  mid-run): `error: the stream ended without RUN_FINISHED`.
- The browser leaves mid-run: the endpoint closes the generator at the
  next event, and with it the model stream.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- This page does not verify event order; a `TEXT_MESSAGE_CONTENT` before
  its `START` is dropped, nothing more. `@ag-ui/client` in step 03 raises
  on an illegal sequence.
- The server is stateless: the page sends the whole history every run,
  and the server prepends its own system prompt to whatever it gets. A
  client-sent `system` message is kept, after the server's.
- No authentication, one process, 127.0.0.1: a local demo.

## What to notice

- The server never sees the page. It sees `RunAgentInput` and answers with
  events. Any AG-UI client can replace `app.js`.
- The message id is the join key. A client can render several messages in
  flight because each delta names its message.
- The content type is `text/event-stream`, the same SSE the browser
  already knows, but read with `fetch` so the request can carry a body.
- The state field is already in the input. It is empty here; step 02
  fills it.

## What the next step adds

Tool calls as `TOOL_CALL_*` events and shared state as `STATE_SNAPSHOT`
plus `STATE_DELTA` JSON Patches; a client tool the page executes.
