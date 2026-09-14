# Step 02 - TrueForge's generative UI, rendered in a page of ours

Step 01 taught the local harness to draw. TrueForge, the hosted harness of
Part 7, already does that: with `generative_ui` enabled its agent answers a
dashboard request with an OpenUI Lang program inside a ```openui fence, and
the TrueForge chat UI renders it as React components. This step captures
such a reply over the Python SDK and renders the program itself.

**What this step adds:** `client/genui.py` opens a TrueForge session with
generative UI on, streams one turn, and extracts the OpenUI Lang program
from the reply. `openui_parse.py` and `web/openui-parse.mjs` parse the
language (statements, lists, inline calls, `+`, forward references,
incomplete lines held back). `web/render.mjs` draws the tree, and
`server.py` streams the program to the page one line per SSE event, so the
skeleton of forward references is visible before their lines arrive.

## Quick demo

```
python demo.py              # live: one turn on http://localhost:8790, then the page
python demo.py --offline    # replays sample_reply.md, no TrueForge needed
```

Recorded output of `python demo.py` (the streamed reply and the tree are
shortened with `...`; the full reply is in `sample_reply.md`):

````text
TrueForge at http://localhost:8790, model openai/gpt-4-1-mini
> Show a lemonade stand report: a table of the top three flavours with cups and price, a line chart of weekly revenue for four weeks, two KPI numbers, a status tag, and a closing sentence.

```openui
root = Stack([title, topFlavoursTable, revenueLineChartCard, kpiStack, statusTag, closingText], "column", "l", "center")

title = TextContent("Lemonade Stand Report", "large-heavy")
topFlavoursTable = Card([
  CardHeader("Top 3 Flavours - Cups Sold & Price"),
  Table([
    Col("Flavour", ["Classic Lemon", "Strawberry", "Mint"]),
    Col("Cups Sold", [150, 120, 100], "number"),
    Col("Price per Cup ($)", [1.50, 1.75, 1.60], "number")
  ])
])
...
kpiStack = Stack([
  Card([TextContent("Total Cups Sold", "small"), TextContent("370", "large-heavy")]),
  Card([TextContent("Average Price per Cup ($)", "small"), TextContent("1.62", "large-heavy")])
], "row", "xl", "center", "evenly")
statusTag = Tag("Performance", null, "md", "success")
closingText = TextContent("Sales are strong and trending upward, keep focusing on the top flavours to maximize revenue.", "default")
```
[6,954 input, 352 output tokens]

--- extracted program: 32 lines, 7 statements ---
Stack('column', 'l', 'center')
  TextContent('Lemonade Stand Report', 'large-heavy')
  Card()
    CardHeader('Top 3 Flavours - Cups Sold & Price')
    Table()
      Col('Flavour')
        ['Classic Lemon', 'Strawberry', 'Mint']
...
  Tag('Performance', None, 'md', 'success')

page: http://127.0.0.1:50522
saved demo_stream.png (forward references still pending)
saved demo.png (program complete)
````

The page mid-stream, 25 lines in. The root line named six children on
line 1; three are still dashed placeholders:

![demo mid-stream](demo_stream.png)

The page once the program is complete:

![demo](demo.png)

## Files

```text
step_02_trueforge_generative_ui/
├── client/
│   ├── __init__.py   exports ask, extract_program, open_session
│   └── genui.py      a TrueForge session with generative UI on; streams one turn and pulls the openui fence out of the reply
├── openui_parse.py   the OpenUI Lang parser, streaming-first: feed(), tree() with Pending references, outline()
├── server.py         http.server + SSE: streams the program to the page one line per event; /reply for the raw text
├── web/
│   ├── index.html    the page shell: the rendered tree beside the program text
│   ├── app.js        one SSE line at a time into the parser, the tree redrawn after every line
│   ├── openui-parse.mjs   the same parser in JavaScript
│   └── render.mjs    DOM renderer keyed by TrueForge component name; unknown box and dashed pending placeholder
├── openui-parse.test.mjs   node --test: the JS parser must agree with openui_parse.py on the same program
├── test_step.py      offline pytest: both parsers, the extractor, the SDK against a fake TrueForge, the page server
├── demo.py           live turn on TrueForge (or --offline replay), then the page and two screenshots
├── demo_stream.png   the page mid-stream, forward references still pending
├── demo.png          the page once the program is complete
├── sample_reply.md   the recorded reply, replayed by --offline and the tests
├── package.json      npm test = node --test (no dependencies)
└── README.md         this file
```

## The idea: the same language, a different renderer

The State of Generative UI report (June 2026) calls OpenUI Lang the most
token-efficient of the declarative formats and the one built for
streaming. TrueForge uses it as its wire format: the agent writes the
program as text inside its reply, and the chat client parses it as tokens
stream in. Nothing about that is tied to the TrueForge UI. The program is
a string, the fence marks where it starts, and any parser that knows the
grammar can draw it. So this step takes the reply over the SDK and gives
the program to a renderer of its own.

Two properties of the language make the page work the way it does:

- **Forward references.** The first line, `root = Stack([title, ...])`,
  names children whose lines come later. The parser keeps the reference
  and resolves it when the line lands; until then the tree carries a
  `Pending` node, which the page draws as a dashed box.
- **Line-oriented statements.** A statement is complete when its brackets
  balance, so the parser can commit a line the moment it ends and hold back
  one that is still open. The server exploits that: one line per SSE event.

## The code, piece by piece

`client/genui.py` opens the session. The only difference from Part 7's
client is the `config`: generative UI switched on for this inline agent.

```python
def open_session():
    """A session on an inline agent with generative UI switched on."""
    spec = AgentSpec(
        model=Model(name=MODEL),
        instructions=INSTRUCTIONS,
        config=RuntimeConfig(generative_ui=GenerativeUiConfig(enabled=True)),
    )
    session = client().sessions.create(agent=SessionAgentSpecBody(spec=spec))
    return session.data.id
```

The reply is prose around one fence. `extract_program()` returns what is
inside it, and copes with a fence that never closed because the stream was
cut:

```python
FENCE = re.compile(r"```openui[^\n]*\n(.*?)```", re.DOTALL)
```

```python
def extract_program(reply):
    """The OpenUI Lang program inside the first ```openui fence, or None.

    Text around the fence is prose for the chat; the fence is the interface.
    An unterminated fence (a reply cut mid-stream) still yields what arrived.
    """
    match = FENCE.search(reply)
    if match:
        return match.group(1).strip("\n")
```

`openui_parse.py` is the parser. `feed()` commits a statement at the first
newline where the text before it balances; an open list waits for its
closing bracket:

```python
    def feed(self, text):
        """Add a chunk. Every complete statement it finishes is parsed now."""
        self.buffer += text
        while True:
            # the first newline at which the text before it is balanced ends a statement
            start, cut = 0, None
            while cut is None:
                nl = self.buffer.find("\n", start)
                if nl == -1:
                    return  # the rest is an unfinished line: hold it back
                if complete(self.buffer[:nl]):
                    cut = nl
                start = nl + 1
            line, self.buffer = self.buffer[:cut], self.buffer[cut + 1:]
            self.add_line(line.replace("\n", " "))
```

`resolve()` turns the small AST into plain values. A reference to a
statement that has not arrived becomes a `Pending` node instead of an
error; `+` concatenates when either side is a string, which is how the
agent writes `"" + total`:

```python
        if kind == "add":
            left, right = self.resolve(expr[1], path), self.resolve(expr[2], path)
            if isinstance(left, str) or isinstance(right, str):
                return f"{left}{right}"
            return left + right
        if kind == "call":
            return {"type": expr[1], "args": [self.resolve(a, path) for a in expr[2]]}
        name = expr[1]
        if name in path:
            return {"type": "Cycle", "ref": name}
        if name not in self.statements:
            return {"type": "Pending", "ref": name}
        return self.resolve(self.statements[name].expr, path | {name})
```

`web/openui-parse.mjs` is the same parser in JavaScript, tested with
`node --test` against the same program so the two cannot disagree:

```js
  tree(name = "root") {
    if (!this.statements.has(name)) return { type: "Pending", ref: name };
    return this.resolve(this.statements.get(name), new Set([name]));
  }
```

`web/render.mjs` maps each component name to a function of its positional
args. Unknown components and pending references still draw something, so
a new component in a future TrueForge release never blanks the page:

```js
  if (node.type === "Pending") return el("div", "pending", `waiting for ${node.ref}`);
  if (node.type === "Cycle") return el("div", "pending", `cycle at ${node.ref}`);
  const draw = RENDERERS[node.type];
  if (draw) return draw(node.args);
  const box = el("div", "unknown");
  box.append(el("strong", "", node.type), el("code", "", JSON.stringify(node.args)));
  return box;
```

`web/app.js` feeds every SSE line to the parser and redraws the whole tree
from `root` after each one. Redrawing is cheap at this size and keeps the
page a pure function of the statements seen so far:

```js
  lines += 1;
  const span = document.createElement("span");
  span.className = "new";
  span.textContent = line + "\n";
  for (const old of program.querySelectorAll(".new")) old.className = "";
  program.append(span);
  parser.feed(line + "\n");
  redraw();
```

`server.py` streams the lines. A `null` event says the program is over, so
the page can call `close()` on the parser and flush a last unterminated
line:

```python
            for line in program.splitlines():
                self.wfile.write(f"data: {json.dumps(line)}\n\n".encode("utf-8"))
                self.wfile.flush()
                time.sleep(delay)
            self.wfile.write(b"data: null\n\n")
```

## Run it

```
python demo.py                    # live turn on TrueForge, then the page and two screenshots
python demo.py --offline          # the recorded reply, same page
python -m pytest test_step.py     # offline: fake TrueForge over SSE, parser tests, node --test
npm test                          # the JS parser tests on their own
```

`TRUEFORGE_BASE_URL` (default `http://localhost:8790`) and `TRUEFORGE_MODEL`
(default `openai/gpt-4-1-mini`) select the server. The tests never use
them: they start a fake TrueForge on an ephemeral port and point the real
`trueforge_sdk` at it.

## What to notice

- The agent was told nothing about OpenUI Lang. The catalog, the grammar
  and the fence come from TrueForge's own harness prompt (1,288 of the
  6,954 input tokens are labelled `harness` in the turn's usage
  breakdown). Enabling `generative_ui` is the whole configuration.
- The program is 32 lines and 352 output tokens for a title, a table, a
  line chart, two KPI cards, a tag and a sentence. The step 01 model wrote
  308 tokens of JSON for a comparable dashboard through a tool call; the
  report's token argument for OpenUI Lang is about larger UIs, and about
  streaming: here every line is drawable the moment it ends.
- Multi-line statements happen. The second recorded run wrote `Card([` on
  one line and closed it four lines later; the parser's balance check is
  what makes that harmless, in Python and in the page.
- The renderer's positional args are a reading of what the agent emitted
  (`Stack(children, direction, gap, align, justify, wrap)`,
  `LineChart(categories, series, variant, xLabel, yLabel)`), not a copy of
  TrueForge's component library. Anything outside that reading lands in
  the `unknown` box with its args visible, which is the honest fallback.

## Diff from the previous step

- `harness/` is gone: the loop runs inside TrueForge. `client/genui.py`
  replaces it with one session and one streamed turn over `trueforge_sdk`.
- The wire format changes from a json-render element map, pushed whole per
  `render_ui` call, to an OpenUI Lang program streamed one line per event.
  `openui_parse.py` and `web/openui-parse.mjs` are new; `web/render.mjs`
  replaces step 01's `web/app.js` renderer with one keyed by TrueForge's
  component names.
- `server.py` keeps step 01's `http.server` + SSE shape and adds `/reply`
  for the raw text. The terminal surface is now `openui_parse.outline()`,
  a tree of the parsed program, instead of a `rich` panel.
- Tests gain a fake TrueForge (`FakeTrueForge` in `test_step.py`) and a
  `node --test` suite for the JS parser.
