# Step 04 - OpenUI's html artifact: catalog by default, open-ended where needed

**What this step adds:** the report's hybrid pattern on the step 02 stack.
The Zod catalog keeps its eight components and gains two more: `Markdown`
for conversational text and `HtmlArtifact`, whose second argument is a
whole HTML/CSS/JavaScript document the model writes when, and only when,
the user asks for something interactive. The renderer shows a "Generating
artifact ..." status and the raw source while the document streams, then
Raw and Rendered tabs, the rendered tab being a sandboxed iframe with a
Content Security Policy injected into the document first. The prompt rules
and the two examples come from OpenUI's own html-artifact example; the
model call is the harness codelab's OpenAI-compatible `llm.py`, not OpenUI
Cloud.

## Quick demo

```
python demo.py
```

```text
== 1. a dashboard: catalog primitives only ==
prompt: show me a dashboard for a lemonade stand
root = Stack([title, metrics, salesChart, inventoryTable, actions])
title = Text("Lemonade Stand Dashboard", "heading")
metrics = Stack([revenueMetric, profitMetric, cupsSoldMetric], "row", "l")
revenueMetric = Metric("Revenue", 1250, "+5%")
profitMetric = Metric("Profit", 450, "+8%")
cupsSoldMetric = Metric("Cups Sold", 300, "-2%")
salesChart = BarChart("Daily Sales This Week", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], [40, 50, 45, 60, 55, 70, 80])
inventoryTable = Card("Inventory Status", [Table(["Item", "Quantity", "Status"], [["Lemons", 50, "Good"], ["Sugar (lbs)", 20, "Low"], ["Ice (lbs)", 15, "Good"], ["Cups", 100, "Good"]])])
actions = Stack([restockButton, salesReportButton], "row", "m")
restockButton = Button("Restock Inventory", "restock", "primary")
salesReportButton = Button("View Sales Report", "view_report")
tokens (API): 1235 prompt, 262 completion; no HtmlArtifact, 262 program tokens
artifacts on the page: 0, status: 11 statements, 0 unresolved, 1235 prompt + 262 completion tokens -> demo_catalog.png

== 2. an interactive request: Markdown plus HtmlArtifact ==
mid-stream: Generating artifact ... 460 characters so far -> demo_streaming.png
prompt: build me an interactive lemonade price calculator I can play with
root = Stack([intro, artifact])
intro = Markdown("Here's an interactive lemonade price calculator. Adjust the price per cup and the number of cups sold to see your total revenue.")
artifact = HtmlArtifact("Lemonade Price Calculator", "<!doctype html><html><head><style>body{font-family:system-ui;padding:1rem;max-width:400px;margin:auto}label{display:block;margin-top:1rem}input[type=number]{width:100%;padding:.5rem;font-size:1rem}output{display:block;margin-top:1rem;font-weight:bold;font-size:1.25rem}</style></head><body><h1>Lemonade Price Calculator</h1><label>Price per cup ($):<input type='number' id='price' min='0' step='0.01' value='1.00'></label><label>Number of cups sold:<input type='number' id='cups' min='0' step='1' value='10'></label><output id='total'>Total Revenue: $10.00</output><script>const priceInput=document.getElementById('price');const cupsInput=document.getElementById('cups');const totalOutput=document.getElementById('total');function updateTotal(){const price=parseFloat(priceInput.value)||0;const cups=parseInt(cupsInput.value)||0;const total=(price*cups).toFixed(2);totalOutput.textContent='Total Revenue: $'+total;}priceInput.addEventListener('input',updateTotal);cupsInput.addEventListener('input',updateTotal);updateTotal();</script></body></html>")
tokens (API): 1238 prompt, 341 completion; artifact document 292 of 341 program tokens (86%)
iframe: sandbox='allow-scripts', CSP meta first in <head>: True
moved INPUT:number inside the sandbox: document text changed: True ['Total Revenue: $90.00']
events accepted from the iframe: (none)
```

Recorded with `gpt-4.1-mini`. The completion token count from the API
equals the `o200k_base` count of the program in both runs, so the 86% share
is exact. The whole system prompt is in [`prompt.txt`](prompt.txt).

The dashboard prompt: catalog components only, no artifact.

![catalog only](demo_catalog.png)

The calculator prompt while the document streams: the Markdown intro is
already rendered, the artifact shows its status line and the raw source so
far.

![streaming](demo_streaming.png)

The same reply once complete, after the headless test typed `9` into the
price field inside the sandboxed iframe: the total changed from $10.00 to
$90.00, so the document's script ran under the CSP.

![demo](demo.png)

## Files

```text
step_04_openui_html_artifact/
├── server.py             static files plus POST /generate: text deltas as SSE, then event: done with the API's token usage
├── llm.py                OpenAI-compatible streaming call with stream_options usage; API_KEY, BASE_URL, MODEL from the env or ~/.simple-harness/env
├── nodetools.py          runs npm install, npm run build (esbuild) and node prompt.mjs from Python, on Windows too
├── artifact.py           finds HtmlArtifact(title, document) statements in a program; o200k_base token counts for the demo
├── library.mjs           the catalog: step 02's eight components plus Markdown and HtmlArtifact; PROMPT_OPTIONS with the example's rules
├── html-artifact.mjs     the HtmlArtifact renderer: status while streaming, Raw and Rendered tabs, the sandboxed iframe
├── sandbox.mjs           the CSP, sandboxed() that injects it first in <head>, checkDocument(), isEvent()
├── markdown.mjs          a dependency-free Markdown subset rendered straight to React elements
├── prompt.mjs            prints library.prompt(PROMPT_OPTIONS); server.py caches the output in prompt.txt
├── prompt.txt            the generated system prompt, sent as the system message
├── app.mjs               the page: prompt box, SSE reader, <Renderer>, the message listener for the iframe
├── index.html            the page shell; loads static/bundle.js
├── style.css             step 02's styles plus the Markdown and artifact styles
├── tests/library.test.mjs   node --test: the catalog, the prompt rules, the partial document while streaming, <Renderer> in both states
├── tests/sandbox.test.mjs   node --test: CSP injection, document checks, the accepted message shape, the Markdown subset
├── test_step.py          offline pytest: fake model behind the SSE route with usage, artifact extraction, then npm test
├── demo.py               two live prompts in headless Chromium, three screenshots, a click inside the sandbox
├── demo_catalog.png      the dashboard reply: catalog primitives only
├── demo_streaming.png    the calculator reply mid-stream: status line and raw source
├── demo.png              the calculator reply rendered in its iframe, after the click
├── package.json          pinned @openuidev/lang-core, @openuidev/react-lang, react, react-dom, zod, esbuild
├── package-lock.json     the lockfile for the pinned versions
├── .gitignore            node_modules/ and static/bundle.js (rebuilt by nodetools.py)
└── README.md             this file
```

## The idea

The State of Generative UI report (June 2026) draws its hybrid pattern as a
catalog of `Heading`, `Card`, `BarChart` and `Button` next to one
`GeneratedView` in a sandboxed iframe: catalog primitives by default,
open-ended generation only where the catalog does not reach. Sub-theme 01
built that by hand. OpenUI ships a reference implementation of the same
idea, `examples/miscellaneous/html-artifact` in the
[thesysdev/openui](https://github.com/thesysdev/openui) repository, and
documents it in the "Open-ended HTML" guide at
https://openui.com/docs/agent/guides/open-ended-html. Its library has three
components: a `Response` root, `Markdown` for normal replies, and
`HtmlArtifact(title, document)`. The model decides per reply. Most replies
are a `Markdown`; "build me a sorting visualizer" is an `HtmlArtifact`.

This step puts that on the step 02 stack, with two changes:

- the catalog is real: the eight step 02 components stay, so a dashboard
  request renders as `Metric`, `BarChart`, `Table` and `Button`, and the
  prompt says so ("Never put a dashboard into an HtmlArtifact");
- the hardening the example's README defers to "before production" is
  done: a CSP injected into the document, a validation pass over it, and a
  check on every message that crosses the iframe boundary.

The mechanism is the same as the example's. There is no second endpoint
and no tool call. The document is the second string argument of one
OpenUI Lang statement, it streams like any other string, and the streaming
parser exposes the partial value on every chunk. `useIsStreaming()` tells
the renderer when to stop showing source and start the iframe.

## The code, piece by piece

The component. Its Zod schema is two strings; the renderer reads the
library's streaming flag and switches views on it:

`html-artifact.mjs`:

```js
function HtmlArtifactRenderer({ props }) {
  const isStreaming = useIsStreaming();
  // Raw while the document streams in, Rendered once it is complete; the
  // reader can switch back to Raw with the tabs.
  const [view, setView] = useState(isStreaming ? "raw" : "rendered");
  useEffect(() => {
    if (!isStreaming) setView("rendered");
  }, [isStreaming]);
  const problems = checkDocument(props.document);
...
    isStreaming || view === "raw"
      ? h("pre", { className: "artifact-raw" }, props.document)
      : h("iframe", {
          title: props.title,
          className: "artifact-frame",
          sandbox: "allow-scripts",
          referrerPolicy: "no-referrer",
          srcDoc: sandboxed(props.document),
        }),
...
export const HtmlArtifact = defineComponent({
  name: "HtmlArtifact",
  description: "A self-contained interactive HTML/CSS/JavaScript document, run in a sandboxed iframe once it has fully arrived",
  props: z.object({
    title: z.string(),
    document: z.string().describe("a complete HTML document with inline CSS and JS"),
  }),
  component: HtmlArtifactRenderer,
});
```

The sandbox. `sandbox="allow-scripts"` gives the document a unique origin
and no access to the host; the CSP, injected first in `<head>`, takes the
network away from inline code too. A CSP the model wrote itself is
removed first so the document cannot loosen the policy:

`sandbox.mjs`:

```js
export const CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:";

export const META = `<meta http-equiv="Content-Security-Policy" content="${CSP}">`;
...
export function sandboxed(html) {
  const cleaned = html.replace(CSP_META_RE, "");
  const head = /<head[^>]*>/i.exec(cleaned);
  if (head) return cleaned.slice(0, head.index + head[0].length) + META + cleaned.slice(head.index + head[0].length);
  return META + cleaned;
}
...
export function isEvent(data) {
  return data !== null && typeof data === "object" && data.type === "event" && typeof data.name === "string";
}
```

The catalog and the prompt options. The rules are the example's
`src/lib/prompt-options.ts`, with the two additions for this catalog:

`library.mjs`:

```js
export const library = createLibrary({
  components: [Stack, Text, Metric, Table, BarChart, Card, Button, Input, Markdown, HtmlArtifact],
  root: "Stack",
});
...
export const PROMPT_OPTIONS = {
  preamble: "You answer with OpenUI Lang only, no prose outside the program.",
  additionalRules: [
    "Use the catalog components (Metric, BarChart, Table, Card, Input, Button, Text) for dashboards, reports and forms. Never put a dashboard into an HtmlArtifact.",
    "Use Markdown for normal conversation. A reply that needs no components is a Stack with a single Markdown child.",
    "Only use HtmlArtifact when the user explicitly asks you to build something interactive: an app, game, simulation, calculator, visualization, or similar experience. Introduce it with a short Markdown child first.",
    "When you use HtmlArtifact, generate a self-contained HTML/CSS/JavaScript experience in the document argument. It may be a complete HTML document or a fragment.",
    "Inside an HtmlArtifact document: use inline CSS and JavaScript only. Do not depend on external scripts, stylesheets, fonts, images, or network requests.",
    "Do not wrap the document in Markdown fences.",
```

The page's side of the iframe boundary. The document may post messages;
the host keeps one shape and drops everything else:

`app.mjs`:

```js
  // Messages from the artifact iframe: keep the one accepted shape, drop the rest.
  useEffect(() => {
    const onMessage = (e) => {
      if (!isEvent(e.data)) return;
      setEvents((list) => [...list, e.data.name]);
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);
```

The model call asks the API for its usage so the demo can report the
share of the completion the document took:

`llm.py`:

```python
    stream = client.chat.completions.create(
        model=MODEL, messages=messages, stream=True, temperature=0,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if usage is not None and getattr(chunk, "usage", None):
            usage["prompt_tokens"] = chunk.usage.prompt_tokens
            usage["completion_tokens"] = chunk.usage.completion_tokens
```

The server stays a relay. The usage rides on the `done` event:

`server.py`:

```python
        program, usage = [], {}
        for delta in llm.stream_completion(messages_for(body.get("prompt", ""), self.system_prompt), usage):
            program.append(delta)
            self.wfile.write(f"data: {json.dumps(delta)}\n\n".encode())
            self.wfile.flush()
        LAST["program"], LAST["usage"] = "".join(program), usage
        self.wfile.write(f"event: done\ndata: {json.dumps({'usage': usage})}\n\n".encode())
```

The Node test that pins the streaming behaviour: the partial document is
visible while its string is still open, and `<Renderer>` shows the status
line, not an iframe, while `isStreaming` is true:

`tests/library.test.mjs`:

```js
test("the streaming parser exposes the partial document while the string is still open", () => {
  const sp = createStreamingParser(schema, "Stack");
  const cut = PROGRAM.indexOf("<button");
  let result = sp.push(PROGRAM.slice(0, cut));
  const art = result.root.props.children[1];
  assert.equal(art.typeName, "HtmlArtifact");
  assert.equal(art.partial, true);
  assert.ok(art.props.document.endsWith("<body>"));
  assert.equal(result.meta.incomplete, true);
  result = sp.push(PROGRAM.slice(cut));
  assert.equal(result.meta.incomplete, false);
  assert.equal(result.root.props.children[1].props.document, DOC);
});

test("<Renderer> shows the status line and the raw source while streaming", () => {
  const html = renderToString(h(Renderer, { response: PROGRAM, library, isStreaming: true }));
  assert.match(html, /Generating artifact \.\.\. \d+ characters so far/);
  assert.match(html, /data-state="streaming"/);
  assert.ok(html.includes('<pre class="artifact-raw">'));
  assert.ok(!html.includes("<iframe"));
});
```

## Run it

```
npm install                 # once; pinned versions, see package.json
npm run prompt > prompt.txt # optional: python does this when the file is stale
python server.py            # builds static/bundle.js if needed, then http://127.0.0.1:8006/
python demo.py              # two live prompts, three screenshots
python -m pytest -q         # offline; runs npm install and npm test when needed
```

`npm install` runs the package's telemetry postinstall; `nodetools.py` sets
`OPENUI_TELEMETRY_DISABLED=1` for every npm and node call it makes.

## What to notice

- The decision is the model's, steered by two prompt rules. In the
  recorded runs the dashboard request produced eleven catalog statements
  and no artifact; the calculator request produced a `Markdown` and one
  `HtmlArtifact`. The example's rule "only when the user explicitly asks
  for something interactive" is what makes the hybrid a hybrid.
- The artifact took 86% of the completion. That is the report's cost of
  open-ended generation, and here it is paid only for the one component
  that needs it; the dashboard reply stayed at 262 tokens.
- The document arrives inside one string, so `parse.meta.incomplete` is
  true for most of the stream and the partial value grows on every chunk.
  The raw view is a real progress indicator, not a spinner.
- What the example leaves out, and this step adds: the CSP (the example's
  iframe has `sandbox` and `referrerpolicy` only, so an inline
  `fetch()` or `<script src>` would still reach the network);
  `checkDocument()`, which lists external resources, network calls and
  meta refresh next to the artifact; and `isEvent()`, so a document that
  posts `{bogus: 1}` to the parent is ignored. The example's own README
  names all three as work to do before production.
- `HtmlArtifact` is rendered by React through `srcDoc`, so a re-parse that
  leaves the document unchanged does not reload the iframe. The Raw tab
  unmounts it, so the document's state resets on the way back.
- `Markdown` renders to React elements, never to an HTML string. Model
  text with `<img onerror=...>` in it comes out as text.

## Diff from the previous step

Step 03 is a benchmark with no page; the code base for this step is step
02, and `count_tokens()` in `artifact.py` uses step 03's `o200k_base`
encoding.

- `html-artifact.mjs`, `sandbox.mjs`, `markdown.mjs` are new; `library.mjs`
  imports the first and the last and adds `Markdown` and `HtmlArtifact`
  to the catalog with the example's `PROMPT_OPTIONS` (`additionalRules`
  and `examples`).
- `llm.py` asks for `stream_options={"include_usage": True}`; `server.py`
  sends the usage on the `done` event and keeps it in `LAST`.
- `app.mjs` reads the `done` payload, shows the token counts in the status
  line, and listens for iframe messages through `isEvent()`.
- `artifact.py` is new: `find_artifacts()` and `count_tokens()` for the
  demo and the tests.
- `demo.py` runs two prompts and saves three screenshots; `test_step.py`
  gains the usage event, the artifact extraction and the CSP checks;
  `tests/sandbox.test.mjs` is new.
