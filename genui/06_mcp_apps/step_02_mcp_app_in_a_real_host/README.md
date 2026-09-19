# Step 02 - The same server in a real host: the harness, then Claude Desktop

**What this step adds:** the lemonade server from step 01, unchanged,
plugged into a host that was not written for it. The harness codelab's
step 26 MCP client (`harness/`, copied into this step) becomes an MCP Apps
host in text: it remembers which tools carry a `ui://` resource, reads the
resource once, and after the tool call draws the result's
`structuredContent` as a card in the terminal, under the tool panel. The
model still reads only the text `content`. The step also gives the exact
configuration for Claude Desktop and Goose, two hosts that mount the same
resource in a real sandboxed iframe, and closes with the comparison to
sub-theme 02: one interface, two transports.

## Quick demo

```bash
python demo.py
```

```text
$ MCP_ALLOW=mcp__lemonade__* python -m harness.agent -p "Show me the lemonade stand dashboard for the last 5 days. Answer in one sentence."

  2,093 prompt · 23 completion · 1,792 cached
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ mcp__lemonade__lemonade_dashboard 5                                     │
  │ ─────────────────────────────────────────────────────────────────────── │
  │ Lemonade stand, last 5 days: 132 cups, $198.00 revenue, best day Tue.   │
  │ Mon: 37 cups at 28 C ($55.50)                                           │
  │ Tue: 51 cups at 30 C ($76.50)                                           │
  │ Wed: 9 cups at 19 C ($13.50)                                            │
  │ Thu: 19 cups at 21 C ($28.50)                                           │
  │ Fri: 16 cups at 19 C ($24.00)                                           │
  └─────────────────────────────────────────────────────────────────────────┘
  ┌─ app · Lemonade dashboard ──────────────────────────────────────────────┐
  │ ui://lemonade/dashboard.html | text/html;profile=mcp-app | 7,876 bytes  │
  │ | csp: restrictive default | rendered as text                           │
  │ ─────────────────────────────────────────────────────────────────────── │
  │ days: 5                                                                 │
  │ rows:                                                                   │
  │   day  temperature  cups  revenue                                       │
  │   ---  -----------  ----  -------                                       │
  │   Mon           28    37     55.5                                       │
  │   Tue           30    51     76.5                                       │
  │   Wed           19     9     13.5                                       │
  │   Thu           21    19     28.5                                       │
  │   Fri           19    16       24                                       │
  │ summary:                                                                │
  │   total_cups: 132                                                       │
  │   total_revenue: 198                                                    │
  │   best_day: Tue                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
  2,227 prompt · 46 completion · 2,048 cached

answer: In the last 5 days at the lemonade stand, 132 cups were sold generating $198.00 in revenue, with the best day being Tuesday with 51 cups sold at 30°C earning $76.50.
```

The first panel is the tool result as the model saw it: text. The second
is the MCP App as this host can show it: the resource's identity and
policy, then the structured data as a table. The demo script leaves out
the harness's late-injection panels; everything else is the harness's
output as printed. A run in Claude Desktop was not recorded (see below).

## Files

```text
step_02_mcp_app_in_a_real_host/
├── .agents/mcp.json  the lemonade server over stdio, the way the harness finds it
├── harness/          the harness codelab's step 26 loop, extended into a text MCP Apps host (mcp_client.py, ui_text.py, ui.py, agent.py)
├── server.py         FastMCP server, unchanged from step 01: the tool, the ui:// resource, the _meta link; --stdio here
├── data.py           the stand's sales, deterministic so the tests are exact
├── view.html         the MCP App, unchanged from step 01
├── host.py           step 01's browser host process, unchanged
├── host.html         step 01's host page, unchanged
├── mcp-http.mjs      step 01's browser MCP client, unchanged
├── bridge.mjs        step 01's host bridge, unchanged
├── llm.py            one model call over the OpenAI-compatible API, key from the env or the key file
├── bridge.test.mjs   node --test for the bridge and the browser client, unchanged
├── test_step.py      offline pytest: step 01's suite plus the harness as a host, a fake session then the real server over stdio
├── demo.py           runs the harness in print mode with the server over stdio and prints the run
├── package.json      npm test = node --test bridge.test.mjs (no dependencies)
└── README.md         this file
```

## The idea: ship both

Step 01 built a host to prove the protocol. Real hosts are built by other
people, and each one decides what it can show. The State of Generative UI
report's rule for this side of the map is to ship both: a text result that
stands on its own, and a UI resource for hosts that can mount it. The
lemonade server already does. `content` is the whole dashboard in prose;
`structuredContent` is the same numbers as data; the resource is the view.

This step puts one server in front of three hosts:

| Host | Declares the extension | Reads the resource | Shows |
|---|---|---|---|
| the browser host (step 01) | yes | yes | the HTML in a sandboxed iframe |
| the harness (this step) | no | yes | the data as a text card; the model gets the text |
| Claude Desktop, Goose | yes | yes | the HTML inline in the conversation |

The server changed for none of them. That is the point of the transport:
the interface is a resource the host fetches, and the host decides.

## The code, piece by piece

### 1. The server joins the harness through its config file

`.agents/mcp.json`:

```json
{
  "servers": {
    "lemonade": {
      "command": "python",
      "args": ["server.py", "--stdio"]
    }
  }
}
```

Step 26's client speaks stdio, so the server runs with `--stdio`: the same
FastMCP instance, `server.run(transport="stdio")` instead of uvicorn. The
harness starts it as a child process before the first turn and registers
its one tool as `mcp__lemonade__lemonade_dashboard`.

### 2. Registration remembers the view

`harness/mcp_client.py`:

```python
UI_MIME_TYPE = "text/html;profile=mcp-app"
UI_TOOLS = {}      # mcp__<server>__<tool> -> the ui:// resource its result should render with
UI_RESOURCES = {}  # (server, uri) -> {"title", "mimeType", "size", "csp"}, read once per session
PENDING_APPS = []  # (mcp__<server>__<tool>, server, uri, result): cards to draw after the tool panel
...
def ui_resource_uri(tool):
    """The ui:// resource a tool asks to be rendered with, from _meta.ui.resourceUri, or None."""
    meta = getattr(tool, "meta", None) or {}
    return (meta.get("ui") or {}).get("resourceUri") or meta.get("ui/resourceUri")
...
    for tool in tools:
        name = tool_name(server, tool.name)
        if ui_resource_uri(tool):
            UI_TOOLS[name] = ui_resource_uri(tool)
```

The Python SDK exposes `_meta` as `tool.meta`. The deprecated flat key
`ui/resourceUri` is read too, because older servers still send it.

### 3. The call queues a card; the model's text does not change

`harness/mcp_client.py`:

```python
    text = "\n".join(parts) or "(no content)"
    if getattr(result, "isError", False):
        text = f"Error: {text}"
    uri = UI_TOOLS.get(tool_name(server, tool))
    if uri and not getattr(result, "isError", False):
        PENDING_APPS.append((tool_name(server, tool), server, uri, result))
    return history.cap(text)


def show_pending(name):
    """Draw the card queued for one tool call, if any. The loop calls this after the tool panel."""
    for entry in PENDING_APPS:
        if entry[0] == name:
            PENDING_APPS.remove(entry)
            show_app(*entry[1:])
            return True
    return False
```

`call_tool` runs from a thread pool, before the loop has printed anything
about the call. So the card waits in `PENDING_APPS`, and the loop draws it
right after the tool panel. The string the function returns is the same as
in step 26: the model never learns that a card was drawn.

`harness/agent.py`:

```python
            ui.tool(tool_call.function.name, args, result)
            mcp_client.show_pending(tool_call.function.name)  # the app's data as a text card, right under its tool
```

### 4. What the host learns from the resource

`harness/mcp_client.py`:

```python
def read_ui_resource(server, uri):
    """What a host learns from resources/read, kept per session: title, MIME type, size, CSP."""
    from . import ui_text

    if (server, uri) not in UI_RESOURCES:
        contents = client().read(server, uri).contents[0]
        html = getattr(contents, "text", None) or ""
        meta = getattr(contents, "meta", None) or {}
        UI_RESOURCES[(server, uri)] = {
            "title": ui_text.title_of(html) or uri,
            "mimeType": contents.mimeType,
            "size": len(html.encode("utf-8")),
            "csp": (meta.get("ui") or {}).get("csp") or {},
        }
    return UI_RESOURCES[(server, uri)]
```

A host reads the resource with `resources/read`, once, and may cache it:
the resource is a static template. This host keeps four facts about it
and shows them in the card's subtitle. A resource whose MIME type is not
`text/html;profile=mcp-app` is noted and not rendered, which is what the
spec asks of every host.

### 5. Any structuredContent as text

`harness/ui_text.py`:

```python
def lines(value, indent=0):
    """The value as a list of text lines."""
    pad = "  " * indent
    if is_table(value):
        return [pad + row for row in table(value)]
    if isinstance(value, dict):
        out = []
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                out.append(f"{pad}{key}:")
                out.extend(lines(item, indent + 1))
            else:
                out.append(f"{pad}{key}: {scalar(item)}")
        return out
```

The renderer knows nothing about lemonade. A list of flat dicts with the
same keys is a table with a header, numbers right-aligned. A dict is
`key: value` lines, nested values indented. It is the terminal's version
of a generic view: less than the HTML, more than nothing.

### 6. The card

`harness/ui.py`:

```python
    def app(self, title, subtitle, body_lines):
        """An MCP App rendered as text: what the sandboxed view would have drawn, as a card."""
        body = Group(Text(subtitle, style=f"italic {MUTED}"), Rule(style=MUTED), Text("\n".join(body_lines)))
```

## In a real iframe host

Claude Desktop, Claude.ai, VS Code, Goose, Postman and MCPJam render MCP
Apps. The server needs no change. Two configurations, both stdio:

Claude Desktop, in `claude_desktop_config.json` (Settings, Developer,
Edit Config), with the absolute path of this step's `server.py`:

```json
{
  "mcpServers": {
    "lemonade": {
      "command": "python",
      "args": ["C:/path/to/genui/06_mcp_apps/step_02_mcp_app_in_a_real_host/server.py", "--stdio"]
    }
  }
}
```

Goose, in `~/.config/goose/config.yaml` under `extensions`, or through
`goose configure`, Add Extension, Command-line Extension, with the same
command.

What to expect after a restart: the tool appears in the host's tool list
with its description. Ask "show me the lemonade stand dashboard for the
last week". The host calls the tool, reads `ui://lemonade/dashboard.html`,
and mounts it inline: the same cards, bars and table as step 01's
screenshot, in the host's theme, because `view.html` reads the host's CSS
variables at `ui/initialize`. The "14 days" button calls the tool again
through the host. "Tell the chat" sends `ui/message`, and the host adds it
to the conversation as a user turn. The model's transcript holds only the
text content, exactly as in the harness above.

For a host without a chat, the ext-apps reference host runs from a clone
of https://github.com/modelcontextprotocol/ext-apps: `npm install`, then
in `examples/basic-host`, `SERVERS='["http://127.0.0.1:8765/mcp"]' npm start`
with `python server.py` running, and http://localhost:8080 lists the tool.

**Not recorded here.** Claude Desktop is installed on the machine this
step was built on, but running the server inside it means editing that
machine's desktop configuration and driving the desktop application by
hand, so no such run was recorded. What did run, and is recorded above
and in step 01: the harness as a text host over stdio, and the browser
host over streamable HTTP with the view in a sandboxed iframe.

## Compare with sub-theme 02: one interface, two transports

The lemonade dashboard could also be an AG-UI state object rendered by a
page you own, as sub-theme 02 does. Same numbers, same picture, different
contract:

| | AG-UI (sub-theme 02) | MCP Apps (this sub-theme) |
|---|---|---|
| who owns the page | you | the host's vendor |
| the wire | your server streams events over SSE to your page | the host calls your MCP server; the view speaks JSON-RPC to the host |
| what the agent emits | events: text, tool calls, state deltas | a tool result: text content plus structured content |
| who renders | your renderer, from state | your HTML, inside the host's sandbox |
| who runs the loop | you | the host |
| who validates the UI | your renderer, against your catalog | the host: nothing beyond the MIME type and its sandbox; the view is trusted to draw the server's own data |
| where it can appear | your product | Claude, ChatGPT, VS Code, Goose, any compliant host |

The report's rule is not to choose. Keep the interface as data, render it
with your own page where you own the product, and ship the same data with
a `ui://` view where you do not. Sub-theme 07 takes the first road inside
the harness; this step took the second.

## Why: what breaks without it

Step 01's host is a page written for the demo. The claim of MCP Apps is
that the *same* server works in a host it never met, including one that
cannot show HTML at all. Without this step that claim rests on the
vendors' hosts, which cannot be driven from a test. Putting the server
behind the codelab's own harness shows the fallback path the extension
requires: a text host reads `content`, ignores the view, and still
answers the user; the app card is what a host can add when it wants to
show that a view exists without running it.

## Run it

Prerequisites: `pip install mcp openai rich` (the harness) plus the
step 01 packages for the browser host; an API key in `API_KEY`/
`OPENAI_API_KEY` or `~/.simple-harness/env` for the agent; no Node, no
Playwright. Run the harness **from this step's directory**:
`.agents/mcp.json` names `server.py` relative to the current directory
(`resolve_arg` makes a relative path absolute only when it exists from
the cwd), and from anywhere else the server "fails to start".

bash:

```bash
export API_KEY=sk-...
python demo.py                                            # the recorded run above
MCP_ALLOW=mcp__lemonade__* python -m harness.agent        # interactive; /mcp lists the server
python server.py                                          # step 01's browser host, unchanged:
python host.py                                            #   the MCP server, then the page on :8766
python -m pytest -q test_step.py
```

PowerShell:

```
$env:API_KEY = "sk-..."
python demo.py
$env:MCP_ALLOW = "mcp__lemonade__*"; python -m harness.agent
python server.py
python host.py
python -m pytest -q test_step.py
```

Expected output: the `Quick demo` transcript above (the model's sentence
differs; the two panels are the check). Leave the interactive agent with
ctrl-d (ctrl-z then enter on Windows), ctrl-c at the prompt, or an empty
line: this harness copy has no `/exit` command.

`MCP_ALLOW` lets the tool run without a prompt; without it, the harness
asks before every MCP call, as step 26 decided. Tests:
`python -m pytest test_step.py` runs step 01's suite plus the harness as a
host: a fake session for the card logic, then the real `server.py --stdio`
as a child process. No network, no key.

## Error handling

The harness copy is step 26's, with this round's rule applied to
`decide()`, `run()` and `settle()` in `harness/tools.py`: every
`tool_call` gets exactly one tool message.

- Arguments that are not a JSON object: the tool message is
  `Error: the arguments of <name> are not a JSON object: <reason>`; the
  call never reaches a permission check.
- A tool the model named that does not exist (a server that went away,
  a typo): `Error: no tool named '<name>'.`
- An exception inside a tool (an MCP server that raised, a missing file):
  `Error: <Type>: <message>`; a non-string result is JSON-encoded, `None`
  is `(no output)`.
- `bash` without `command`, `write_file` without `path`,
  `browser_open` without `url`: `Blocked by policy: <name>: missing
  argument '<key>'` (`permissions.check` reads with `.get`).
- The lemonade server not starting (wrong cwd, no `mcp` package): the
  server is listed as failed at start-up and its tools are absent; the
  agent runs without them.
- A dead model call and ctrl-c mid-turn behave as in step 26 (the main
  codelab's README for that step describes them); this copy is not
  updated with the main codelab's later loop changes.

## Gotchas / What this is not

- `PENDING_APPS` pairs cards with tool panels by tool *name*, in FIFO
  order: two parallel calls to the same tool in one reply get their
  cards in call order, which is right only because the loop draws
  panels in the same order. A subagent's calls never drain the queue, so
  it is cleared at the end of every turn rather than left to surface
  under a later call of the same name.
- The card is text: `ui_text.py` renders any JSON as an outline. It
  never runs the view's HTML and never will; that is the point of the
  step, not a limitation to fix.
- The host does not declare the `io.modelcontextprotocol/ui` extension
  (see "What to notice"); a server that hides `_meta.ui` from
  non-declaring hosts shows no card here.

## What to notice

- The server did not change between the three hosts. The host decides
  what it can show; the server ships text, data and a view, and does not
  know which one is on screen.
- This host does not declare the `io.modelcontextprotocol/ui` extension.
  Declaring it promises to mount HTML. A strict server would then hide
  the `_meta.ui` from this host, and the tool would still work, because
  the text content is complete on its own.
- The card is drawn after the tool panel, not inside the call. The call
  runs on a pool thread; the terminal is written by the loop, in order.
- `structuredContent` never reached the model. In the demo, the model's
  prompt grew by the text lines only; the table came from the data the
  view would have used.
- The resource was read once. Hosts may prefetch and cache it at
  connection time; this one reads it lazily, on the first call, and keeps
  it for the session.

## Diff from the previous step

- `harness/`: step 26's harness, with `config.py` on the series
  convention (`OPENAI_API_KEY` fills `API_KEY`; OpenAI defaults).
- `harness/mcp_client.py`: `UI_TOOLS`, `UI_RESOURCES`, `PENDING_APPS`,
  `ui_resource_uri`, `Client.read`, `read_ui_resource`, `show_app`,
  `show_pending`; `register` and `call_tool` feed them.
- `harness/ui_text.py`: new, the JSON-to-text renderer.
- `harness/ui.py`: `app()`, and UTF-8 stderr in print mode.
- `harness/agent.py`: one line after `ui.tool`.
- `.agents/mcp.json`: the lemonade server over stdio.
- `demo.py`: runs the harness in print mode instead of the browser.
- `server.py`, `view.html`, `host.py`, `host.html`, `bridge.mjs`,
  `mcp-http.mjs`: unchanged from step 01.

## What the next step adds

Step 03 makes the view itself hybrid: a fixed catalog region drawn from
`structuredContent`, plus a model-generated HTML region the server
produces on each call, in a second sandbox inside the view.
