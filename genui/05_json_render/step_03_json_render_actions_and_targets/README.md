# Step 03 - Actions, and a second target

<!-- genui-orientation -->
**Lesson 17 of 23.** [Course](../../README.md) · [Theme](../README.md) · [Previous lesson](../step_02_json_render_streaming_patches/README.md) · [Next lesson](../../06_mcp_apps/step_01_mcp_app_resource/README.md)

<!-- /genui-orientation -->

**What this step adds:** two things the flat element map makes cheap. First,
actions: a `Button` component and two catalog actions (`refresh_numbers`,
`show_details`). The library handles the built-in `setState` inside the page;
the catalog actions go to the server (`POST /action`), which runs one more
model turn on the same transcript, and the model answers with patches that
edit the spec already on screen. Second, a second renderer: the same
catalog and the same spec drawn in the terminal by `@json-render/ink`
(`ink_render.mjs`), no browser involved.

## Quick demo

```
python demo.py
```

```text
page: complete at 17.59 s, 34 patches
3 buttons, 4 cards visible
press 'Refresh Numbers':
  refresh_numbers {} -> server
  refresh_numbers: 12 patches applied in 4.48 s
  4 cards visible
press 'Show Details':
  show_details {"metric":"This Week's Sales"} -> server
  show_details: 2 patches applied in 1.91 s
  5 cards visible
press 'Hide Notes':
  setState /showNotes = false (handled in the page)
  4 cards visible
turn generate: 34 patches in 17.56 s, 1228 completion tokens
turn refresh_numbers: 12 patches in 4.45 s, 282 completion tokens
  {"op": "replace", "path": "/state/sales/thisWeekTotal", "value": "$270"}
  {"op": "replace", "path": "/state/sales/dailySales/0", "value": 22}
turn show_details: 2 patches in 1.89 s, 79 completion tokens
  {"op": "replace", "path": "/state/notes", "value": "Detailed sales analysis:\n- Total revenue increa...
  {"op": "replace", "path": "/state/showNotes", "value": true}
catalog check: ok; skipped lines: 0
saved demo_spec.json and demo.png
the same spec in the terminal (node ink_render.mjs demo_spec.json):
╭──────────────────────────────────────────────────────────────────────────────────────╮
│ Lemonade Stand Dashboard                                                             │
│ THIS WEEK'S SALES    BEST DAY    PRODUCTS SOLD                                       │
│ $270                 Saturday    165                                                 │
│ +5%                  +20%        +10%                                                │
│ [ Refresh Numbers ]  [ Show Details ]                                                │
│ ╭──────────────────────────────────────────────────────────────────────────────────╮ │
│ │ Sales Over the Week                                                              │ │
│ │ Monday    ████████                 22                                            │ │
│ │ Saturday  ████████████████████████ 64                                            │ │
│ ╰──────────────────────────────────────────────────────────────────────────────────╯ │
│ [ Hide Notes ]                                                                       │
│ ╭──────────────────────────────────────────────────────────────────────────────────╮ │
│ │ Notes                                                                            │ │
│ │ Detailed sales analysis:                                                         │ │
│ ╰──────────────────────────────────────────────────────────────────────────────────╯ │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

The output is cut to fit the 40-line limit: `python demo.py` prints every
patch of the refresh turn, the whole chart, the two tables and the full
notes card.

![demo](demo.png)

Read the three presses in order. `refresh_numbers` went to the server, and
the model replaced twelve values in state; the metrics and the chart
changed on screen without a new spec. `show_details` went to the server
with the metric's label as a parameter; the model wrote a note into state
and set `/showNotes`, so the notes card appeared and the toggle button's
`$cond` label became "Hide Notes". The last press was that toggle:
`setState` ran inside the page and no request left the browser.

## Files

```text
step_03_json_render_actions_and_targets/
├── server.py           FastAPI app: POST /stream starts a session; POST /action runs the next turn as patches; GET /last lists the turns
├── llm.py              OpenAI-compatible client; stream_text(messages) streams one turn of a transcript
├── json_patch.py       RFC 6902 JSON Patch and RFC 6901 JSON Pointer; SpecStream compiles every turn
├── prompt.py           runs prompt.mjs and catalog_json.mjs once and caches prompt.txt and catalog.json
├── spec.py             check_spec(): types, child ids, props, and every on binding against the declared actions
├── catalog.mjs         six components plus Button; actions refresh_numbers and show_details with Zod params
├── registry.mjs        the React component map; Button emits "press" and the renderer dispatches on.press
├── app.mjs             the page: the compiler in a ref, handlers that POST /action, onStateChange logs setState, the #log element
├── ink_render.mjs      the second target: the same catalog with ink Box and Text components; node ink_render.mjs spec.json
├── index.html          the page shell and the import map of pinned esm.sh builds
├── prompt.mjs          prints the system prompt json-render generates from the catalog
├── catalog_json.mjs    prints the JSON Schema plus the action names (catalog and built-in)
├── prompt.txt          the cached prompt
├── catalog.json        the cached JSON Schema and action names
├── demo_spec.json      the spec after the recorded generate, refresh_numbers and show_details turns
├── tests/targets.test.mjs   node --test: one spec through react-dom/server and through a fake terminal; every page text appears in both
├── test_step.py        offline pytest: a fake model streams a first spec and an action turn; one transcript and compiler across both
├── demo.py             streams a dashboard, presses every button, prints each turn, saves demo.png, renders the spec with ink
├── demo.png            the page after the three presses, with the action log
├── package.json        adds @json-render/ink 0.20.0 and ink 6.8.0; npm test, npm run ink
├── package-lock.json   the lockfile for those pins
└── README.md           this file
```

## The idea

A spec is data, so a press is data too. json-render binds events with an
`on` field on the element, not with code in props:

```json
{
  "type": "Button",
  "props": { "label": "Refresh Numbers" },
  "on": { "press": { "action": "refresh_numbers" } },
  "children": []
}
```

Two kinds of action exist. Built-in ones (`setState`, `pushState`,
`removeState`) change the state model and never leave the page; a `visible`
condition or a `$state` prop reacts. Catalog actions are names you declare;
the page maps each to a handler, and here every handler is the same: tell
the server, run the next model turn, apply the patches that come back. That
is the loop the State of Generative UI report describes as the point of a
declarative format: the model edits a document, and the document is the UI.

The second half of the step is the reason to pick this format at all. The
element map does not mention HTML. The same `catalog.mjs` and the same
`demo_spec.json` go through `@json-render/ink`, and the dashboard appears in
a terminal. The json-render family has renderers for React, React Native,
Vue, Svelte, PDF, email and ink; a catalog written once serves all of them,
with one component map per target.

## The code, piece by piece

`catalog.mjs`: the Button and the two actions. `params` is a Zod schema, so
the model's `show_details` carries a typed `metric`.

```js
    Button: {
      props: z.object({
        label: z.string(),
        variant: z.enum(["primary", "secondary"]).nullable(),
      }),
      description: "A button. Bind its press event to an action with the on field.",
    },
  },
  actions: {
    refresh_numbers: {
      params: z.object({}),
      description: "Reload this week's numbers from the stand. The agent answers with patches that replace the values.",
    },
    show_details: {
      params: z.object({ metric: z.string() }),
      description: "Ask the agent for a details card about one metric. params.metric is the metric's label.",
    },
  },
});
```

`registry.mjs`: the component only emits. The renderer finds `on.press` on
the element and dispatches whatever action is bound there.

```js
    Button: ({ props, emit }) => html`
      <button className=${"button " + (props.variant ?? "primary")} onClick=${() => emit("press")}>${props.label}</button>`,
```

`app.mjs`: the handlers for the two catalog actions, and the trace of the
built-in one. The compiler lives in a ref now, so the second turn's patches
land on the spec the first turn built.

```js
  async function serverAction(action, params) {
    const started = performance.now();
    note(`${action} ${JSON.stringify(params)} -> server`);
    setLoading(true);
    const response = await fetch("/action", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, params }),
    });
    const patches = await consume(response);
    setLoading(false);
    note(`${action}: ${patches} patches applied in ${((performance.now() - started) / 1000).toFixed(2)} s`);
  }

  const handlers = {
    refresh_numbers: (params) => serverAction("refresh_numbers", params ?? {}),
    show_details: (params) => serverAction("show_details", params ?? {}),
  };

  // setState never reaches a handler; onStateChange is the only trace of it.
  function onStateChange(changes) {
    for (const { path, value } of changes) note(`setState ${path} = ${JSON.stringify(value)} (handled in the page)`);
  }
```

`server.py`: one transcript per session. A press becomes a user message
that names the action and its params, and asks for patches against the
spec the model already produced. The library's `buildUserPrompt` builds the
same kind of message in TypeScript; here it is one string.

```python
ACTION_TURN = """The user pressed a button bound to the action "{action}" with params {params}.
Answer with JSONL patches (RFC 6902) that edit the spec you already produced: use replace for
values that change, add for new elements and for new state, remove for elements to drop. Keep
existing ids. Output only patches, one per line."""
```

`server.py`: the same `SpecStream` compiles every turn, and the reply is
appended to the transcript once the stream ends. The action name and its
params are checked against the catalog before the model hears about the
press: the exported catalog JSON carries each action's `params` Zod schema
as JSON Schema (`show_details.metric: string`), so a press with the wrong
params is a `400` here, not a guess by the model.

```python
@app.post("/action")
def action(request: ActionRequest):
    if SESSION["compiler"] is None:
        raise HTTPException(status_code=409, detail="no spec on screen yet; POST /stream first")
    actions = catalog_json()["actions"]
    if request.action not in actions:
        raise HTTPException(status_code=400, detail=f"unknown action {request.action!r}; the catalog has {sorted(actions)}")
    # the params carry the Zod schema the catalog declared, exported as JSON Schema: check them here
    # so the model is never asked about a press whose params are not what the catalog promised
    for problem in jsonschema.Draft202012Validator(actions[request.action]["params"]).iter_errors(request.params):
        raise HTTPException(status_code=400, detail=f"{request.action} params: {problem.message}")
    SESSION["messages"].append({"role": "user", "content": ACTION_TURN.format(action=request.action, params=json.dumps(request.params))})
    return StreamingResponse(relay(SESSION["messages"], request.action), media_type="application/x-ndjson")
```

`server.py`: a turn whose model call fails must not leave the transcript
half-done. The pressed user message is removed when no reply came (the
next turn would otherwise send two user messages in a row), the stream
ends with the `{"error": "..."}` line of step 02, and the turn is
recorded with its `error` so `/last` tells the truth:

```python
    if error is None:
        messages.append({"role": "assistant", "content": reply})
    elif messages and messages[-1]["role"] == "user":
        messages.pop()  # no reply came: the next turn must not start with two user messages
```

`spec.py`: the Python check now reads the `on` field too. An action the
catalog does not declare would be dropped by the page with a console
warning, so the server reports it first. A binding that is a string, or
an `on` that is not an object, is reported as an unknown action rather
than raised:

```python
        bindings = element.get("on") or {}
        for event, binding in (bindings.items() if isinstance(bindings, dict) else []):
            for one in binding if isinstance(binding, list) else [binding]:
                action = one.get("action") if isinstance(one, dict) else None
                if action not in catalog.get("actions", {}) and action not in catalog.get("builtInActions", []):
                    problems.append(f"{element_id}: on.{event}: unknown action {action!r}")
```

`ink_render.mjs`: the second target. Same catalog, a second component map,
written with ink's `Box` and `Text`. `createRenderer` wraps the providers;
the `state` prop seeds the `$state` expressions. The ink package hands
components the whole `element`, where the React one hands them `props`.

```js
export const components = {
  Card: ({ element, children }) =>
    h(Box, { flexDirection: "column", borderStyle: "round", paddingX: 1, marginBottom: 0 },
      h(Text, { bold: true }, element.props.title),
      element.props.subtitle ? h(Text, { dimColor: true }, element.props.subtitle) : null,
      children),
  Row: ({ children }) => h(Box, { flexDirection: "row", gap: 2 }, children),
  ...
  Button: ({ element }) => h(Text, { color: "cyan" }, `[ ${element.props.label} ]`),
};

export const InkRenderer = createRenderer(catalog, components);
```

`ink_render.mjs`: ink draws to a stream. A fake stdout collects the frames
and a fake stdin satisfies ink's raw-mode check, so the render works under
a test runner and in a pipe.

```js
export async function renderSpecToText(spec, { columns = 88, onAction } = {}) {
  const stdout = new FakeStdout(columns);
  const instance = render(h(InkRenderer, { spec, state: spec.state ?? {}, onAction }), {
    stdout,
    stdin: new FakeStdin(),
    debug: true,
    patchConsole: false,
    exitOnCtrlC: false,
  });
  await new Promise((resolve) => setTimeout(resolve, 30));
  instance.unmount();
  // On a CI runner Ink unmounts with one more, empty write: keep the last frame that has content.
  return stdout.frames.filter((frame) => frame.trim()).at(-1) ?? "";
}
```

## Why: what breaks without it

A dashboard the user cannot touch is a picture. json-render's answer is
the `on` binding: a button names an action, and the action is either a
built-in the page handles (`setState`) or one the server answers with
more patches from the same model on the same transcript. Without the
session the model has no memory of the spec it wrote and answers a press
with a whole new dashboard; without the params check it is asked about
`show_details {}` and guesses a metric. The second target (Ink) is the
proof that the spec is data: nothing in it knows about the DOM.

## Run it

Prerequisites as steps 01 and 02 (Node 20+ and `npm install`, which now
brings `ink` and `@json-render/ink`; fastapi/uvicorn/httpx/jsonschema/
openai; a key; Playwright for `demo.py`).

bash:

```
npm install
export API_KEY=sk-...
python server.py                     # http://127.0.0.1:8057, press Generate, then the buttons
python demo.py                       # streams, presses every button, saves demo.png, renders in the terminal
node ink_render.mjs demo_spec.json   # the terminal render alone
python -m pytest -q test_step.py
npm test
```

PowerShell:

```
npm install
$env:API_KEY = "sk-..."
python server.py
python demo.py
node ink_render.mjs demo_spec.json
python -m pytest -q test_step.py
npm test
```

Expected output: the `Quick demo` transcript above. The number of
buttons and the patch counts depend on the model; `catalog check: ok;
skipped lines: 0` and a box-drawn dashboard at the end are the checks.

## Error handling

- A press with the wrong params (`show_details` without `metric`): `400`
  with the schema's message; the page logs `show_details: failed:
  server answered 400: ...`. An unknown action: `400`; a press before
  any spec: `409`. The page checks `response.ok` on both routes, so a
  JSON error body is never fed to the compiler as a patch line.
- A model call that fails during a turn: the stream ends with
  `{"error": "..."}`, the log says `refresh_numbers: failed: <reason>`,
  the pressed message is removed from the transcript, and
  `/last["turns"][-1]["error"]` records it. What arrived before the
  failure was applied.
- One turn at a time: `Generate` is disabled while a stream runs, and a
  button press during a turn is logged as `ignored, a turn is still
  running` and dropped; two presses cannot interleave on the shared
  compiler or the server's single session.
- A `$state` prop that has not arrived yet: `Table` and `Chart` default
  their arrays, `Metric` defaults `label` and `value` to `""`, so no
  component is swallowed by the Ink error boundary.
- `demo.py` gives uvicorn 10 s to bind port 8057 (`RuntimeError` when it
  cannot) and finds each button by its label, not its index, because a
  turn may add or remove buttons.
- ctrl-c stops `server.py` and `demo.py`; `node ink_render.mjs` exits on
  its own (the fake stdin holds no handle open).

## What to notice

- The terminal shows the notes card and the page does not. The page's
  last press was `setState /showNotes = false`, and `setState` never
  reaches the server; the terminal renders the spec as the server compiled
  it, where the model's own patch left `/showNotes` at `true`. Built-in
  actions are local state; if the agent must know, send them.
- The model edits with `replace` on state paths more than on elements.
  Twelve patches refreshed a whole dashboard for 282 output tokens, because
  the first turn put the numbers in state and the elements read them with
  `$state`.
- One `replace` in the demo targets `/state/sales/dailySales/0`: a single
  array cell. JSON Pointer reaches into arrays, and the chart re-renders
  with one bar changed.
- A `$state` prop can resolve to `undefined` while its state patch is still
  in flight, in the browser and in the terminal alike. The `Table` and
  `Chart` components default their arrays and `Metric` its `label` and
  `value` for that reason; without the default, the element's error
  boundary swallows the component and it stays blank after the state
  arrives.
- `renderSpecToText` waits 30 ms and then unmounts. That is a fixed
  wait, not a poll: Ink's first render is synchronous, so the frame is
  already in the fake stdout when the timer fires; the wait only lets a
  second frame land if the providers scheduled one. With `debug: true`
  Ink writes whole frames, and `unmount()` writes one more, empty frame
  on a CI runner, which is why the last *non-empty* frame is returned.
- `tests/targets.test.mjs` renders one spec with both targets and checks
  that every text the page shows, the terminal shows. That is the "one
  spec, two renderers" claim as a test.

## Gotchas / What this is not

- One session: `SESSION` is a module-level transcript and compiler. Two
  browsers pressing buttons share it, and a `Generate` in one resets the
  other's. There is no concurrency control beyond the page's own
  one-turn-at-a-time rule.
- `setState` stays in the page by design: the server's spec keeps
  `/showNotes` at the model's last value, which is why the terminal
  render shows the notes card. A real app that wants the agent to know
  sends the state change as its own turn or as context on the next one.
- The params check reads the JSON Schema `catalog_json.mjs` exported
  from the Zod `params`; a Zod refinement without a JSON Schema form is
  not checked in Python.
- The Ink target is a render, not a TUI: no key handling, no focus; the
  `onAction` hook exists so a terminal host could wire one.

## Diff from the previous step

- `catalog.mjs`: a `Button` component; `actions` with `refresh_numbers` and
  `show_details`; two prompt rules that make the demo exercise both kinds
  of action.
- `catalog_json.mjs` and `spec.py`: the action names (catalog and built-in)
  are exported and checked against every `on` binding.
- `registry.mjs`: the Button, which emits `press`.
- `app.mjs`: the compiler in a `useRef`, `consume()` shared by both turns,
  `handlers` for the catalog actions, `onStateChange` for the trace, and
  the `#log` element.
- `llm.py`: `stream_text(messages)` takes a transcript instead of two
  strings.
- `server.py`: `SESSION` (transcript, compiler, turns), `POST /action`,
  `ACTION_TURN`; `/last` now lists the turns with their patches and usage.
- `ink_render.mjs`: new, the terminal target and its CLI.
- `package.json`: `@json-render/ink` and `ink` pinned; `npm run ink`.
- `tests/targets.test.mjs` replaces `stream.test.mjs`.

## What the next step adds

Sub-theme 06 moves the same idea into MCP Apps: the UI is a resource an
MCP server ships, and the host mounts it in a sandboxed iframe with a
bridge instead of a catalog.
