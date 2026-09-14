# Step 02 - The real thing: lang-core and react-lang

**What this step adds:** the official packages in place of the hand-written
parser. The catalog is now defined with Zod through
`@openuidev/react-lang`'s `defineComponent()` and `createLibrary()`; the
system prompt is generated from that catalog by `library.prompt()` and cached
in `prompt.txt`; a real model streams OpenUI Lang over SSE into the page,
where `<Renderer>` (which wraps `@openuidev/lang-core`'s streaming parser)
re-parses the text on every chunk and renders the catalog's React
components. React without JSX, bundled once by esbuild.

## Quick demo

```
python demo.py
```

```text
== 1. the system prompt library.prompt() generates (signatures section) ==
Stack(children: any[], direction?: "column" | "row", gap?: "s" | "m" | "l") — Lays children out in a column or a row
Text(text: string, size?: "small" | "body" | "heading") — A run of text
Metric(label: string, value: string | number, delta?: string) — One number with a label and an optional change
Table(columns: string[], rows: (string | number)[][]) — A table with column headers and rows of cells
BarChart(title: string, labels: string[], values: number[]) — A bar chart with one series
Card(title: string, children: any[]) — A bordered box with a title and children
Button(label: string, action: string, variant?: "primary" | "secondary") — A button that fires an action name
Input(name: string, placeholder?: string, type?: "text" | "email" | "number") — A single-line text field
(48 lines, 3163 characters in prompt.txt)

== 2. the model streams OpenUI Lang into <Renderer> ==
prompt: show me a dashboard for a lemonade stand
root = Stack([header, metrics, salesChart, inventoryTable, orderForm], "column", "m")

header = Text("Lemonade Stand Dashboard", "heading")

metrics = Stack([metricRevenue, metricCupsSold, metricProfit], "row", "l")
metricRevenue = Metric("Revenue", 120.50, "+5%")
metricCupsSold = Metric("Cups Sold", 75, "+10%")
metricProfit = Metric("Profit", 45.30, "+8%")

salesChart = BarChart("Daily Sales", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [10, 15, 12, 20, 18, 25, 22])

inventoryTable = Card("Inventory", [Table(["Item", "Quantity"], [["Lemons", 30], ["Sugar (cups)", 20], ["Ice (bags)", 15], ["Cups", 50]])])

orderForm = Card("Place Order", [Input("orderName", "Your Name"), Input("orderQuantity", "Quantity", "number"), Button("Submit Order", "submitOrder", "primary")])
status: 9 statements, 0 unresolved -> demo.png
```

Recorded with `gpt-4.1-mini`. The whole system prompt is in
[`prompt.txt`](prompt.txt).

![demo](demo.png)

## Files

```text
step_02_openui_react_lang/
├── server.py           static files plus POST /generate: the model's text deltas as SSE, system prompt from prompt.txt
├── llm.py              OpenAI-compatible streaming call; API_KEY, BASE_URL, MODEL from the env or ~/.simple-harness/env
├── nodetools.py        runs npm install, npm run build (esbuild) and node prompt.mjs from Python, on Windows too
├── library.mjs         the catalog: eight defineComponent() calls with Zod props and React renderers; createLibrary()
├── prompt.mjs          prints library.prompt(); server.py caches the output in prompt.txt
├── prompt.txt          the generated system prompt, sent as the system message
├── app.mjs             the page: a prompt box, an SSE reader, <Renderer> from @openuidev/react-lang; React without JSX
├── index.html          the page shell; loads static/bundle.js
├── style.css           the page styles for the catalog components
├── tests/library.test.mjs   node --test: the generated prompt, createParser on toJSONSchema(), renderToString(<Renderer>)
├── test_step.py        offline pytest: fake model behind the SSE route, prompt caching, then npm test
├── demo.py             prints the prompt signatures, runs the live model call in headless Chromium, saves demo.png
├── demo.png            the recorded page
├── package.json        pinned @openuidev/lang-core, @openuidev/react-lang, react, react-dom, zod, esbuild; scripts build, prompt, test
├── package-lock.json   the lockfile for the pinned versions
├── .gitignore          node_modules/ and static/bundle.js (rebuilt by nodetools.py)
└── README.md           this file
```

## The idea

Step 01 showed the mechanism. This step shows the contract the library puts
around it. Three things are generated from one source, the Zod schemas in
`library.mjs`:

- the **prompt**: one signature line per component, in Zod key order, plus
  the language rules and the streaming advice (`root` first, then
  components, then data);
- the **parser's parameter map**: `library.toJSONSchema()` is the same
  `$defs` shape as step 01's `catalog.json`, and `createStreamingParser()`
  reads it to map positional arguments to prop names;
- the **renderers**: each `defineComponent()` carries the React function
  that draws the element node.

Because all three come from one place, adding a component to the catalog
changes the prompt, the parser and the renderer together. The State of
Generative UI report calls this the declarative mode's main advantage over
open-ended HTML: the model can only produce what the catalog allows, and
the catalog is code, not prose.

### Why a bundler here, and which one

Steps that use plain `.mjs` need no build. This step cannot avoid one:
`@openuidev/react-lang`'s ESM build imports the bare specifiers `react`,
`react/jsx-runtime`, `@openuidev/lang-core` and `@openuidev/observability`,
and React 19 on npm ships CommonJS only, so a browser has nothing to
resolve those against. It also reads `process.env.NODE_ENV`. The smallest
fix is one esbuild command with no config file and no dev server:

`package.json`:

```json
"build": "esbuild app.mjs --bundle --format=esm --outfile=static/bundle.js --define:process.env.NODE_ENV=\\\"production\\\" --log-level=warning"
```

`nodetools.py` runs it when `static/bundle.js` is missing or older than the
sources, so `python demo.py` and `python server.py` work from a fresh
checkout. Vite would do the same job with a config file and a dev server;
esbuild was chosen because the step needs neither.

## The code, piece by piece

The catalog. Key order in `z.object()` is the positional argument order the
model must use; the renderer receives `{ props, renderNode }` and calls
`renderNode` on child element nodes:

`library.mjs`:

```js
const Metric = defineComponent({
  name: "Metric",
  description: "One number with a label and an optional change",
  props: z.object({
    label: z.string(),
    value: z.union([z.string(), z.number()]),
    delta: z.string().optional().describe('such as "+12%"'),
  }),
  component: ({ props }) =>
    h("div", { className: "metric" },
      h("div", { className: "label" }, props.label),
      h("div", { className: "value" }, String(props.value)),
      h("div", { className: `delta ${String(props.delta ?? "").startsWith("-") ? "down" : "up"}` }, props.delta ?? "")),
});
...
export const library = createLibrary({
  components: [Stack, Text, Metric, Table, BarChart, Card, Button, Input],
  root: "Stack",
});
```

The prompt, generated and printed. `server.py` caches it in `prompt.txt`
and sends it as the system message:

`prompt.mjs`:

```js
import { library, PROMPT_OPTIONS } from "./library.mjs";

process.stdout.write(library.prompt(PROMPT_OPTIONS));
```

The model call follows the harness convention: `API_KEY`, `BASE_URL`,
`MODEL` from the environment or `~/.simple-harness/env`, streamed deltas:

`llm.py`:

```python
def stream_completion(messages: list[dict]) -> Iterator[str]:
    """Yield the text deltas of one streamed chat completion."""
    from openai import OpenAI

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True, temperature=0)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

The server forwards every delta as one SSE message and never parses the
program itself:

`server.py`:

```python
    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")  # the stream ends when the socket closes
        self.end_headers()
        program = []
        for delta in llm.stream_completion(messages_for(body.get("prompt", ""), self.system_prompt)):
            program.append(delta)
            self.wfile.write(f"data: {json.dumps(delta)}\n\n".encode())
            self.wfile.flush()
```

The page accumulates the deltas in one string and hands it to
`<Renderer>`. Everything about parsing, forward references and partial
statements happens inside that component:

`app.mjs`:

```js
  async function run(text) {
    setResponse("");
    setStreaming(true);
    let program = "";
    try {
      await generate(text, (delta) => { program += delta; setResponse(program); });
    } finally {
      setStreaming(false);
      window.openui.lastResponse = program;
    }
  }
...
      h("section", { id: "ui" },
        h(Renderer, { response, library, isStreaming: streaming, onParseResult: setParse,
          onAction: (event) => console.log("action", event) })),
```

The Node tests use the same library server-side: `createParser` on
`library.toJSONSchema()`, and `renderToString` on `<Renderer>`:

`tests/library.test.mjs`:

```js
test("<Renderer> renders the catalog components from OpenUI Lang", () => {
  const response = 'root = Stack([m, t])\nm = Metric("Cups", 241, "+8%")\nt = Table(["A"], [[1]])\n';
  const html = renderToString(h(Renderer, { response, library, isStreaming: false }));
  assert.match(html, /class="metric"/);
  assert.match(html, /<div class="value">241<\/div>/);
  assert.match(html, /<td>1<\/td>/);
});
```

## Run it

```
npm install                 # once; pinned versions, see package.json
npm run prompt > prompt.txt # optional: python does this when the file is stale
python server.py            # builds static/bundle.js if needed, then http://127.0.0.1:8004/
python demo.py              # prompt section, live model call, demo.png
python -m pytest -q         # offline; runs npm install and npm test when needed
```

`npm install` runs the package's telemetry postinstall; `nodetools.py` sets
`OPENUI_TELEMETRY_DISABLED=1` for every npm and node call it makes.

## What to notice

- The model's program in the demo has blank lines and an inline
  `Table(...)` inside a `Card`. The parser accepts both; the prompt asks
  for references "for better streaming", and the model mostly obeys.
- The `.describe()` texts on props do not appear in the signature lines;
  the description on the component does. Put anything the model must know
  about an argument into the component description or `additionalRules`.
- `parse.meta.errors` carries codes (`unknown-component`,
  `missing-required`, `excess-args`). The page shows the count; a
  production app would send them back to the model as a repair turn.
- `library.toJSONSchema()` is the step 01 catalog format. Step 03 uses it
  to parse the benchmark samples with the real `createParser`.

## Diff from the previous step

- `openui_parse.py`, `openui-parse.mjs`, `render.mjs`, `catalog.json` are
  gone; `library.mjs` (Zod + React renderers) replaces all four.
- `prompt.mjs` and `prompt.txt` are new: the system prompt is generated,
  not written.
- `server.py` gains `POST /generate` and `llm.py`; the SSE route streams a
  model instead of a file.
- `app.mjs` replaces `app.js`: React, `<Renderer>`, bundled by esbuild into
  `static/bundle.js` (gitignored, rebuilt by `nodetools.py`).
- `package.json` has dependencies now; `test_step.py` installs them when
  `node_modules` is missing.
