# Step 03 - The official renderer, over AG-UI

**What this step adds:** two swaps around the same generate loop. The page
renders with `@a2ui/lit`, the official Lit renderer, instead of
`render.mjs`. The messages travel as AG-UI events: every A2UI envelope is
the `value` of a `CUSTOM` event named `a2ui`, encoded by the
`ag-ui-protocol` package's `EventEncoder`, between `RUN_STARTED` and
`RUN_FINISHED`. A click becomes a second AG-UI run whose `forwardedProps`
carry the action and the client's data model.

## Why: what breaks without it

Step 02 proved the loop against a hand-written renderer for part of the
catalog and a hand-written SSE reader. Neither is the thing a product
ships: the official renderer runs the catalog functions, renders markdown
and keeps a data model that typing writes into; and a product already has
a transport with runs, threads and a terminal event. Bolting A2UI onto
that transport by hand (a second endpoint, a second reader) is how the
two protocols drift apart. This step shows the join is one event type,
so that neither side has to change: an A2UI server that speaks AG-UI is
the same generate loop with a different encoder.

## Quick demo

```bash
npm install && npm run build
python demo.py
```

```text
browser http://127.0.0.1:8743/  (renderer: @a2ui/lit 0.11.0 over @a2ui/web_core; transport: AG-UI CUSTOM events named a2ui)
  1.63s POST /agent run with 1 message(s)
  1.67s RUN_STARTED ""
  1.69s STEP_STARTED "attempt 1"
  7.19s CUSTOM a2ui createSurface
  7.95s CUSTOM a2ui updateComponents (2 components)
  8.44s CUSTOM a2ui updateComponents (3 components)
  ... 51 more CUSTOM a2ui updateComponents ...
  15.63s CUSTOM a2ui updateComponents (10 components)
  15.64s CUSTOM a2ui updateDataModel
  15.64s STEP_FINISHED "attempt 1"
  15.64s RUN_FINISHED {"attempt":1,"usage":{"prompt_tokens":9929,"completion_tokens":686},"reply_chars":2663}
typed: data model = {"form": {"firstName": "Ada", "email": "ada@example.com", "newsletter": true, "status": ""}}
click -> 15.78s action submit from sendButton {"firstName":"Ada","email":"ada@example.com","newsletter":true}
        15.81s RUN_FINISHED {"answered":"submit"}
the status Text now reads: Server got 'submit' at 15:04:04 with firstName='Ada', email='ada@example.com', newsletter=True; the client data model says {"form": {"firstName": "Ada", "email": "ada@example.com", "newsletter": true, "status": ""}}
wire of an action run (POST /agent), one AG-UI event per data: line:
  data: {"type":"RUN_STARTED","threadId":"t1","runId":"r2"}
  data: {"type":"CUSTOM","name":"a2ui","value":{"version":"v0.9.1","updateDataModel":{"surfaceId":"main","path":"/form/status","value":"Server
  data: {"type":"RUN_FINISHED","threadId":"t1","runId":"r2","result":{"answered":"submit"}}
screenshot: demo.png
```

![demo](demo.png)

## Files

```text
step_03_a2ui_lit_and_ag_ui/
├── envelope.py           the four messages, validation, SurfaceStore; unchanged from step 02
├── llm.py                model access; unchanged from step 02
├── prompt.py             the a2ui-agent-sdk prompt and parsers; unchanged from step 02
├── server.py             FastAPI app: POST /agent takes a RunAgentInput and streams AG-UI events via EventEncoder; keepalives; the mirror reset per generation
├── schema/
│   ├── server_to_client.json   the envelope schema (the four messages)
│   ├── common_types.json       shared types: ComponentId, bindings, actions
│   └── catalog.json            the Basic Catalog: every component and function schema
├── src/
│   ├── page.mjs          the official @a2ui/lit renderer fed by AG-UI events; the CUSTOM a2ui join; one run at a time
│   └── agui.mjs          a small AG-UI client: SSE frame parser (LF or CRLF, comments skipped), RunAgentInput shape, reader loop
├── static/
│   └── index.html        the page shell; loads bundle.js, which npm run build writes here
├── agui.test.mjs         node --test for agui.mjs and @a2ui/web_core's MessageProcessor without a DOM
├── test_step.py          offline pytest: scripted reply, AG-UI wire decoded with the event classes, npm tests and build
├── demo.py               builds if the bundle is missing or older than src/, a live model call, typing, a click, the raw wire; saves demo.png
├── demo.png              the recorded page
├── package.json          @a2ui/lit, @a2ui/web_core, @a2ui/markdown-it, @lit/context; esbuild for the build
├── package-lock.json     pinned npm dependency tree
├── .gitignore            node_modules/ and static/bundle.js
└── README.md             this file
```

## A2UI over AG-UI over A2A: where each layer stops

The State of Generative UI report separates two choices: the transport
(where the UI appears) and the generation format (what the agent emits).
This step is the two choices side by side. AG-UI is the transport: a run
with a thread id, ordered events on one stream, and `forwardedProps` for
anything the application needs to carry. A2UI is the generation format: the
four envelope messages and the catalog. AG-UI does not know what a surface
is; A2UI does not know what a run is. The join is one line: a `CUSTOM` event
named `a2ui` whose value is one envelope.

The report describes the same stack with A2A underneath: A2UI messages as
parts of A2A messages between agents, AG-UI between the agent and the
browser. Each layer stops where its vocabulary ends. A2A moves messages
between agents and knows nothing about runs in a browser. AG-UI moves runs
to a browser and knows nothing about components. A2UI names components and
knows nothing about who delivered them. This step has no second agent, so
A2A is not on the wire; its slot is where `run()` reads the last user
message.

## The code, piece by piece

The renderer. `@a2ui/lit` is a thin package: it exports the `A2uiSurface`
element, `basicCatalog`, `A2uiLitElement`, `A2uiController` and `Context`.
The state machine, `MessageProcessor`, and the Lit components of the Basic
Catalog live in `@a2ui/web_core`. The processor looks catalogs up by id when
a `createSurface` arrives, and the Lit catalog registers itself under the
`v0_9` id, so the spec's `v0_9_1` id gets an alias.

`src/page.mjs`:

```js
import { MessageProcessor, Catalog } from '@a2ui/web_core/v0_9';
import { injectBasicCatalogStyles } from '@a2ui/web_core/v0_9/basic_catalog';
import { A2uiSurface, basicCatalog, Context } from '@a2ui/lit/v0_9';
import { ContextProvider } from '@lit/context';
import { renderMarkdown } from '@a2ui/markdown-it';
...
const V0_9_1 = 'https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json';
const alias = new Catalog(V0_9_1, [...basicCatalog.components.values()], [...basicCatalog.functions.values()]);
const processor = new MessageProcessor([basicCatalog, alias], onAction);
injectBasicCatalogStyles();
new ContextProvider(app, { context: Context.markdown, initialValue: renderMarkdown }); // Text renders markdown
processor.onSurfaceCreated((surface) => {
  const element = new A2uiSurface();
  element.surface = surface;
  element.id = `surface-${surface.id}`;
  app.append(element);
});
```

The join between the two protocols, on the page: one `case` in the event
switch.

`src/page.mjs`:

```js
function onEvent(event) {
  switch (event.type) {
    case 'CUSTOM':
      if (event.name === 'a2ui') {
        processor.processMessages([event.value]);
```

The action. The official renderer resolves the `Button`'s context from its
data model and hands the processor's action handler the spec's
client-to-server `action` message. AG-UI has no message type for it, so it
goes into `forwardedProps`, with the client data model alongside, which is
what `sendDataModel` in the spec asks a transport to carry as metadata.

`src/page.mjs`:

```js
function onAction(action) {
  note(`action ${action.name} from ${action.sourceComponentId} ${JSON.stringify(action.context)}`);
  const dataModel = processor.getClientDataModel('v0.9.1') ?? { version: 'v0.9.1', surfaces: {} };
  run(history, { a2ui: { action, a2uiClientDataModel: dataModel } });
}
```

One run at a time, and a run always ends. The button is disabled and a
click on the surface is ignored (logged) while a run is open; whatever
the run does, `window.a2uiDone` flips in a `finally`, so the demo and a
test never wait on a page that broke.

`src/page.mjs`:

```js
let running = false;
async function run(messages, forwardedProps = {}) {
  window.a2uiDone = false;
  running = true;
  form.elements.go.disabled = true;
  let ended = false;
  try {
    await runAgent('/agent', runAgentInput({ threadId: THREAD, messages, forwardedProps }), (event) => {
      ended ||= event.type === 'RUN_FINISHED' || event.type === 'RUN_ERROR';
      onEvent(event);
    });
    if (!ended) note('the stream ended without RUN_FINISHED or RUN_ERROR');
  } catch (error) {
    note(`run failed: ${error.message}`);
  } finally {
    running = false;
    form.elements.go.disabled = false;
    window.a2uiDone = true;
  }
}
```

The server side of the join: the loop from step 02 yields
`(kind, payload)` pairs, and one function maps them onto AG-UI event
classes. Attempts of the correction loop become `STEP_STARTED` and
`STEP_FINISHED`; the model's prose becomes one text message, sent after
the reply is complete (the loop only knows the prose once the full parser
has separated it from the `<a2ui-json>` blocks, so it is not streamed);
the usage rides in `RUN_FINISHED.result`.

`server.py`:

```python
def to_events(agent_input, pairs):
    """Map the loop's (kind, payload) pairs onto AG-UI event objects."""
    ids = dict(thread_id=agent_input.thread_id, run_id=agent_input.run_id)
    yield RunStartedEvent(**ids)
    for kind, payload in pairs:
        if kind is None:
            yield CustomEvent(name="a2ui", value=payload)
        elif kind == "note":
            yield CustomEvent(name="a2ui.note", value=payload)
        elif kind == "step":
            step = StepStartedEvent if payload["started"] else StepFinishedEvent
            yield step(step_name=f"attempt {payload['attempt']}")
        elif kind == "text":
            message_id = f"{agent_input.run_id}-text"
            yield TextMessageStartEvent(message_id=message_id)
            yield TextMessageContentEvent(message_id=message_id, delta=payload)
            yield TextMessageEndEvent(message_id=message_id)
        elif kind == "error":
            yield RunErrorEvent(message=payload)
            return
        elif kind == "done":
            yield RunFinishedEvent(**ids, result=payload)
            return
    yield RunFinishedEvent(**ids)
```

Routing a run: an action in `forwardedProps` is answered without a model
call; anything else is the last user message through the generate loop.
The page sends the whole thread (`history` grows with every prompt), and
the server carries it but reads only the last user message: a chat
history is AG-UI's unit, and this loop generates from one prompt. FastAPI
validates the body against the `RunAgentInput` class, so a bad body is a
`422` with the field named, never a run; `EventEncoder` writes the frames.

`server.py`:

```python
def run(agent_input: RunAgentInput):
    """One AG-UI run: route to the action answer or the generate loop.
    The page sends the whole thread; the loop reads only the last user message."""
    a2ui_props = (agent_input.forwarded_props or {}).get("a2ui") if isinstance(agent_input.forwarded_props, dict) else None
    if a2ui_props and a2ui_props.get("action"):
        return answer_action(a2ui_props["action"], a2ui_props.get("a2uiClientDataModel"))
    user_turns = [m for m in agent_input.messages if m.role == "user"]
    return generate(user_turns[-1].content if user_turns else "")
...
@app.post("/agent")
async def agent_endpoint(agent_input: RunAgentInput, request: Request):
    """The body is validated by FastAPI (a bad one is a 422, not a 500); the events stream as SSE."""
    encoder = EventEncoder(accept=request.headers.get("accept"))
```

A second run on the same page. The official `MessageProcessor` throws
`Surface main already exists.` on a repeated `createSurface` (step 01's
hand store treated it as a reset), so every generation withdraws the
previous surfaces first, on the wire and in the mirror; the page's
`onSurfaceDeleted` removes the old element. A generate run's events, in
order:

```text
RUN_STARTED
CUSTOM a2ui deleteSurface            (only when a surface from an earlier run exists)
STEP_STARTED "attempt 1"
CUSTOM a2ui createSurface            (sendDataModel: true, set by the server)
CUSTOM a2ui updateComponents  x N    (one per repaint of the stream parser)
CUSTOM a2ui.note {...}               (streaming_stopped, a validation warning; only when there is one)
CUSTOM a2ui updateComponents         (the final, validated structure)
CUSTOM a2ui updateDataModel          (the data model, sent by the final pass only)
TEXT_MESSAGE_START / CONTENT / END   (the prose, after the reply)
STEP_FINISHED "attempt 1"
RUN_FINISHED {"attempt": 1, "usage": {...}, "reply_chars": ...}
```

A failed attempt ends its step with `CUSTOM a2ui.note {"error": ...}`,
a `deleteSurface` for what it created, `STEP_FINISHED`, then
`STEP_STARTED "attempt 2"`; two failures end in `RUN_ERROR`. An action
run is three events: `RUN_STARTED`, one `CUSTOM a2ui` with an
`updateDataModel`, `RUN_FINISHED {"answered": "submit"}`.

`server.py`:

```python
def generate(user_prompt):
    """Yield (event, payload) pairs: the progressive messages, then the final ones."""
    for surface_id in list(STORE.surfaces):
        yield mirror(envelope.delete_surface(surface_id))  # the previous generation goes first
```

The answer to a click reads two things: the `context` the model bound on
the `Button` (what step 02 already had) and the client data model that
`sendDataModel` made the page send, which holds every field the user
typed, bound or not. The status line echoes both, so the second source is
demonstrated rather than measured.

`server.py`:

```python
    typed = (client_data_model or {}).get("surfaces", {}).get(action["surfaceId"], {})
    fields = ", ".join(f"{key}={value!r}" for key, value in action.get("context", {}).items())
    when = datetime.now(timezone.utc).strftime("%H:%M:%S")
    # the context carries what the Button bound; the data model carries every field the user typed
    text = f"Server got '{action['name']}' at {when} with {fields}; the client data model says {json.dumps(typed)[:200]}"
```

While the model thinks (five to ten seconds of silence in the recorded
run) the stream carries an SSE comment, `: keepalive`, every 15 s, so a
proxy does not drop it; the client skips frames without a `data:` line,
and the comment is only written when the client asked for
`text/event-stream` (it means nothing in protobuf).

The AG-UI client is forty lines with no DOM in them: a frame splitter, the
input shape, and a reader loop that rejects on a non-2xx answer (a `422`
has no frames, so its body is the only explanation). `node --test` covers
it with a fake `fetch`.

`src/agui.mjs`:

```js
export function parseSse(buffer) {
  const events = [];
  buffer = buffer.replaceAll('\r\n', '\n');
  let end;
  while ((end = buffer.indexOf('\n\n')) >= 0) {
    const frame = buffer.slice(0, end);
    buffer = buffer.slice(end + 2);
    const data = frame.split('\n').filter((l) => l.startsWith('data: ')).map((l) => l.slice(6)).join('\n');
    if (data) events.push(JSON.parse(data));
  }
  return { events, rest: buffer };
}
...
export function runAgentInput({ threadId, messages, forwardedProps = {} }) {
  return { threadId, runId: newId('run'), state: {}, messages, tools: [], context: [], forwardedProps };
}
```

## Run it

```bash
pip install a2ui-agent-sdk==0.6.0 ag-ui-protocol fastapi uvicorn openai jsonschema httpx playwright
npm install              # @a2ui/lit, @a2ui/web_core, @a2ui/markdown-it, @lit/context; esbuild for the build
npm run build            # src/page.mjs -> static/bundle.js (one esbuild command, no config)
python server.py         # then open http://127.0.0.1:8743/ and press Run agent
python demo.py           # builds if the bundle is missing or stale, a live model call, writes demo.png
python -m pytest test_step.py   # offline; runs npm install, npm test, and npm run build when the bundle is stale
npm test
```

PowerShell:

```powershell
$env:API_KEY = "sk-..."     # or API_KEY=... in ~\.simple-harness\env
pip install a2ui-agent-sdk==0.6.0 ag-ui-protocol fastapi uvicorn openai jsonschema httpx playwright
python -m playwright install chromium
npm install; npm run build
python server.py
python demo.py
python -m pytest test_step.py
npm test
```

Expected output: the page shows the form's card within about six
seconds, then fields, labels and the button fill in while the log lists
one `CUSTOM a2ui updateComponents` per repaint; the fields get their
values with the final `updateDataModel`, the prose appears under the
form, then `STEP_FINISHED` and `RUN_FINISHED {...usage...}`. Typing and
clicking Send logs `action submit from ...`, a three-event run, and the
status line under the form reads `Server got 'submit' at ... the client
data model says {...}`. The quick demo above is the same run, driven
headlessly, plus the raw frames of an action run.

A build step is needed here, and only here in this sub-theme. `@a2ui/lit`
imports `lit`, `zod`, `@lit/context`, `@preact/signals-core`, `date-fns`,
`markdown-it` and `dompurify` by bare specifier from fifteen packages; a
browser cannot resolve those without an import map covering every file, so
one `esbuild` call bundles them into `static/bundle.js` (about 750 KB, not
committed).

What was used from each package:

- `@a2ui/lit` 0.11.0: `A2uiSurface`, `basicCatalog`, `Context`. Its root
  entry still exports the v0.8 API; the v0.9 one is `@a2ui/lit/v0_9`.
- `@a2ui/web_core` 0.11.0: `MessageProcessor`, `Catalog`,
  `injectBasicCatalogStyles`; the Lit components themselves are defined
  here, and `@a2ui/lit`'s `basicCatalog` only lists them. `MessageProcessor`
  runs under Node with no DOM, which the node tests use.
- `@a2ui/markdown-it` 0.1.2: `renderMarkdown`, injected through
  `@lit/context` so `Text` renders `# Contact Us` as a heading. Without it
  the component logs a warning and shows the raw text.
- `@a2ui/react` 0.11.1: inspected, not used. Its root entry is also v0.8;
  `@a2ui/react/v0_9` exports `A2uiSurface`, `basicCatalog` and the
  components as React function components with `MarkdownContext`. It is
  the same `@a2ui/web_core` underneath.
- `ag-ui-protocol` 0.1.22 (Python): `RunAgentInput`, the event classes,
  `EventEncoder`.
- `a2ui-agent-sdk` 0.6.0 and `a2ui-core` 0.1.1 (Python): as in step 02.
  `a2ui-core` also has a `MessageProcessor` (a server-side mirror like
  `envelope.SurfaceStore`); its strict mode accepts `"version": "v0.9"`
  only, so it was not used here.

## Error handling

- No key, or the model call fails: `RUN_STARTED`, `STEP_STARTED`, then
  `RUN_ERROR {"message": "AuthenticationError: ..."}`; the page logs it,
  nothing is drawn, `a2uiDone` flips, the button comes back.
- The reply fails validation: `CUSTOM a2ui.note {"error": ...}`, the
  partial surface is withdrawn with `deleteSurface`, `STEP_FINISHED`, and
  a second attempt; a second failure is
  `RUN_ERROR "gave up after the correction attempt"` and an empty page.
- The stream parser hits something it cannot heal (a trailing comma):
  `CUSTOM a2ui.note {"streaming_stopped": ...}`; the page keeps what it
  has, the final pass sends the repaired messages.
- The model is silent for 15 s: a `: keepalive` comment, skipped by the
  client.
- A body that is not a `RunAgentInput` (a missing `messages`, a non-JSON
  body): `422` from FastAPI; the page logs `run failed: 422 ...`.
- The server is down, or the stream is cut: `run failed: ...`, or
  `the stream ended without RUN_FINISHED or RUN_ERROR` when the headers
  arrived but the terminal event did not. `a2uiDone` is set either way,
  so `demo.py` stops instead of waiting two minutes, and exits with the
  last log lines when no `RUN_FINISHED` was seen.
- A message the official processor refuses (an unknown catalog id, a
  component outside the catalog): `processMessages` throws inside
  `onEvent`, the rest of that stream is not read, `run failed: ...` is
  logged; the next run starts with a `deleteSurface`.
- `demo.py` raises `RuntimeError` when uvicorn cannot bind port 8743
  (another `server.py` still running) instead of waiting forever.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- One page per process: `STORE` is a global, not keyed by `threadId`
  although every run carries one; two tabs would answer each other's
  clicks. A product keys the mirror by thread.
- `history` is sent in full and only the last user message is read; the
  thread is carried, not used.
- The prose is one text message after the reply, not streamed.
- The `sendDataModel` round trip is shown by echoing the typed fields into
  the status line; a real server would validate them and act (save,
  send, fetch).
- A click during a run is ignored, and Run agent is disabled until the
  run ends.
- Fields are empty until the final pass sends `updateDataModel` (the
  streaming pass skips it, as in step 02).
- The bundle is not committed; `demo.py` and `test_step.py` rebuild it
  when `src/*.mjs` is newer than `static/bundle.js`, so `npm` must be on
  PATH the first time and after every page change.
- Fixed port 8743; no authentication; the prompt goes to the model as
  typed.

## What to notice

- The wire of an action run is three lines: `RUN_STARTED`, one `CUSTOM`
  `a2ui` event with an `updateDataModel`, `RUN_FINISHED`. Nothing in AG-UI
  had to change to carry A2UI, and nothing in A2UI had to change to ride
  AG-UI.
- The official renderer does what step 01's did not: the catalog functions
  run (`BASIC_FUNCTIONS` in `@a2ui/web_core` implements `required`,
  `email`, `formatDate` and the rest), `Text` renders markdown, and typing
  writes into `web_core`'s `DataModel` so `getClientDataModel()` returns
  `{version, surfaces: {main: {...}}}` for the next run.
- Over fifty `updateComponents` events for one form: the SDK's stream parser
  re-sends reachable components as strings heal. The Lit renderer absorbs
  them because `MessageProcessor` updates a component in place and the
  elements re-render from signals; nothing is torn down.
- `sendDataModel` is set by the server on the way out, not by the model.
  The server owns the surface, so it decides whether it wants the data
  model back; the mirror is then a convenience, not a requirement.
- The thread is one `threadId` for the page and a new `runId` per
  generation or click. That is the AG-UI unit; an A2UI surface lives across
  runs until a `deleteSurface`, which is why a new generation sends one
  first.

## What the next sub-theme adds

Sub-theme 04 swaps the format: OpenUI Lang, a line-oriented language
(`id = Component(args)`) that a renderer can draw one line at a time and
that the report measures as the most token-efficient of the open formats;
the same transport ideas hold, the messages get smaller.

## Diff from the previous step

- `static/surface.mjs`, `static/render.mjs`, `static/app.mjs` removed;
  `src/page.mjs` (the Lit renderer and the event switch) and `src/agui.mjs`
  (the AG-UI client) replace them, bundled by `npm run build` into
  `static/bundle.js`.
- `package.json` gains pinned dependencies and a `build` script;
  `agui.test.mjs` replaces `surface.test.mjs`.
- `server.py`: `POST /generate` and `POST /action` replaced by
  `POST /agent` (`RunAgentInput` in, AG-UI events out); the generate loop
  yields `step`, `text`, `done` and `error` kinds that `to_events` maps;
  `mirror` sets `sendDataModel`; `answer_action` reads the client data
  model from `forwardedProps` and echoes it. The reset per generation,
  the keepalive and the one-run-at-a-time page are step 02's, kept.
- `envelope.py`, `llm.py`, `prompt.py` unchanged.
