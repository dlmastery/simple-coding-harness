# Step 01 - A2UI messages by hand

<!-- genui-orientation -->
**Lesson 8 of 23.** [Course](../../README.md) · [Theme](../README.md) · [Previous lesson](../../02_ag_ui/step_03_ag_ui_from_the_harness/README.md) · [Next lesson](../step_02_a2ui_from_a_model/README.md)

<!-- /genui-orientation -->

**What this step adds:** the A2UI v0.9.1 protocol with no library on either
side. `a2ui.py` builds the four envelope messages and validates them against
the official JSON schemas. `static/surface.mjs` keeps what a client keeps: a
flat component map and a data model per surface. `static/render.mjs` paints
that state for part of the Basic Catalog. The demo streams the protocol
document's own contact form and renders it.

## Why: what breaks without it

Sub-theme 01 invented its own layout JSON and sub-theme 02 its own
`dashboard` state; each page could read exactly one server. A2UI is the
shared vocabulary for the declarative middle: four envelope messages, a
catalog of components with published JSON schemas, and a data model with
JSON Pointer bindings. With it, a renderer written once (step 03 uses the
official one) draws what any A2UI agent sends, and a message can be
validated before it is drawn. This step writes the messages by hand, so
the shapes are learned before a model writes them in step 02.

## Quick demo

```
python demo.py
```

```text
contact_form.jsonl: 4 messages from the spec's Example Stream
  1 createSurface     valid
  2 updateComponents  INVALID at /updateComponents/components/14/checks/0: 'condition' is a required property
    repair_checks: 3 rules rewritten to {condition, message} -> valid
  3 updateDataModel   valid
  4 deleteSurface     valid
python  after createSurface: surfaces = ['contact_form_1']
python  after updateComponents: root=Card, 25 components, missing refs=[]
python  after updateDataModel: /contact/firstName = 'John', /contact/subscribe = True
python  after deleteSurface: surfaces = []
browser http://127.0.0.1:8741/?all=1
browser after updateDataModel: 8 inputs, first name = 'John', subscribe checked = True
browser click Send Message -> action {"name":"submitContactForm","surfaceId":"contact_form_1","sourceComponentId":"submit_button","timestamp":"2026-09-14T14:45:58.700Z","context":{
browser after deleteSurface: surfaces on page = 0
browser log:
  createSurface: surface contact_form_1
  updateComponents: 25 components, missing refs: 0
  updateDataModel: path /contact
  action {"name":"submitContactForm","surfaceId":"contact_form_1","sourceComponentId":"submit_button","timestamp
screenshot: demo.png
```

![demo](demo.png)

## Files

```text
step_01_a2ui_messages_by_hand/
├── a2ui.py               the four envelope messages, schema validation, JSON Pointer, SurfaceStore (cycle-safe tree)
├── server.py             FastAPI app: GET /stream replays the spec's contact form over SSE
├── contact_form.jsonl    the "Example Stream" from the A2UI v0.9.1 protocol document, unchanged
├── schema/
│   ├── server_to_client.json   the envelope schema (the four messages)
│   ├── common_types.json       shared types: ComponentId, bindings, actions
│   └── catalog.json            the Basic Catalog: every component and function schema
├── static/
│   ├── index.html        the page shell and the styles for the hand renderer
│   ├── app.mjs           reads the SSE stream, feeds the store, repaints after every message; logs a bad message and a reconnect
│   ├── surface.mjs       the DOM-free client state: JSON Pointer (prototype keys refused), Surface, SurfaceStore
│   └── render.mjs        the hand painter for part of the Basic Catalog, keyed by component name; paints a cycle once
├── surface.test.mjs      node --test for surface.mjs
├── test_step.py          offline pytest: builders, validation, surface state, the SSE endpoint, the node tests
├── demo.py               validates the stream, replays it in Python and the browser, saves demo.png
├── demo.png              the recorded page
├── package.json          npm test = node --test (no dependencies)
└── README.md             this file
```

## Why a flat list and a separate data model

A2UI is the declarative middle of the State of Generative UI report's
generation axis: the agent emits a description of the interface, not the
interface itself. Two design choices set it apart from a nested JSON tree.

First, components arrive as a **flat list** joined by ids. `Card` points at
`form_container`; `form_container` lists its children by id. The client
stores every component in a map and rebuilds the tree at render time. So
the server may send components in any order, and a parent may name a child
that has not arrived yet. Sub-theme 01 measured why this streams better than
a nested tree; here it is the protocol's shape.

Second, **structure and data are separate messages**. `updateComponents`
says there is a text field bound to `/contact/email`. `updateDataModel`
says what is at `/contact/email`. Later data updates do not resend the
structure, and an input writes into the same local data model as it is
typed into (two-way binding), which a `Text` bound to the same path sees at
once.

Four messages cover the whole server-to-client protocol: `createSurface`,
`updateComponents`, `updateDataModel`, `deleteSurface`. Everything else is
the catalog.

## The code, piece by piece

The four messages. Each is a JSON object with a `version` and exactly one
of the four keys.

`a2ui.py`:

```python
def create_surface(surface_id, catalog_id=BASIC_CATALOG_ID, theme=None, send_data_model=None):
    """A createSurface message. A surface must exist before anything else targets it."""
    body = {"surfaceId": surface_id, "catalogId": catalog_id}
    if theme is not None:
        body["theme"] = theme
    if send_data_model is not None:
        body["sendDataModel"] = send_data_model
    return {"version": VERSION, "createSurface": body}


def update_components(surface_id, components):
    """An updateComponents message: a flat list; one component must have id 'root'."""
    return {"version": VERSION, "updateComponents": {"surfaceId": surface_id, "components": list(components)}}


def update_data_model(surface_id, path="/", value=None, remove=False):
    """An updateDataModel message. Omit value (remove=True) to delete the key at path."""
    body = {"surfaceId": surface_id, "path": path}
    if not remove:
        body["value"] = value
    return {"version": VERSION, "updateDataModel": body}
```

Validation uses the three official schemas in `schema/`. The envelope
schema refers to a placeholder file named catalog.json; the registry maps
that name to the Basic Catalog, which is how the spec says a validator plugs
any catalog in.

`a2ui.py`:

```python
        envelope = load_schema("server_to_client.json")
        common = load_schema("common_types.json")
        catalog = load_schema("catalog.json")
        placeholder = envelope["$id"].rsplit("/", 1)[0] + "/catalog.json"
        registry = Registry().with_resources([
            (envelope["$id"], Resource.from_contents(envelope)),
            (common["$id"], Resource.from_contents(common)),
            (catalog["$id"], Resource.from_contents(catalog)),
            (placeholder, Resource.from_contents(catalog)),
        ])
```

Errors come back in the spec's standard shape, so a later step can hand
them to a model. The envelope's `anyComponent` is a `oneOf` over every
catalog entry and only says "not valid under any schema"; the entry named
by the component's own `component` field says what is wrong.

`a2ui.py`:

```python
def validate(message):
    """The spec's standard error shape ({code, surfaceId, path, message}) or None when valid."""
    from jsonschema.exceptions import best_match

    error = best_match(schemas()["envelope"].iter_errors(message))
    if error is None:
        return None
    body = message.get(message_type(message) or "", {})
    surface_id = body.get("surfaceId", "") if isinstance(body, dict) else ""
    path, text = list(error.absolute_path), error.message
    if path[:2] == ["updateComponents", "components"] and len(path) == 3:
        inner_path, inner_text = component_error(body["components"][path[2]])
        path, text = path + inner_path, inner_text or text
    return {"code": "VALIDATION_FAILED", "surfaceId": surface_id, "path": "/" + "/".join(str(p) for p in path), "message": text[:200]}
```

The client state, with no DOM in it. A surface is a component map plus a
data model; `tree()` rebuilds the nested view and marks ids that have not
arrived, and an id that names itself as a descendant (which a model can
write in step 02) comes back as `{cycle: true}` instead of a stack
overflow.

`static/surface.mjs`:

```js
  apply(message) {
    const kind = messageType(message);
    const body = message[kind];
    if (kind === 'updateComponents') {
      for (const component of body.components) this.components.set(component.id, component);
    } else if (kind === 'updateDataModel') {
      if ('value' in body) pointerSet(this.data, body.path ?? '/', body.value);
      else pointerDelete(this.data, body.path ?? '/');
    } else {
      throw new Error(`${kind} is not a surface update`);
    }
  }
...
  tree(id = 'root', ancestors = new Set()) {
    const component = this.components.get(id);
    if (!component) return { id, missing: true };
    if (ancestors.has(id)) return { id, cycle: true };
    const inner = new Set(ancestors).add(id);
    return { id, component: component.component, children: this.childIds(component).map((c) => this.tree(c, inner)) };
  }
```

The data model is written through JSON Pointer, and the path comes from
the wire. `pointerTokens` refuses `__proto__`, `constructor` and
`prototype` (through `pointerSet` they would reach `Object.prototype`),
`pointerGet` reads own properties only, and a list index must be digits.
`a2ui.py` gives the same verdicts. One deliberate deviation from RFC
6902's `remove`: deleting a list element with `updateDataModel` leaves a
hole (`undefined` / `None`) rather than shifting the rest, so bound paths
such as `/tags/1` keep pointing at the same item.

The store treats a repeated `createSurface` for an existing id as a
reset: the old surface goes, a fresh one takes its place. That is what
makes an `EventSource` reconnect harmless (the server replays from the
start). The official `MessageProcessor` in step 03 throws on it instead,
so a server that wants to start over sends `deleteSurface` first; steps
02 and 03 do.

A bound value is resolved at render time; on a click, the action's context
is resolved at that moment. Function calls such as `formatDate` are not
evaluated by this renderer; the official one in step 03 brings them.

`static/surface.mjs`:

```js
  resolve(value) {
    if (value && typeof value === 'object' && 'path' in value) return pointerGet(this.data, value.path);
    if (value && typeof value === 'object' && 'call' in value) return undefined;
    return value;
  }
...
  action(componentId, timestamp = new Date().toISOString()) {
    const event = this.components.get(componentId)?.action?.event ?? {};
    const context = {};
    for (const [key, value] of Object.entries(event.context ?? {})) context[key] = this.resolve(value) ?? null;
    return { name: event.name, surfaceId: this.id, sourceComponentId: componentId, timestamp, context };
  }
```

The painter is a map from component name to a function. `TextField` shows
the two-way binding: the input reads its value from the data model and
writes every keystroke back to the bound path. A child id with no component
yet paints a placeholder.

`static/render.mjs`:

```js
  TextField(ctx, c) {
    const input = el('input', 'a2ui-input');
    input.type = c.variant === 'obscured' ? 'password' : c.variant === 'number' ? 'number' : 'text';
    input.placeholder = text(ctx.surface, c.label);
    input.value = text(ctx.surface, c.value);
    input.dataset.field = c.id;
    if (c.value?.path) input.oninput = () => ctx.write(c.value.path, input.value);
    return el('label', 'a2ui-field', el('span', 'a2ui-label', text(ctx.surface, c.label)), input);
  },
...
    paint(id) {
      if (id == null) return null;
      const component = surface.components.get(id);
      if (!component) return el('span', 'a2ui-placeholder', `waiting for ${id}`);
      if (ctx.painting.has(id)) return el('span', 'a2ui-placeholder', `cycle at ${id}`);
```

`paint` rebuilds the whole DOM on every message and on every keystroke
(`onChange`), then restores focus and caret on the input being edited by
its `data-field`. That is the cost of having no diffing: a checkbox or
radio loses focus when a bound `Text` elsewhere repaints.

The server replays the spec's stream as server-sent events, one envelope
per `data:` line. A2UI does not pick a transport; it asks for ordered
delivery and message framing, and SSE gives both.

`server.py`:

```python
@app.get("/stream")
async def stream(all: bool = False):
    """createSurface, updateComponents, updateDataModel; with ?all=1 the deleteSurface too."""
    messages = contact_form_messages()
    if not all:
        messages = [m for m in messages if a2ui.message_type(m) != "deleteSurface"]

    async def body():
        for index, message in enumerate(messages):
            if index:
                await asyncio.sleep(GAP * (4 if a2ui.message_type(message) == "deleteSurface" else 1))
            yield sse(message)
        yield sse({"count": len(messages)}, event="done")

    return StreamingResponse(body(), media_type="text/event-stream")
```

## Run it

```bash
pip install fastapi uvicorn jsonschema playwright   # playwright: also `playwright install chromium`
python server.py          # then open http://127.0.0.1:8741/
python demo.py            # validates, replays, screenshots demo.png
python -m pytest test_step.py
npm test                  # node --test on static/surface.mjs; no install needed
```

PowerShell:

```powershell
pip install fastapi uvicorn jsonschema playwright
python -m playwright install chromium
python server.py
python demo.py
python -m pytest test_step.py
npm test
```

`jsonschema` 4.18 or newer is needed: the validator imports `referencing`
(the registry in the snippet above), which ships with it. No model key:
this step calls no model.

Expected output: the page shows the contact form building up, one
message every 0.6 s: an empty card ("waiting for root"), then the form,
then the fields fill with John Doe's details. Typing in a field updates
the data model line in the log; clicking Send Message logs the action
with the context resolved. With `?all=1` the surface disappears again
after the `deleteSurface`. The quick demo above is the same run, driven
headlessly, with the Python replay first.

`contact_form.jsonl` is the "Example Stream" from the A2UI v0.9.1 protocol
document, unchanged. `schema/` holds the three schema files the
`a2ui-agent-sdk` package bundles for v0.9.1 (Apache-2.0); their `$id`s still
say `v0_9`, and the envelope accepts both `v0.9` and `v0.9.1` as `version`.

## Error handling

- A message in `contact_form.jsonl` that does not validate after
  `repair_checks`: `/stream` raises before the first frame, so the page
  gets a 500 and logs `stream error: reconnecting` (EventSource retries;
  the error is in the server's terminal).
- A message the store refuses (an update for a surface never created, a
  path with a prototype key, a component inside itself): the page logs
  `bad message: ...` or paints `cycle at <id>` and goes on with the next
  message.
- The server drops mid-stream: `EventSource` reconnects and the server
  replays from the first message; the repeated `createSurface` resets the
  surface, so the page ends up where a fresh load would.
- `demo.py` with port 8741 in use (a `python server.py` still running):
  `RuntimeError: the server did not start on port 8741 (in use?)`.
- Leave `python server.py` with ctrl-c.

## Gotchas / what this is not

- The renderer covers ten of the Basic Catalog's components and no
  catalog functions (`formatDate` and friends resolve to `null`); the
  official renderer in step 03 covers all of it.
- `deleteSurface` on a list element keeps the list's length (see above).
- Fixed port 8741; `server.py` and `demo.py` cannot run at the same time.
- Nothing here talks to a model or to a server beyond the replay; the
  client-to-server half (`action`, `sendDataModel`) is logged, not sent,
  until step 02.

## What to notice

- The spec's own example does not pass the spec's own schema. Its
  `TextField` checks are written `{"call": "required", "args": ..., "message": ...}`;
  the schema's `CheckRule` requires `{"condition": {"call": ..., "args": ...}, "message": ...}`,
  the shape the document's `Button` example uses. `repair_checks` rewrites
  three rules and the message validates. Validate before rendering, and
  expect the validator to disagree with prose.
- The error path is a JSON Pointer into the message
  (`/updateComponents/components/14/checks/0`). That is the format the spec
  asks a client to send back so a model can correct itself; step 02 uses it.
- The renderer never sees a tree on the wire. `tree()` is computed from the
  map at paint time, so `missing refs: 0` is a fact about the map, and a
  child that arrives later fills its placeholder on the next paint.
- Typing into a field changes the local data model only. Nothing reaches
  the server until a `Button` action, whose `context` is resolved at click
  time. In the log the action carries `isNewsletterSubscribed: true` read
  from `/contact/subscribe`, and `clientTime: null` because this renderer
  does not run catalog functions.
- `deleteSurface` removes the surface and its state. The page keeps
  nothing else; the server owns the conversation.

## What the next step adds

A model writes the messages: a prompt built from the catalog schema, the
reply validated with this step's `validate` and sent back to the model
when it fails, and the page's `action` posted to a server that answers
with another surface.
