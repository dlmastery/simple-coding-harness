# Step 01 - A render_ui tool for the harness

The harness codelab ends with a coding agent that talks in prose and tool
panels. This step gives that agent a way to answer with an interface.

**What this step adds:** the stage 15 loop (`harness/`, copied from
`step_15_subagents`) gains one tool, `render_ui(spec)`. Its argument is a
json-render element map validated against a small catalog. The terminal
draws the spec as a `rich` panel tree, and `--web` serves the same spec to
a browser page over SSE. One agent, one spec, two surfaces.

## Quick demo

```
python demo.py              # real model, terminal + web surface, saves demo.png
python demo.py --offline    # scripted model, no API key
```

Recorded output of `python demo.py` (blank lines removed):

```text
───────────────────────────────  coding agent  ────────────────────────────────
  web surface: http://127.0.0.1:53546
  show me a dashboard for a lemonade stand
  1,365 prompt · 308 completion
  ┌─ render_ui · 10 elements ───────────────────────────────────────────────┐
  │ ┌─ Lemonade Stand Dashboard ──────────────────────────────────────────┐ │
  │ │ Daily Lemonade Sales                                                │ │
  │ │ 120 cups  +8%                                                       │ │
  │ │ Sales Over the Past Week                                            │ │
  │ │ Mon                      ██████████████████       100               │ │
  │ │ Tue                      ████████████████████     110               │ │
  │ │ Wed                      █████████████████████    115               │ │
  │ │ Thu                      ████████████████████████ 130               │ │
  │ │ Fri                      ███████████████████████  125               │ │
  │ │ Sat                      ██████████████████████   120               │ │
  │ │ Sun                      ██████████████████████   120               │ │
  │ │ ┌─ Inventory ─────────────────────────────────────────────────────┐ │ │
  │ │ │ ┌─────────────┬──────────┐                                      │ │ │
  │ │ │ │ Item        │ Quantity │                                      │ │ │
  │ │ │ ├─────────────┼──────────┤                                      │ │ │
  │ │ │ │ Lemons      │ 50       │                                      │ │ │
  │ │ │ │ Sugar (lbs) │ 10       │                                      │ │ │
  │ │ │ │ Cups        │ 150      │                                      │ │ │
  │ │ │ │ Ice (lbs)   │ 20       │                                      │ │ │
  │ │ │ └─────────────┴──────────┘                                      │ │ │
  │ │ └─────────────────────────────────────────────────────────────────┘ │ │
  │ │ ┌─ Today's Weather ───────────────────────────────────────────────┐ │ │
  │ │ │ Sunny, 78°F                                                     │ │ │
  │ │ └─────────────────────────────────────────────────────────────────┘ │ │
  │ │ Daily Expenses                                                      │ │
  │ │ $45  -5%                                                            │ │
  │ │ Daily Profit                                                        │ │
  │ │ $180  +10%                                                          │ │
  │ └─────────────────────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────────────┘
  1,690 prompt · 43 completion
  agent
  I created a dashboard for the lemonade stand showing daily sales with a
  metric and chart, inventory details, today's weather, daily expenses, and
  daily profit. Let me know if you want to add or change anything!
  saved demo.png from the web surface
```

The same spec on the web surface, taken headlessly by the demo script:

![demo](demo.png)

## Files

```text
step_01_render_ui_tool/
├── harness/          the stage 15 loop; changed from step_15_subagents: agent.py (--web flag), config.py (OpenAI defaults, OPENAI_API_KEY), llm.py (catalog in the system prompt), tools.py (render_ui), ui.py (rich renderer), subagent.py (render_ui withheld); new: genui.py (catalog + validate), web.py (SSE surface)
├── web/
│   ├── index.html    the browser surface's page shell
│   └── app.js        one renderer per catalog type, walking the element map from root
├── test_step.py      offline pytest: the validator, the tool, both surfaces, the loop against a scripted model
├── demo.py           one scripted turn on the real model, both surfaces, saves demo.png
├── demo.png          the recorded web surface
└── README.md         this file
```

## The idea: the spec is the interface

In the report's terms this is **declarative generation** on a custom
transport. The agent never writes HTML and never picks a widget by name. It
emits a spec: a flat element map with ids, the shape json-render and A2UI
use. The harness validates the spec against a catalog and hands it to
whichever surface is listening.

That split is the point of the step. The tool result the model sees is one
sentence. The picture is drawn by the surface, from data. Add a surface and
nothing in the agent changes; the same map is a `rich` tree in the terminal
and a DOM tree in the browser.

## The code, piece by piece

`harness/genui.py` holds the catalog. Six components, each with typed props,
a required list, and a flag for whether it takes children:

```python
CATALOG = {
    "Card": {
        "description": "A titled box around other elements.",
        "props": {"title": "string"},
        "required": [],
        "children": True,
    },
    "Stack": {
        "description": "Lays its children out in a row or a column.",
        "props": {"direction": "string"},
        "required": ["direction"],
        "children": True,
    },
...
    "Metric": {
        "description": "One number with a label and an optional delta such as '+12%'.",
        "props": {"label": "string", "value": "string", "delta": "string"},
        "required": ["label", "value"],
        "children": False,
    },
```

`validate()` returns every problem as a sentence. The model gets the list
back as the tool result, so a bad spec is a correction, not a crash:

```python
def validate(spec):
    """Every problem in a spec, as plain sentences. An empty list means valid."""
    problems = []
    if not isinstance(spec, dict) or "elements" not in spec or "root" not in spec:
        return ["spec must be an object with 'root' and 'elements'"]
...
        for name in entry["required"]:
            if name not in props:
                problems.append(f"{eid}: {element['type']} needs prop '{name}'")
        for name, value in props.items():
            expected = entry["props"].get(name)
            if expected is None:
                problems.append(f"{eid}: {element['type']} has no prop '{name}'")
            elif not isinstance(value, TYPES[expected]):
                problems.append(f"{eid}: prop '{name}' must be a {expected}")
...
        for child in children:
            if child not in elements:
                problems.append(f"{eid}: child '{child}' is not an element id")
```

`harness/tools.py` adds the tool next to `bash` and `task`. The function is
small: validate, publish, report:

```python
def render_ui(spec: dict) -> str:
    """Validate a json-render element map and hand it to every surface.

    The terminal draws it in ui.tool(); the web page gets it over SSE. The
    model only sees this short string, never the picture: the spec is data
    that the surfaces interpret, not something the model has to describe.
    """
    problems = validate(spec)
    if problems:
        return "Invalid spec, nothing rendered:\n- " + "\n- ".join(problems)
    web.publish(spec)
    return f"Rendered {len(spec['elements'])} elements from root '{spec['root']}'."
```

`harness/llm.py` puts the catalog into the system prompt, generated from the
same dictionary the validator uses, so the two cannot drift apart:

```python
When the answer is a dashboard, a table, a chart or a set of numbers, call
render_ui with a json-render element map instead of writing it out as text.
The catalog, the only element types you may use:
{catalog_prompt()}
```

`harness/ui.py` is the first surface. `tool()` routes a valid `render_ui`
call to `render()`, and `_element()` maps one element to one `rich`
renderable, recursing over children:

```python
        if name == "render_ui" and not validate(args.get("spec")):
            return self.render(args["spec"])
```

```python
    def _element(self, spec, eid):
        """One element to one rich renderable; containers recurse over their children."""
        element = spec["elements"][eid]
        kind, props = element["type"], element.get("props") or {}
        children = [self._element(spec, c) for c in element.get("children") or []]
        if kind == "Card":
            return Panel(Group(*children), title=Text(props.get("title", ""), style=f"bold {ACCENT}"), title_align="left", border_style=MUTED, padding=(0, 1))
        if kind == "Stack":
            return Columns(children, padding=(0, 2), expand=True) if props["direction"] == "row" else Group(*children)
        if kind == "Text":
            return Text(props["text"])
```

`harness/web.py` is the second surface's server: the standard library
`http.server` in a daemon thread, one queue per open tab, and a replay of the
last spec to a tab that opens late:

```python
def publish(spec):
    """Hand a spec to every open tab and remember it for the next one."""
    global latest
    with lock:
        latest = spec
        for q in list(subscribers):
            q.put(spec)
```

```python
                else:
                    self.wfile.write(f"data: {json.dumps(spec)}\n\n".encode())
```

`web/app.js` is the browser renderer. The shape mirrors `_element()`: one
function per catalog type, keyed by name, and a walk from `root`:

```js
export function render(spec, id = spec.root) {
  const element = spec.elements[id];
  const children = (element.children || []).map((child) => render(spec, child));
  const draw = RENDERERS[element.type];
  if (!draw) return el("p", "", `(${element.type}: no web renderer)`);
  const node = draw(element.props || {}, children);
  node.dataset.id = id;
  return node;
}
```

```js
const source = new EventSource("/events");
source.onmessage = (event) => {
  const spec = JSON.parse(event.data);
  surface.replaceChildren(render(spec));
```

## Run it

```
python -m harness.agent            # the interactive agent, terminal surface only
python -m harness.agent --web      # also serve http://127.0.0.1:8770
python demo.py                     # one scripted turn, both surfaces, demo.png
python -m pytest test_step.py      # offline: fake model, ephemeral web server
```

Settings come from `API_KEY`, `BASE_URL` and `MODEL` in the environment or
in `~/.simple-harness/env`. Playwright with Chromium is needed only for the
screenshot.

## What to notice

- The model saw the catalog once, in the system prompt, and produced a
  ten-element map with nested Cards, a Chart and a Table on the first call.
  Nothing in the loop changed to make that happen; the tool did the work.
- `render_ui` sits behind `execute()`, so it goes through the same
  permission check as `bash`. The subagent does not get it (`WITHHELD` in
  `harness/subagent.py`): an explorer reports, it does not draw.
- The terminal renderer and the DOM renderer are the same shape: a lookup
  by type and a recursive walk. Adding a `Gauge` means one catalog entry
  and one function per surface. The validator already rejects it until
  those exist, which the tests check.
- The web surface is a push channel, not a poll. `publish()` fans one spec
  out to every open tab, and a tab that opens after the render still gets
  the latest one.
