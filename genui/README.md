# Zero to Hero: Generative UI

## When the agent's answer is an interface, not a paragraph

The harness codelab in the parent directory builds the loop behind a coding
agent. This series builds what the user sees. A generative UI is an
interface the agent composes at run time: a metric card, a table, a form
that asks the next question, a chart. The agent still calls a model in a
loop. The difference is what the loop emits and what renders it.

The map for this series comes from the State of Generative UI report
(June 2026, https://www.openui.com/blog/state-of-generative-ui-report). It
separates two choices that are often mixed up.

**Transport: where the UI appears.**

| You want the agent inside | Use | Sub-theme |
|---|---|---|
| your own product | AG-UI, an event protocol over SSE | 02 |
| a host you do not control (Claude, ChatGPT, VS Code, Goose) | MCP Apps, sandboxed HTML resources over MCP | 06 |

**Generation: what the agent emits.**

| Mode | The agent emits | Who decides the layout | Sub-theme |
|---|---|---|---|
| static | a component name and its props | you, ahead of time | 01 |
| declarative | a spec from a catalog: a JSON tree, a flat element map, a DSL | the agent, inside your catalog | 01, 03, 04, 05 |
| open-ended | raw HTML, CSS and JavaScript | the agent, alone, in a sandboxed iframe | 01 |

The declarative middle is where the open formats compete: A2UI from Google,
OpenUI Lang from Thesys, json-render from Vercel. They differ in wire
format, token cost, streaming behaviour and renderer coverage. Sub-theme
04 measures them side by side.

Every step is a directory you can run. Every step has an offline test.
Every step's README opens with a **quick demo**: the command, its recorded
output, and a screenshot when there is a page.

**What you will build**

```text
01  foundations       static, declarative and open-ended generation with no framework,
                      then the hybrid escape hatch; measured in tokens
02  AG-UI             the transport: run lifecycle, text, tool calls and shared state as
                      events; then the harness codelab's loop speaking AG-UI
03  A2UI              Google's protocol: surfaces, flat component lists, data binding,
                      client-to-server actions, the official Lit renderer, A2UI over AG-UI
04  OpenUI Lang       the line-oriented DSL: a parser written by hand, the real React
                      renderer, and the token benchmark across four formats
05  json-render       Vercel's element map: catalog, JSON Patch streaming, actions, two
                      renderers for one spec
06  MCP Apps          UI inside a host you do not control: a tool result that carries an
                      HTML resource, a minimal host, and the harness as a host
07  in the harness    a render_ui tool for the stage 15 harness, and TrueForge's built-in
                      generative UI captured over its SDK
```

## Before you start

```bash
git clone https://github.com/dlmastery/simple-coding-harness
cd simple-coding-harness
pip install -r requirements.txt
pip install ag-ui-protocol a2ui-core jsonschema tiktoken
python -m playwright install chromium        # for the demo screenshots
```

Put your key where the harness codelab reads it: `API_KEY` in the
environment or in `~/.simple-harness/env` as `OPENAI_API_KEY=...`. Steps
with a browser part have a `package.json`; `npm install` in the step
directory fetches the one or two packages they use. Node 22 is required.

```bash
python run_tests.py genui/01          # one sub-theme, offline, no key
python run_tests.py genui             # every genui step
python check_snippets.py genui/03     # every snippet in those READMEs exists in the code
```

## How to read a step

Each step README follows one shape: **What this step adds**, the **quick
demo**, the idea in the report's terms, **the code piece by piece** with
every snippet verified against the source, **run it**, **what to notice**,
and the diff from the previous step. Read the sub-theme README first; it
says what its steps add in order.

<!-- SUBTHEMES -->

<!-- SUBTHEME 06 -->
# Sub-theme 06: MCP Apps, UI in a host you do not control

AG-UI puts the agent in your product. MCP Apps put your UI in someone
else's: Claude, ChatGPT, VS Code, Goose. The tool result carries a
pointer to an HTML resource. The host mounts it in a sandboxed iframe and
talks to it over `postMessage` with the same JSON-RPC shape MCP already
uses.

## Step 06.1: An MCP App from scratch

**Goal.** One tool, one HTML resource, one minimal host.

**The idea.** The tool returns two things: text for the model and
structured content for the view. Its metadata points at the resource.
The resource is a self-contained HTML document with a small bridge. The
host declares the UI extension, mounts the document with a content
security policy built from the resource's metadata, delivers the tool
input and result, and proxies the view's own tool calls back to the
server. Nothing here needs an SDK, which is the point of reading the
specification.

`06_mcp_apps/step_01_mcp_app_resource/server.py`:

```python
@server.tool(meta={"ui": {"resourceUri": VIEW_URI}})
def lemonade_dashboard(days: int = 7) -> types.CallToolResult:
    """Sales dashboard for the lemonade stand over the last `days` days (1 to 28)."""
    days = max(1, min(int(days), 28))
    rows = data.sales(days)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=data.as_text(days, rows))],
        structuredContent={"days": days, "rows": rows, "summary": data.summary(rows)},
    )


@server.resource(VIEW_URI, name="lemonade_dashboard_view", mime_type=MIME_TYPE, meta=VIEW_META)
def dashboard_view() -> str:
    """The dashboard's HTML document. Static: the data arrives later, over postMessage."""
    return VIEW_FILE.read_text(encoding="utf-8")
```

**Try it.**

```bash
cd genui/06_mcp_apps/step_01_mcp_app_resource
python demo.py
```

**You should see** the host connect, the model call the tool, the
dashboard mount inside the app panel, a click on "14 days" inside the
view trigger a second tool call through the host, and the bridge log of
every message in both directions.

![A minimal MCP Apps host with the lemonade dashboard mounted](06_mcp_apps/step_01_mcp_app_resource/demo.png)

**Takeaway.** The model sees text. The view sees data. The host sees
neither's secrets, and it decides what the iframe may do.

## Step 06.2: The same server in a host not written for it

**Goal.** Put the app in front of a real host, and in front of the
harness codelab's own MCP client.

**The idea.** A terminal cannot mount HTML. The stage 26 MCP client
learns to read the UI metadata, fetch the resource once, and draw the
structured content as a text card under the tool panel, while the model
still sees only the text. The step also gives the Claude Desktop, Goose
and reference-host configuration and what to expect there. Those runs
were not recorded: editing your desktop configuration is your decision.

**Try it.**

```bash
cd genui/06_mcp_apps/step_02_mcp_app_in_a_real_host
python demo.py
```

**You should see** the harness call the tool over stdio, the tool panel
with the model's text, and an app card under it with the resource's
name, size, policy and the structured rows rendered as a table.

**Takeaway.** One interface, two transports. The report's rule is to
ship both, and this sub-theme with sub-theme 02 is what that costs.


<!-- SUBTHEME 02 -->
# Sub-theme 02: AG-UI, the transport

AG-UI is an event protocol. A run is a request. The server streams typed
events back over Server-Sent Events: lifecycle, text, tool calls, state.
Nothing in it says what the UI looks like. That is why it is the transport
the report recommends for an agent inside your own product.

## Step 02.1: An AG-UI server, and a client written by hand

**Goal.** Stream one run's events from a real model call and read them
with `fetch`.

**The idea.** The agent is a plain Python generator that never sees HTTP.
It yields events; the endpoint encodes them one per line. A model
failure becomes a terminal event, not a broken stream. The page reads
the stream with a 25-line SSE reader and a switch on the event type.

`02_ag_ui/step_01_ag_ui_server/agent.py`:

```python
def run(input: RunAgentInput):
    """Yield the events of one run. A model failure becomes RUN_ERROR, not a broken stream."""
    yield RunStartedEvent(thread_id=input.thread_id, run_id=input.run_id)
    message_id = str(uuid4())
    try:
        yield TextMessageStartEvent(message_id=message_id, role="assistant")
        for delta in stream_text(to_openai(input.messages)):
            yield TextMessageContentEvent(message_id=message_id, delta=delta)
        yield TextMessageEndEvent(message_id=message_id)
    except Exception as error:  # noqa: BLE001 - the client must see a terminal event
        yield RunErrorEvent(message=str(error))
        return
    yield RunFinishedEvent(thread_id=input.thread_id, run_id=input.run_id)
```

**Try it.**

```bash
cd genui/02_ag_ui/step_01_ag_ui_server
python demo.py
```

**You should see** the exact wire bytes, one `data:` line per event from
`RUN_STARTED` to `RUN_FINISHED`, the assembled text, and the page
rendering the same reply.

**Takeaway.** The transport is the whole protocol. The events carry text
here; the next step makes them carry UI.

## Step 02.2: Tools and shared state

**Goal.** Generative UI as state, the AG-UI way.

**The idea.** Server tools do not draw. They return JSON Patch operations
against a `dashboard` object. The server applies them, streams them as
`STATE_DELTA`, and the page re-renders from state. One tool belongs to
the page: the server streams the call and ends the run, the page shows
Confirm or Decline, and the answer returns as a tool message on the next
run with no user text.

`02_ag_ui/step_02_ag_ui_tools_and_state/agent.py`:

```python
            waiting_on_client = False
            for call_id, call in calls.items():
                if call["name"] in client_tools:
                    waiting_on_client = True  # the page runs it; its result opens the next run
                    continue
                result, operations = execute(call["name"], json.loads(call["arguments"] or "{}"))
                if operations:
                    apply_patch(state, operations)
                    yield StateDeltaEvent(delta=operations)
                yield ToolCallResultEvent(message_id=str(uuid4()), tool_call_id=call_id, content=result, role="tool")
                messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            if waiting_on_client:
                break
```

**Try it.**

```bash
cd genui/02_ag_ui/step_02_ag_ui_tools_and_state
python demo.py
```

**You should see** three metric tool calls each followed by a state
delta, a table and a chart, then "Buy a new cooler for $40" end the run
at the client tool, and the purchase recorded after the confirm click.

**Takeaway.** State is the UI. A patch stream is a UI stream.

## Step 02.3: The harness codelab's loop, speaking AG-UI

**Goal.** Drive the stage 21 harness from a browser with the official
client.

**The idea.** The harness's model call blocks and reports text through a
callback. A worker thread runs it and pushes every callback onto a
queue; a generator drains the queue. From there every part of the loop
maps to an event: deltas to text content, assembled tool calls to tool
call events, tool results to results, permission questions to custom
events, the todo list to a state delta, and the usage dict to the
finished event. The page only subscribes.

`02_ag_ui/step_03_ag_ui_from_the_harness/bridge.py`:

```python
def streamed(messages):
    """call_llm as a generator: ("delta", text) while it streams, then ("message", (message, usage)).

    call_llm blocks and reports text through a callback. A worker thread runs
    it and pushes every callback onto a queue; this generator drains the queue.
    """
    items = queue.Queue()

    def worker():
        try:
            result = call_llm(messages, on_delta=lambda text: items.put(("delta", text)))
            items.put(("message", result))
        except Exception as error:  # noqa: BLE001 - re-raised on the generator side
            items.put(("error", error))

    threading.Thread(target=worker, daemon=True).start()
    while True:
        kind, payload = items.get()
        if kind == "error":
            raise payload
        yield kind, payload
        if kind == "message":
            return
```

**Try it.**

```bash
cd genui/02_ag_ui/step_03_ag_ui_from_the_harness
npm install && npm run build
python demo.py
```

**You should see** a coding task run from the browser: the file written,
the command run after a permission event, the answer streamed, and a
second task planned with the todo list live in a side panel.

![The harness codelab's loop driven from the browser over AG-UI](02_ag_ui/step_03_ag_ui_from_the_harness/demo.png)

**Takeaway.** The loop did not change. Its callbacks became events, and
a browser became a client.


<!-- SUBTHEME 07 -->
# Sub-theme 07: Generative UI in the harness

The two codelabs meet here. The harness codelab built a loop and moved it
onto TrueForge. This series showed the formats an agent can emit instead
of prose. Sub-theme 07 puts a rendering surface on both harnesses.

## Step 07.1: A render_ui tool for the stage 15 harness

**Goal.** One agent, two surfaces: the terminal and a browser page.

**The idea.** The stage 15 loop gains one tool. Its argument is a
json-render element map, `{root, elements: {id: {type, props, children}}}`,
validated against a six-component catalog that is also written into the
system prompt. The model never sees the picture. It sees a short result
string. The surfaces interpret the spec.

`07_harness_genui/step_01_render_ui_tool/harness/tools.py`:

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

**Try it.**

```bash
cd genui/07_harness_genui/step_01_render_ui_tool
python -m harness.agent --web
> show me a dashboard for a lemonade stand
```

**You should see** a panel tree in the terminal, nested cards with a bar
chart, a table and metric tiles, and the same dashboard in the browser
page the `--web` flag opened. The recorded run produced ten elements on
the first call.

**Takeaway.** Errors are results here too: an invalid spec comes back as
text the model can fix, and nothing is drawn.

## Step 07.2: TrueForge's built-in generative UI, rendered by your own page

**Goal.** Capture a hosted harness's UI output and render it yourself.

**The idea.** TrueForge with `generative_ui` enabled answers a report
request with an OpenUI Lang program inside its reply. The step streams
the turn over the SDK, extracts the program, and parses it with a
streaming-first parser written here in Python and JavaScript. Forward
references become pending nodes, so the page shows placeholders before
their definitions arrive. The live agent writes multi-line statements, so
a line is committed only when its brackets balance.

`07_harness_genui/step_02_trueforge_generative_ui/openui_parse.py`:

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

**Try it.**

```bash
cd genui/07_harness_genui/step_02_trueforge_generative_ui
python demo.py
```

**You should see** the raw reply with its OpenUI fence, the extracted
program (32 lines, 7 statements in the recording), a mid-stream
screenshot with dashed "waiting for" placeholders, and the finished page:
a table, a line chart, metric cards and a status tag.

![TrueForge generative UI rendered by the step's own page](07_harness_genui/step_02_trueforge_generative_ui/demo.png)

**Takeaway.** A UI language is only as portable as its parsers. Writing
one shows exactly what the format promises: streaming, forward references
and nothing executable.


## Sub-theme index

| Sub-theme | Steps | Packages |
|---|---|---|
| 01 foundations | static components, declarative tree, open-ended HTML, hybrid escape hatch | none |
| [02 AG-UI](02_ag_ui/) | server, tools and state, from the harness | `ag-ui-protocol`, `@ag-ui/client` |
| 03 A2UI | messages by hand, from a model, Lit renderer over AG-UI | `a2ui-core`, `a2ui-agent-sdk`, `@a2ui/lit` |
| 04 OpenUI Lang | parser, React renderer, format benchmark | `@openuidev/lang-core`, `@openuidev/react-lang`, `tiktoken` |
| 05 json-render | catalog, streaming patches, actions and targets | `@json-render/core`, `@json-render/react` |
| [06 MCP Apps](06_mcp_apps/) | app resource, in a real host | `mcp`, `@modelcontextprotocol/ext-apps` |
| [07 in the harness](07_harness_genui/) | render_ui tool, TrueForge generative UI | `rich`, `trueforge_sdk` |

> **Build status.** Sub-themes with a link in the table above are finished
> and tested. The specification they are built from is `GENUI_SPEC.md`.

MIT licensed. The specifications and libraries this series uses are
Apache-2.0 (A2UI, json-render) and MIT (AG-UI, OpenUI, MCP Apps); each
step README names what it uses.
