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
back as the tool result, so a bad spec is a correction, not a crash. The spec
is whatever the model put in the tool call, so every level is checked for
its shape before it is read - a `root` that is a list, `props` that is a
list, a child given as an object - and a wrong shape is a sentence too:

```python
def validate(spec):
    """Every problem in a spec, as plain sentences. An empty list means valid.

    The spec is whatever the model put in the tool call, so every level is
    checked for its shape before it is read: a wrong shape is a sentence in
    the list, never an exception out of the validator.
    """
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

What it checks, in order: the top-level shape; every element is an object
with a string `type` from the catalog; `props` is an object whose keys are
in the catalog and whose values have the declared type (`string` or `list`);
required props are present; `children` is a list of ids that exist, and only
on types that take children; `Stack.direction` is `row`/`column`;
`Chart.kind` is `bar`/`line`, `labels` and `values` have the same length and
`values` are numbers; every `Table` row is a list; and, when nothing else
is wrong, no element contains itself (`cycles()`). What it does not check:
the length of a label or a value, the number of cells per row against the
number of columns, or ids that no `children` list reaches (an unreachable
element is simply never drawn).

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

`harness/ui.py` is the first surface. `tool()` routes a `render_ui` call
that *ran* to `render()` - the decision is keyed on the result, not on the
arguments, so a denied or failed call shows the usual tool panel with the
denial or the error in it and no picture. `_element()` then maps one element
to one `rich` renderable, recursing over children:

```python
        if name == "render_ui" and result.startswith("Rendered "):  # drawn only when the tool ran: a denied or failed call is a panel, not a picture
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

## Why: what breaks without it

Ask the stage 15 agent for "a dashboard for the lemonade stand" and it
writes a Markdown table and a list of numbers, because prose is the only
output it has. A model that *could* answer with a chart has no channel for
it, so the answer is a description of a chart. Giving it HTML instead would
open the other failure: the model writes markup, the terminal cannot show
it, and the browser would run whatever it wrote. The spec sits in between:
structured enough for both surfaces to draw, constrained enough (six
catalog types, validated) that the surfaces can trust it. Without the
validator the terminal renderer would raise on the first `Chart` whose
`values` are strings, halfway through a turn, with the tool call still
unanswered in the transcript.

## Run it

Prerequisites: `pip install -r ../../../requirements.txt` from the repo
root (openai, rich, prompt_toolkit). Playwright with Chromium
(`pip install playwright && playwright install chromium`) is needed only for
`demo.py`'s screenshot. Settings come from `API_KEY` (or `OPENAI_API_KEY`),
`BASE_URL` and `MODEL` in the environment or in `~/.simple-harness/env`;
the defaults are the OpenAI endpoint and `gpt-4.1-mini`.

```bash
cd genui/07_harness_genui/step_01_render_ui_tool
python -m harness.agent            # the interactive agent, terminal surface only
python -m harness.agent --web      # also serve http://127.0.0.1:8770
python -m harness.agent --web 9000 # ...on another port
python demo.py                     # one scripted turn on the real model, both surfaces, demo.png
python demo.py --offline           # the same turn against the scripted model, no API key
python -m pytest test_step.py -q   # offline: fake model, ephemeral web server
```

```powershell
cd genui\07_harness_genui\step_01_render_ui_tool
$env:API_KEY = "sk-..."             # or OPENAI_API_KEY; ~/.simple-harness/env works too
python -m harness.agent --web
python demo.py --offline
python -m pytest test_step.py -q
```

Expected output of `python -m harness.agent --web`, then one request:

```text
───────────────────────────────  coding agent  ────────────────────────────────
  sandbox: none  ·  /sessions  /rewind  ·  alt-enter for a newline  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave
  web surface: open http://127.0.0.1:8770 in a browser

> show me a dashboard for a lemonade stand
  1,365 prompt · 308 completion
  ┌─ render_ui · 7 elements ─────────────────────────────────────────────────┐
  │ ┌─ Lemonade stand - this week ─────────────────────────────────────────┐ │
  │ │ Revenue              Cups sold             Margin                    │ │
  │ │ $184  +12%           92  +8                61%  -2%                  │ │
  │ │ Cups per day                                                         │ │
  │ │ Mon  ███████████████             14                                  │ │
  ...
  └──────────────────────────────────────────────────────────────────────────┘
  1,690 prompt · 43 completion
  agent
  Here is this week's lemonade stand at a glance.
```

The browser tab shows the same seven elements as DOM, and redraws on the
next `render_ui` call without a reload. `python -m pytest test_step.py -q`
ends in `12 passed`.

## Error handling

Every tool call gets exactly one `tool` message, whatever went wrong, so the
transcript stays valid and `--resume` can always send it:

- A `render_ui` call with a spec the catalog rejects returns
  `Invalid spec, nothing rendered:` followed by one line per problem. Nothing
  is drawn on either surface; the model reads the list and tries again.
- Malformed JSON in the arguments returns
  `Error: the arguments of render_ui are not a JSON object: ...`; a tool name
  that does not exist returns `Error: no tool named 'x'.`; anything a tool
  raises comes back as `Error: TypeError: ...` (all in `tools.execute()`,
  shared with the subagent).
- A denied call (`Blocked by policy: ...` or `The user denied this tool
  call.`) is shown as a tool panel, never drawn - `ui.tool` checks the
  result, not the arguments.
- `--web` on a port that is taken prints
  `web surface not started on port 8770: ...` and the terminal surface
  carries on alone.
- A model call that fails (`openai.APIError`, or an empty reply) ends the
  turn with `model call failed: ...`; your message stays in the transcript.
- ctrl-c during a turn answers every tool call that had not run with
  `(interrupted before this tool ran)`, prints `interrupted`, saves, and
  returns to the prompt. A turn that would exceed 40 model calls stops with
  `stopped after 40 model calls in one turn; say 'continue' to go on`.
- Leave with `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or
  ctrl-c at the prompt.

## Gotchas / What this is not

- `render_ui` goes through `execute()`, which today rates it `allow`: the
  permission rules only ask about `bash` and writes outside the project or
  into `.git/`. If you add an `ask` rule for it, nothing else has to change -
  `ui.tool` already refuses to draw a call whose result is a denial.
- The subagent never gets the tool (`WITHHELD` in `harness/subagent.py`)
  and is denied if it names it anyway: what it may run is exactly what it
  was shown.
- The web surface serves only `web/index.html` and `web/app.js`; a path
  with `..` in it is a 404. It listens on 127.0.0.1, has no authentication,
  and replays the last spec to every tab that connects.
- Both renderers assume a validated spec. `render()` is only reached through
  a `Rendered ...` result; calling it by hand with a spec `validate()` would
  reject is on you.
- This is a fixed catalog with no state and no actions: a `Metric` cannot
  be clicked and a `Table` cannot be sorted. Sub-theme 05 has the actions
  story; here the point is the one-tool, two-surface shape.
- The tool named `bash` runs through `subprocess` with `shell=True`, so on
  Windows it is cmd.exe, and the sandbox is `none` there (see stage 12).

## What to notice

- The model saw the catalog once, in the system prompt, and produced a
  ten-element map with nested Cards, a Chart and a Table on the first call.
  Nothing in the loop changed to make that happen; the tool did the work.
- `render_ui` sits behind `execute()`, the same entry point as `bash`, so
  the same code decides, asks and reports for it - today it is rated
  `allow`. The subagent does not get it (`WITHHELD` in
  `harness/subagent.py`): an explorer reports, it does not draw.
- The terminal renderer and the DOM renderer are the same shape: a lookup
  by type and a recursive walk. Adding a `Gauge` means one catalog entry
  and one function per surface. The validator already rejects it until
  those exist, which the tests check.
- The web surface is a push channel, not a poll. `publish()` fans one spec
  out to every open tab, and a tab that opens after the render still gets
  the latest one.

## What the next step adds

The same catalog idea on a harness we do not own: TrueForge's built-in
generative UI speaks OpenUI Lang, and step 02 renders its stream in a page
of ours with the parser from sub-theme 04.
