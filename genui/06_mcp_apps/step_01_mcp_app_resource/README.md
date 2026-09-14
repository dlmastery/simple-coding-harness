# Step 01 - An MCP App: a tool result that carries its interface

**What this step adds:** an MCP server whose tool comes with a user
interface, and the smallest host that can show it. `server.py` is a
FastMCP server with one tool, `lemonade_dashboard`, and one resource at
`ui://lemonade/dashboard.html` whose text is a complete HTML document. The
tool's `_meta.ui.resourceUri` points at that resource. `host.html` is the
host: it connects to the server over streamable HTTP, lists the tools,
calls the tool, reads the resource, mounts the HTML in a sandboxed iframe
and relays JSON-RPC messages between the iframe and the server over
`postMessage`. `host.py` serves the page and owns the model call, so the
model picks the tool. This is MCP Apps, SEP-1865, with no SDK on either
side.

## Quick demo

```bash
python demo.py
```

```text
host page: http://127.0.0.1:8766/?prompt=show%20me%20the%20lemonade%20stand%20dashboard%20for%20the%20last%205%20days

user: show me the lemonade stand dashboard for the last 5 days
tool: lemonade_dashboard({"days":5})
assistant: In the last 5 days, your lemonade stand sold 132 cups and earned $198.00. The best day was Tuesday with 51 cups sold and $76.50 revenue.

bridge log (condensed):
  ->         initialize                       extensions: io.modelcontextprotocol/ui
  <-         response #1                      serverInfo.name=lemonade
  ->         notifications/initialized
  ->         tools/list
  <-         response #2                      1 tool(s)
  ->         resources/list
  <-         response #3                      1 resource(s)
  ->         tools/call                       lemonade_dashboard({"days": 5})
  ->         resources/read
  <-         response #4                      structuredContent + content
  <-         response #5                      contents[0].mimeType=text/html;profile=mcp-app
  host       mount ui://lemonade/dashboard.html  csp: default-src 'none'; script-src 'self' ...
  view->host ui/initialize
  host->view response #1                      hostContext + hostCapabilities
  view->host ui/notifications/initialized
  host->view ui/notifications/tool-input      {"days": 5}
  host->view ui/notifications/tool-result
  view->host ui/notifications/size-changed    550x458
  view->host tools/call                       lemonade_dashboard({"days": 14})
  ->         tools/call                       lemonade_dashboard({"days": 14})
  <-         response #6                      structuredContent + content
  host->view response #2                      structuredContent + content
  view->host ui/notifications/size-changed    550x665

screenshot: demo.png
```

`->` and `<-` are the host talking to the MCP server over HTTP.
`view->host` and `host->view` are the iframe and the host over
`postMessage`. The last five lines are the interactive phase: the demo
clicked "14 days" inside the view, and the view called the tool through
the host. Without a key, the demo calls the tool directly and the chat
stays empty; the bridge log is the same.

![demo](demo.png)

## The idea: UI for a host you do not control

Sub-theme 02 put the agent inside a product you own: your page, your
event stream, your renderer. MCP Apps is the other transport in the State
of Generative UI report (June 2026,
https://www.openui.com/blog/state-of-generative-ui-report): the agent lives
in someone else's chat client, such as Claude, ChatGPT, VS Code or Goose, and
you ship the interface to it. You do not control the page, the model or
the loop. You control one MCP server.

So the interface travels as a resource. The server declares it once, with
a `ui://` URI and the MIME type `text/html;profile=mcp-app`. A tool points
at it. When the model calls the tool, a host that supports the extension
reads the resource, puts the HTML in a sandboxed iframe and hands the tool
result to it. A host that does not support the extension shows the tool's
text. The interface is a progressive enhancement, never a requirement.

Three parties, two channels:

```text
MCP server  <-- MCP over HTTP or stdio -->  host  <-- JSON-RPC over postMessage -->  view (iframe)
server.py                                   host.html + host.py                     view.html
```

The view never talks to the server. Every call goes through the host,
which can log it, refuse it, or ask the user. That is the security model:
sandboxed iframe, auditable messages, a content security policy built from
what the resource declared.

## The code, piece by piece

### 1. The server: a tool, a resource, and the link between them

`server.py`:

```python
VIEW_URI = "ui://lemonade/dashboard.html"
VIEW_FILE = Path(__file__).parent / "view.html"
MIME_TYPE = "text/html;profile=mcp-app"
...
VIEW_META = {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": True}}

server = FastMCP("lemonade", host="127.0.0.1", port=PORT, json_response=True, log_level="WARNING")


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

The tool's `meta` becomes `_meta` on the wire; `ui.resourceUri` is the
spec's field. The result has two halves. `content` is text: the model reads
it, and a text-only host shows it. `structuredContent` is data: the view
renders it, and the model never sees it. The resource's `meta` carries the
content security policy. Both lists are empty, so the host allows no
external connection and no external script. The view is self-contained.

`json_response=True` makes the server answer each POST with plain JSON
instead of a short SSE stream. Either works; JSON is easier to read in the
log.

### 2. The view: JSON-RPC over postMessage, in three functions

`view.html`:

```js
  const pending = new Map();
  let nextId = 1;

  function request(method, params) {
    const id = nextId++;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      window.parent.postMessage({ jsonrpc: "2.0", id, method, params }, "*");
    });
  }

  function notify(method, params) {
    window.parent.postMessage({ jsonrpc: "2.0", method, params }, "*");
  }
  ...
  window.addEventListener("message", (event) => {
    const msg = event.data;
    if (!msg || msg.jsonrpc !== "2.0") return;
    if (msg.method) {
      handlers[msg.method]?.(msg.params ?? {}, msg.id);
    } else if (pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    }
  });
```

The spec says a view does not need an SDK to talk to the host, and this
is the proof. A request has an id and gets a response. A notification has
no id. An incoming message with a method is a request or a notification
from the host; one without a method is the answer to something the view
asked. The official `@modelcontextprotocol/ext-apps` package wraps the same
messages in an `App` class with typed handlers.

### 3. The view's lifecycle

`view.html`:

```js
  const handlers = {
    "ui/notifications/tool-input": ({ arguments: args }) => {
      status.textContent = `loading the last ${args.days ?? 7} days...`;
    },
    "ui/notifications/tool-result": (result) => render(result),
    "ui/notifications/tool-cancelled": ({ reason }) => { status.textContent = `cancelled: ${reason}`; },
    "ui/notifications/host-context-changed": (context) => applyContext(context),
    "ui/resource-teardown": (params, id) => respond(id, {}),  // a request: the host waits for the answer
  };
  ...
  (async () => {
    const init = await request("ui/initialize", {
      appInfo: { name: "Lemonade Dashboard", version: "0.1.0" },
      appCapabilities: { availableDisplayModes: ["inline"] },
      protocolVersion: "2025-06-18",
    });
    applyContext(init.hostContext);
    notify("ui/notifications/initialized", {});
    new ResizeObserver(() => {
      notify("ui/notifications/size-changed", { width: document.body.scrollWidth, height: document.body.scrollHeight + 24 });
    }).observe(document.body);
  })();
```

The order is fixed by the spec. The view sends `ui/initialize` and gets
the host's context back: theme, CSS variables, container size, the tool
that opened it. The view says `ui/notifications/initialized`. Only then
does the host send `ui/notifications/tool-input` and
`ui/notifications/tool-result`. The view reports its size after every
render so the host can grow the frame. `ui/resource-teardown` is a request
from the host: the view must answer before the host removes the frame.

The buttons are the interactive phase. "14 days" calls
`request("tools/call", ...)`: the host forwards it to the server and the
result comes back as the response. "Tell the chat" sends `ui/message`,
which the host adds to the conversation as a user turn.

### 4. The host as MCP client: streamable HTTP with fetch

`mcp-http.mjs`:

```js
  async connect() {
    this.server = await this.request("initialize", {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: { extensions: { [UI_EXTENSION]: { mimeTypes: [APP_MIME_TYPE] } } },
      clientInfo: this.hostInfo,
    });
    await this.notify("notifications/initialized");
    return this.server;
  }
```

The host declares the extension `io.modelcontextprotocol/ui` and the MIME
type it can render. A server may check this and register text-only tools
for hosts without it. The rest of the class is one `fetch` per JSON-RPC
message, with the `mcp-session-id` header echoed back once the server has
assigned one.

### 5. The host bridge: capabilities, delivery, proxying

`bridge.mjs`:

```js
  hostCapabilities() {
    return {
      serverTools: {},
      serverResources: {},
      openLinks: {},
      logging: {},
      message: { text: {} },
      updateModelContext: { text: {} },
    };
  }
  ...
  async dispatch(method, params) {
    switch (method) {
      case "ui/initialize":
        return this.initializeResult();
      case "tools/call":
        return this.callTool(params.name, params.arguments ?? {});
      case "resources/read":
        return this.readResource(params.uri);
      case "ui/message":
        await this.onMessage?.(params);
        return {};
      case "ui/open-link":
        await this.onOpenLink?.(params.url);
        return {};
      ...
      default:
        throw new Error(`the host does not support ${method}`);
    }
  }
  ...
  async deliver(args, resultPromise) {
    this.notify("ui/notifications/tool-input", { arguments: args });
    try {
      this.notify("ui/notifications/tool-result", await resultPromise);
    } catch (error) {
      this.notify("ui/notifications/tool-cancelled", { reason: error.message });
    }
  }
```

`hostCapabilities` is what the view learns at `ui/initialize`: this host
proxies tool calls and resource reads, opens links, and accepts chat
messages. `dispatch` is the switch behind every request from the view.
`deliver` sends the two data notifications in order; `notify` holds them
until the view has said initialized. The class has no DOM in it, so the
node tests drive it with plain objects.

### 6. The sandbox and its content security policy

`bridge.mjs`:

```js
export const RESTRICTIVE_CSP = {
  "default-src": ["'none'"],
  "script-src": ["'self'", "'unsafe-inline'"],
  "style-src": ["'self'", "'unsafe-inline'"],
  "img-src": ["'self'", "data:"],
  "media-src": ["'self'", "data:"],
  "font-src": ["'self'"],
  "object-src": ["'none'"],
  "connect-src": ["'none'"],
  "frame-src": ["'none'"],
  "base-uri": ["'self'"],
};
```

`host.html`:

```js
    const meta = uiMetaOf(content, state.listing.get(uri));
    const csp = cspFor(meta);
    ...
    const iframe = document.createElement("iframe");
    iframe.setAttribute("sandbox", "allow-scripts");  // no allow-same-origin: the view gets an opaque origin
    ...
    iframe.srcdoc = withCsp(html, csp);
    $("app").replaceChildren(iframe);
    bridge.deliver(args, resultPromise);
```

`cspFor` starts from the spec's restrictive default and widens only the
directives the resource declared: `connectDomains` opens `connect-src`,
`resourceDomains` opens the script, style, image, font and media sources.
`withCsp` puts the policy in a `<meta>` tag at the top of the document,
and `sandbox="allow-scripts"` without `allow-same-origin` gives the view
an opaque origin: no cookies, no storage, no access to the host page.

This is the one place where the step is smaller than the spec. A
production web host must load the view through a sandbox proxy on a
second origin, with the policy set as an HTTP header the view cannot
rewrite. The ext-apps `basic-host` example does that with a
`sandbox.html` on port 8081. This host collapses the two frames into one
and accepts a `<meta>` policy. The messages are the same.

### 7. The model picks the tool

`host.py`:

```python
SYSTEM_PROMPT = """You are the assistant inside a chat host that can render MCP Apps.
When a tool is the right way to answer, call it. After a tool result, answer in one or two short sentences.
Do not describe the numbers row by row: the user sees the interface."""
...
def chat_turn(messages, tools):
    """One model turn for the page: the system prompt goes in front, the reply comes back as is."""
    return llm.complete([{"role": "system", "content": SYSTEM_PROMPT}] + messages, tools or None)


@app.post("/chat")
def chat(request: ChatRequest):
    return chat_turn(request.messages, request.tools)
```

`host.html`:

```js
      for (const call of reply.tool_calls) {
        const args = JSON.parse(call.arguments || "{}");
        bubble("tool", `${call.name}(${JSON.stringify(args)})`);
        const result = await runTool(call.name, args);
        const summary = result.content.filter((c) => c.type === "text").map((c) => c.text).join("\n");
        state.messages.push({ role: "tool", tool_call_id: call.id, content: summary });  // the model reads text only
      }
```

The page sends the transcript and the server's tool schemas to `/chat`.
The model answers with a tool call; the page runs it over MCP, mounts the
view, and appends only the `content` text as the tool message. The model
then writes one sentence. The structured data went to the iframe and
never entered the context window.

## Run it

```bash
python server.py            # the MCP server, http://127.0.0.1:8765/mcp
python host.py              # the host page, http://127.0.0.1:8766/
```

Open the host page, click Connect, then type a prompt or click "call with
defaults". `python demo.py` starts both, drives a headless browser, prints
the bridge log and saves `demo.png`. `python server.py --stdio` speaks the
protocol over stdin and stdout for desktop hosts; step 02 uses that.

Tests: `python -m pytest test_step.py` runs the server in process, the
streamable HTTP round trip through an in-process ASGI transport with the
extension capability declared, the `/chat` endpoint with a fake model, and
`node --test bridge.test.mjs` for the bridge and the browser client. No
network, no key.

## What to notice

- The tool result has two audiences. `content` is for the model and for
  hosts without UI support. `structuredContent` is for the view. Keep the
  text short and the data complete.
- The resource is static and declared up front. The host can fetch and
  review it before any tool runs. The data arrives later, as a
  notification. Template and data are separate on purpose.
- The host holds the tool input and result until the view has said
  `initialized`. Send them earlier and the view's listener is not there
  yet.
- The view can call tools, but only through the host, and only tools on
  its own server. The host logged every call in the demo. A real host may
  ask the user first.
- Teardown is a request, not a notification. The host asks, the view
  answers, then the frame goes. The demo log shows it when a second tool
  call replaces the first view.
- `visibility: ["app"]` in a tool's `_meta.ui` hides it from the model
  while the view can still call it. `toolsForModel` in `mcp-http.mjs`
  filters on it. A refresh button does not need to be a model tool.
