# Step 01 - A json-render catalog and the React Renderer

**What this step adds:** the whole json-render loop, once, without streaming.
A catalog of six components with Zod props (`catalog.mjs`); the prompt the
library generates from it (`catalog.prompt()`, printed by `prompt.mjs` and
cached in `prompt.txt`); a Python server that asks the model for one complete
spec; a check of that spec against the same catalog in Python (`spec.py`);
and the page, where `defineRegistry` maps each catalog entry to a React
function and `Renderer` walks the spec. No JSX and no bundler: the page uses
`htm` and an import map.

## Quick demo

```
python demo.py
```

```text
prompt: Show me a dashboard for a lemonade stand: this week's sales, the best days, and what sold.
complete spec after 5.8 s: 9 elements, 4109 prompt tokens, 351 completion tokens
first paint: 5.8 s (nothing renders before the whole object arrives)
Card #card-main  {"title": "Lemonade Stand Dashboard", "subtitle": "Weekly Sales Overvi...
  Row #row-metrics  {"gap": "large"}
    Metric #metric-sales  {"label": "This Week's Sales", "value": {"$template": "$${/sales/total...
    Metric #metric-best-day  {"label": "Best Day", "value": {"$state": "/sales/bestDay"}}
    Metric #metric-products-sold  {"label": "Products Sold", "value": {"$state": "/sales/productsSold"}}
  Card #card-best-days  {"title": "Best Days"}
    Table #table-best-days  {"columns": ["Day", "Sales"], "rows": [["Monday", "$120"], ["Wednesday...
  Card #card-products  {"title": "What Sold"}
    Table #table-products  {"columns": ["Product", "Units Sold", "Revenue"], "rows": [["Classic L...
state: {"sales": {"total": 250, "bestDay": "Wednesday", "productsSold": 100}}
saved demo_spec.json and demo.png
```

![demo](demo.png)

The model chose to put three numbers in `state` and to reference them with
`$state` and `$template` props. The catalog prompt suggests that; the
renderer resolves the expressions before the `Metric` component sees them.

## Files

```text
step_01_json_render_catalog/
├── server.py           FastAPI app: POST /generate returns one complete spec; GET /spec the last one; serves the page
├── llm.py              OpenAI-compatible client, key from the env or ~/.simple-harness/env; complete_spec() in JSON mode
├── prompt.py           runs prompt.mjs and catalog_json.mjs once and caches prompt.txt and catalog.json
├── spec.py             check_spec(): unknown types, dangling child ids and wrong prop types, against catalog.json
├── catalog.mjs         the catalog: six components with Zod props; PROMPT = catalog.prompt() plus four "one object" rules
├── registry.mjs        one React function per catalog entry through defineRegistry, written with htm (no JSX)
├── app.mjs             the page: send the prompt, receive one spec, hand it to Renderer inside JSONUIProvider
├── index.html          the page shell and the import map of pinned esm.sh builds (React 19, htm, json-render)
├── prompt.mjs          prints the system prompt json-render generates from the catalog
├── catalog_json.mjs    prints the catalog as JSON Schema, one entry per component
├── prompt.txt          the cached prompt (about 4,100 tokens)
├── catalog.json        the cached JSON Schema of the six components
├── demo_spec.json      the spec the recorded demo produced
├── tests/render.test.mjs   node --test: the catalog, the prompt and the registry through react-dom/server
├── test_step.py        offline pytest: fake model, real server, spec check, prompt cache, then the Node suite
├── demo.py             starts the server, generates once, prints the spec as a tree, saves demo_spec.json and demo.png
├── demo.png            the recorded page
├── package.json        @json-render/core and /react 0.20.0, htm, react 19, zod pinned; npm test
├── package-lock.json   the lockfile for those pins
└── README.md           this file
```

## The idea

json-render is the declarative middle of the State of Generative UI report:
the model does not write code, and it does not pick from fixed screens. It
emits a JSON document that names components from a catalog you wrote. The
catalog is the contract. It produces the prompt, the type of the props, the
component map and the validation, all from one object.

The spec shape is a flat element map, not a nested tree:

```json
{
  "root": "card-1",
  "elements": {
    "card-1": { "type": "Card", "props": { "title": "Lemonade" }, "children": ["metric-1"] },
    "metric-1": { "type": "Metric", "props": { "label": "Sales", "value": "$250" }, "children": [] }
  },
  "state": { "sales": { "bestDay": "Wednesday" } }
}
```

Elements refer to each other by id. That is what makes step 2 possible: a
patch can add one element at a time, and a parent can name a child that has
not arrived yet. This step asks for the whole document in one reply, so the
reader sees the shape before it is cut into patches.

## The code, piece by piece

`catalog.mjs`: six components. `.nullable()` marks a prop the model may skip;
the prompt shows it as `subtitle?`.

```js
export const catalog = defineCatalog(schema, {
  components: {
    Card: {
      props: z.object({
        title: z.string(),
        subtitle: z.string().nullable(),
      }),
      description: "A titled container. Put related elements inside it.",
    },
    ...
    Chart: {
      props: z.object({
        kind: z.enum(["bar", "line"]),
        labels: z.array(z.string()),
        values: z.array(z.number()),
      }),
      description: "A small bar or line chart. labels and values have the same length.",
    },
  },
  actions: {},
});
```

`catalog.mjs`: the library's prompt asks for JSONL patches, because streaming
is its native mode. Four extra rules ask for one object instead. Step 2
removes them.

```js
export const PROMPT = catalog.prompt({
  system: "You are a dashboard builder. You turn a request into a UI spec.",
  customRules: [
    "Reply with ONE JSON object, the complete spec: {\"root\": \"...\", \"elements\": {...}}. Do not output JSONL patches.",
    "Use short element ids such as card-1, row-1, metric-1.",
    "Every element needs type, props and children (an empty array when it has none).",
    "Fill every prop. Use null for an optional prop you do not need.",
  ],
});
```

Python never imports the catalog. It runs `node prompt.mjs` once and keeps
the text in `prompt.txt`; `catalog_json.mjs` does the same for the props as
JSON Schema. The cache lives in `prompt.py`:

```python
def _cached(cache_file, script):
    if not cache_file.exists():
        node = shutil.which("node")
        if node is None:
            raise RuntimeError(f"{cache_file.name} is missing and node is not on PATH")
        result = subprocess.run([node, script], cwd=STEP, capture_output=True, text=True, encoding="utf-8", check=True)
        cache_file.write_text(result.stdout, encoding="utf-8")
    return cache_file.read_text(encoding="utf-8")
```

`llm.py`: JSON mode makes the API return one object, which is what the
extra rules ask for.

```python
    response = client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
```

`spec.py`: the server checks the spec before the page sees it. Unknown
types, dangling child ids and wrong prop types are the three faults a
renderer fails on quietly. Props that are expressions (`{"$state": ...}`)
are skipped, as the renderer resolves them first.

```python
def check_spec(spec, catalog):
    problems = []
    if not isinstance(spec, dict) or "root" not in spec or not isinstance(spec.get("elements"), dict):
        return ["spec needs a root id and an elements map"]
    elements = spec["elements"]
    if spec["root"] not in elements:
        problems.append(f"root {spec['root']!r} is not in elements")
    components = catalog["components"]
    for element_id, element in elements.items():
        kind = element.get("type")
        if kind not in components:
            problems.append(f"{element_id}: unknown type {kind!r}")
            continue
        for child in element.get("children", []):
            if child not in elements:
                problems.append(f"{element_id}: child {child!r} is not in elements")
        props = {k: v for k, v in element.get("props", {}).items() if not is_expression(v)}
        expressions = set(element.get("props", {})) - set(props)
        validator = jsonschema.Draft202012Validator(props_schema(components[kind], expressions))
        for error in validator.iter_errors(props):
            where = "/".join(str(p) for p in error.path) or "props"
            problems.append(f"{element_id}: {kind}.{where}: {error.message}")
    return problems
```

One React function per catalog entry. `defineRegistry` types `props` from
the Zod schema (in TypeScript; at runtime it only builds the map). `htm`
replaces JSX, so the same file runs in the browser and in `react-dom/server`
for the tests. From `registry.mjs`:

```js
export const { registry } = defineRegistry(catalog, {
  components: {
    Card: ({ props, children }) => html`
      <section className="card">
        <h2>${props.title}</h2>
        ${props.subtitle ? html`<p className="subtitle">${props.subtitle}</p>` : null}
        ${children}
      </section>`,
    ...
    Metric: ({ props }) => html`
      <div className="metric">
        <div className="label">${props.label}</div>
        <div className="value">${props.value}</div>
        ${props.delta ? html`<div className="delta">${props.delta}</div>` : null}
      </div>`,
```

`app.mjs`: `Renderer` needs the contexts `JSONUIProvider` supplies (state,
actions, visibility). `spec.state` seeds the state model.

```js
    <main id="surface">
      <${JSONUIProvider} registry=${registry} initialState=${spec?.state ?? NO_STATE}>
        <${Renderer} spec=${spec} registry=${registry} />
      <//>
    </main>`;
```

The import map. React 19 ships no browser ESM build, so the pinned builds
come from esm.sh; `?external=` keeps one copy of `react`, `zod` and
`@json-render/core` shared by every package. The versions are the ones in
`package.json`, which serve Node. From `index.html`:

```html
<script type="importmap">
{
  "imports": {
    "react": "https://esm.sh/react@19.2.3",
    "react/jsx-runtime": "https://esm.sh/react@19.2.3/jsx-runtime?external=react",
    ...
    "@json-render/core": "https://esm.sh/@json-render/core@0.20.0?external=zod",
    "@json-render/react": "https://esm.sh/@json-render/react@0.20.0?external=react,react/jsx-runtime,zod,@json-render/core,@json-render/core/store-utils",
```

## Run it

```
npm install
python server.py          # http://127.0.0.1:8055
python demo.py            # generates once, saves demo_spec.json and demo.png
python -m pytest -q test_step.py
npm test
```

The model settings come from `API_KEY`, `BASE_URL` and `MODEL`, or from
`~/.simple-harness/env`. Delete `prompt.txt` and `catalog.json` after editing
`catalog.mjs`; the next start regenerates them.

## What to notice

- One object, four outputs. `catalog.mjs` produces the prompt, the JSON
  Schema, the typed registry and `catalog.validate`. Change a prop and every
  layer changes with it.
- The prompt is 4,100 tokens for six components. Most of it is the
  library's own text about state, repeats, events and visibility. That is
  the price of a general renderer; sub-theme 04 measures the other side.
- The check in `spec.py` and the check in `catalog.validate` agree on the
  spec shape, but Python cannot run the Zod schema, so it reads the JSON
  Schema the Node script exported. Two runtimes, one catalog.
- Nothing renders before the whole object arrives: 5.8 s in the demo. Step
  2 changes that number.
