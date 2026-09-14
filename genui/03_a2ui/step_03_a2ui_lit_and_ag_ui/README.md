# Step 03 - The official renderer, over AG-UI

**What this step adds:** two swaps around the same generate loop. The page
renders with `@a2ui/lit`, the official Lit renderer, instead of
`render.mjs`. The messages travel as AG-UI events: every A2UI envelope is
the `value` of a `CUSTOM` event named `a2ui`, encoded by the
`ag-ui-protocol` package's `EventEncoder`, between `RUN_STARTED` and
`RUN_FINISHED`. A click becomes a second AG-UI run whose `forwardedProps`
carry the action and the client's data model.

## Quick demo

```
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
the status Text now reads: Server got 'submit' at 15:04:04 with firstName='Ada', email='ada@example.com', newsletter=True; client data model had 92 bytes
wire of an action run (POST /agent), one AG-UI event per data: line:
  data: {"type":"RUN_STARTED","threadId":"t1","runId":"r2"}
  data: {"type":"CUSTOM","name":"a2ui","value":{"version":"v0.9.1","updateDataModel":{"surfaceId":"main","path":"/form/status","value":"Server
  data: {"type":"RUN_FINISHED","threadId":"t1","runId":"r2","result":{"answered":"submit"}}
screenshot: demo.png
```

![demo](demo.png)

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

The server side of the join: the loop from step 02 yields
`(kind, payload)` pairs, and one function maps them onto AG-UI event
classes. Attempts of the correction loop become `STEP_STARTED` and
`STEP_FINISHED`; the model's prose becomes a text message; the usage rides
in `RUN_FINISHED.result`.

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
The `RunAgentInput` class validates the body; `EventEncoder` writes the
frames.

`server.py`:

```python
def run(agent_input: RunAgentInput):
    """One AG-UI run: route to the action answer or the generate loop."""
    a2ui_props = (agent_input.forwarded_props or {}).get("a2ui") if isinstance(agent_input.forwarded_props, dict) else None
    if a2ui_props and a2ui_props.get("action"):
        return answer_action(a2ui_props["action"], a2ui_props.get("a2uiClientDataModel"))
    user_turns = [m for m in agent_input.messages if m.role == "user"]
    return generate(user_turns[-1].content if user_turns else "")
...
@app.post("/agent")
async def agent_endpoint(request: Request):
    agent_input = RunAgentInput.model_validate(await request.json())
    encoder = EventEncoder(accept=request.headers.get("accept"))
```

The AG-UI client is forty lines with no DOM in them: a frame splitter, the
input shape, and a reader loop. `node --test` covers it with a fake `fetch`.

`src/agui.mjs`:

```js
export function parseSse(buffer) {
  const events = [];
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

```
pip install a2ui-agent-sdk ag-ui-protocol fastapi uvicorn openai jsonschema httpx playwright
npm install              # @a2ui/lit, @a2ui/web_core, @a2ui/markdown-it, @lit/context; esbuild for the build
npm run build            # src/page.mjs -> static/bundle.js (one esbuild command, no config)
python server.py         # then open http://127.0.0.1:8743/ and press Run agent
python demo.py           # builds if needed, a live model call, writes demo.png
python -m pytest test_step.py   # offline; runs npm install, npm test and npm run build when node is on PATH
npm test
```

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
  runs until a `deleteSurface`.

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
  model from `forwardedProps`.
- `envelope.py`, `llm.py`, `prompt.py` unchanged.
