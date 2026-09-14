# Step 02 - Declarative tree

**What this step adds:** the agent designs the layout. A catalog of eight
components (`Card`, `Row`, `Column`, `Text`, `Metric`, `Table`, `Chart`,
`Button`) replaces the three tools of step 01. The model writes the whole
dashboard as one JSON document, the server validates it against a JSON
Schema built from the catalog, and the page renders it as it streams with a
tolerant partial-JSON parser. The document comes in two shapes, a nested
tree and a flat element map with ids, and the demo measures why the flat
shape, the one A2UI and json-render chose, streams better.

## Quick demo

```bash
python demo.py
```

```text
prompt: show me a dashboard for a lemonade stand
shape  chunks  chars            first paint           layout known    done  valid  tokens
tree      408   1545      chunk  91 / 3.22s      chunk 408 / 6.10s   6.10s  yes    408
flat      266    921      chunk  33 / 1.08s      chunk  33 / 1.08s   3.41s  yes    266
demo_streaming.png: both shapes replayed to chunk 88 (tree left, flat right)
saved demo.png, demo_streaming.png
```

Both shapes replayed to the same chunk of their stream. The nested tree
has one metric inside an open card. The flat map has the whole layout, with
the slots that have not arrived yet drawn as pending:

![streaming](demo_streaming.png)

The finished flat layout:

![demo](demo.png)

## Declarative generation

The State of Generative UI report calls this the middle mode. Static
generation (step 01) lets the agent pick from a menu. Open-ended generation
(step 03) lets it write anything. Declarative generation lets it compose:
the components are still prebuilt and typed, but the agent decides which
ones, in what order, nested how. The output is data, not code, so the page
can validate it, render it with its own components, and refuse what it does
not understand.

Two things make this step more than "ask for JSON". First, the schema is
derived from the catalog, so the catalog is the single source of truth for
the prompt, the validator and the renderer. Second, the page does not wait
for the document to finish. It re-parses the partial text after every chunk
and re-renders. That only works if the parser tolerates unfinished JSON, and
it only looks good if the document's shape puts the layout before the
details. The nested tree does not: its root closes last. The flat map does:
the root element, with its list of child ids, is the first thing written.

## The code, piece by piece

`catalog.py`: the catalog, one entry per component: its props as JSON
Schema fragments and whether it takes children.

```python
# name -> (props schema, takes children?)
CATALOG = {
    "Card": ({"title": STRING}, True),
    "Row": ({}, True),
    "Column": ({}, True),
    "Text": ({"text": STRING}, False),
    "Metric": (METRIC_PROPS, False),
    "Table": (TABLE_PROPS, False),
    "Chart": (CHART_PROPS, False),
    "Button": ({"label": STRING, "action": STRING}, False),
}
```

`catalog.py`: the two schemas built from it. A node's `type` selects which
component schema applies. In the tree, a child is a node (`$ref`); in the
flat map, a child is an id (a string).

```python
def tree_schema():
    """A nested tree: every child is itself a node."""
    return {"$defs": {"node": any_node_schema({"$ref": "#/$defs/node"})}, "$ref": "#/$defs/node"}


def flat_schema():
    """A flat element map: every child is the id of another element."""
    return {
        "type": "object",
        "properties": {
            "root": STRING,
            "elements": {"type": "object", "additionalProperties": any_node_schema(STRING)},
        },
        "required": ["root", "elements"],
        "additionalProperties": False,
    }
```

`catalog.py`: validation returns a list of problems, so the server can send
them to the page instead of hiding a bad layout. The flat shape gets one
extra check the schema cannot express: every child id must exist.

```python
def validate(spec, shape):
    """The list of problems, empty when the spec fits the catalog. Also checks flat ids resolve."""
    validator = jsonschema.Draft202012Validator(SCHEMAS[shape]())
    problems = [f"{'/'.join(str(p) for p in e.path) or '/'}: {e.message}" for e in validator.iter_errors(spec)]
    if shape == "flat" and not problems:
        elements = spec["elements"]
        if spec["root"] not in elements:
            problems.append(f"root {spec['root']!r} is not an element")
        for element_id, element in elements.items():
            for child in element.get("children", []):
                if child not in elements:
                    problems.append(f"{element_id}: child {child!r} is not an element")
    return problems
```

`catalog.py`: the prompt is generated from the same catalog. The flat rules
ask for the root first and the elements top-down. That ordering is the
whole trick.

```python
SHAPE_RULES = {
    "tree": "Answer with one JSON object: the root node. A node is {\"type\", \"props\", \"children\"}; "
            "children is a list of nodes and is only allowed on components that take children.",
    "flat": "Answer with one JSON object {\"root\", \"elements\"}. Write \"root\" first. \"elements\" maps an id to a node "
            "{\"type\", \"props\", \"children\"}, where children is a list of ids. Write the root element first, "
            "then its children in order, then their children: top-down, so the layout is known before the details.",
}
```

The tolerant parser is a normal recursive-descent JSON parser with one
difference: running out of text is not an error. An open object or array
is returned as it stands, typed `PartialDict` or `PartialList` so a
renderer can tell "closed by the model" from "closed by the parser". The
same rules live in `page/partial-json.mjs`; here is `partial_json.py`:

```python
    def obj(self):
        self.i += 1  # {
        out = PartialDict()
        while True:
            self.skip_ws()
            if self.at_end():
                return out
            c = self.peek()
            if c == "}":
                self.i += 1
                return dict(out)  # closed by the model: a plain dict
            if c == ",":
                self.i += 1
                continue
            if c != '"':
                raise ValueError(f"expected a key at {self.i}")
            key, closed = self.string()
            if not closed:
                return out  # the key itself was cut
            self.skip_ws()
            if self.at_end():
                return out  # key but no colon yet
            if self.peek() != ":":
                raise ValueError(f"expected ':' at {self.i}")
            self.i += 1
            try:
                out[key] = self.value()
            except Incomplete:
                return out  # key and colon, but no value yet
```

`page/render.mjs`: the two walkers. In the tree, an open node renders with
whatever closed children it has, wrapped as pending. In the flat map, a
child id whose element has not arrived renders as an empty pending slot, so
the layout holds still while the details stream in.

```js
export function renderTree(node) {
  // A nested tree. A node still open in the stream renders as pending, with
  // whatever closed children it already has inside it.
  if (!isComponent(node)) return node ? PENDING : "";
  const children = (node.children ?? []).map(renderTree).join("");
  const html = render(node.type, node.props, children);
  return isPartial(node) ? `<div class="pending-wrap">${html}</div>` : html;
}

export function renderFlat(spec, id = spec?.root, seen = new Set()) {
  // A flat element map. A child id whose element has not arrived yet renders
  // as a pending slot, so the layout holds still while the details stream in.
  const node = spec?.elements?.[id];
  if (node === undefined || seen.has(id)) return PENDING;
  seen.add(id);
  if (!isComponent(node)) return PENDING;
  const children = (node.children ?? []).map((child) => renderFlat(spec, child, seen)).join("");
  const html = render(node.type, node.props, children);
  return isPartial(node) ? `<div class="pending-wrap">${html}</div>` : html;
}
```

`page/app.js`: the loop. Static messages are appended as in step 01. Deltas
are accumulated, parsed and re-rendered on every chunk.

```js
    } else if (message.delta !== undefined) {
      text += message.delta;
      timeline.push(Math.round(performance.now() - started));
      wire.textContent = text;
      dashboard.innerHTML = renderSpec(parsePartial(text), mode);
    } else if (message.done) {
      wire.textContent += "\n" + JSON.stringify({ ...message, spec: undefined });
      if (message.spec) dashboard.innerHTML = renderSpec(message.spec, mode);
```

`progress.py`: the measurement. After each chunk it asks two questions:
how many catalog components are closed and reachable from the root, and is
the root's list of children final. The demo prints the chunk and the time
at which each first became true.

```python
def skeleton_known(spec, shape):
    """Is the root's list of direct children final?"""
    if shape == "tree":
        return is_component(spec) and not is_partial(spec) and not is_partial(spec.get("children", []))
    if not isinstance(spec, dict) or not isinstance(spec.get("elements"), dict):
        return False
    root = spec["elements"].get(spec.get("root"))
    return is_component(root) and not is_partial(root) and not is_partial(root.get("children", []))
```

## Run it

```bash
python server.py            # http://127.0.0.1:8010, pick a mode in the page
python demo.py              # both shapes, the table, demo.png and demo_streaming.png
python -m pytest test_step.py
npm test                    # the parser and renderer tests alone
```

`GET /api/schema/flat` and `/api/schema/tree` return the generated
schemas. The request sets `response_format: {"type": "json_object"}` so the
model does not wrap the JSON in a code fence; the server strips one anyway.

## What to notice

- The catalog drives three things: the prompt the model reads, the schema
  the server checks, and the renderer table the page uses. Add a component
  in one place and all three follow.
- The tree's layout was known at chunk 408 of 408. The flat map's at chunk
  33 of 266. Same prompt, same model, same components. The difference is
  the order in which the JSON puts the information, and that is why the
  declarative protocols in the next sub-themes all use a flat map with ids.
- First paint is a different number. The nested tree painted its first
  metric at chunk 91; the flat map at chunk 33, because the root element is
  short and closes early. Neither shape needs the parser to be clever about
  half-written strings: a metric titled "Lemon" for one chunk is fine, a
  layout that jumps is not.
- The model wrote `"children": []` on leaves in one run. The schema now
  allows an empty list there; the validator's messages name the exact path
  when something else is wrong, so a bad layout is reported, not hidden.
- Validation happens on the finished document. The page renders the
  partial one on trust, with unknown component names shown as stubs.

## Diff from the previous step

```bash
diff -r ../step_01_static_components .
```

New: `partial_json.py`, `progress.py`, `page/partial-json.mjs`,
`tests/partial-json.test.mjs`. Changed: `catalog.py` (catalog, schemas,
prompt, `validate`), `server.py` (`mode`, `declarative_layout`,
`/api/schema`), `llm.py` (`response_format`), `page/render.mjs` (five more
renderers, `renderTree`, `renderFlat`), `page/app.js` (mode, deltas,
replay hook), `page/index.html` (mode select, layout styles), `demo.py`.
