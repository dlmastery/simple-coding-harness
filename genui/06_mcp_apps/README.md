# 06 - MCP Apps: UI in a host you do not control

The second transport in the State of Generative UI report (June 2026,
https://www.openui.com/blog/state-of-generative-ui-report). Sub-theme 02
put the agent inside a product you own. Here the agent lives in someone
else's chat client, and you ship the interface to it as an MCP resource:
a `ui://` URI, an HTML document, a tool that points at it, and a JSON-RPC
bridge over `postMessage` between the sandboxed iframe and the host. The
spec is SEP-1865, kept in the ext-apps repository
(https://github.com/modelcontextprotocol/ext-apps). All three steps use
the Python `mcp` package (FastMCP) on the server and no SDK anywhere else.

Steps, in order:

1. `step_01_mcp_app_resource` - a FastMCP server whose tool result carries
   a view (`content` for the model, `structuredContent` for the iframe,
   `_meta.ui.resourceUri` to link them), and a minimal browser host that
   connects over streamable HTTP, mounts the HTML in a sandboxed iframe
   with a content security policy built from the resource's metadata, and
   relays the spec's messages. The model picks the tool.
2. `step_02_mcp_app_in_a_real_host` - the same server, unchanged, in the
   harness codelab's step 26 MCP client extended into a text host, with
   the configuration for Claude Desktop and Goose, and the comparison with
   AG-UI: one interface, two transports, ship both.
3. `step_03_mcp_app_hybrid` - the report's hybrid pattern inside the same
   host: the tool returns a small static spec the view renders with its
   own catalog, plus one open-ended HTML region the server obtains from
   the model, mounted one boundary deeper in a nested sandboxed iframe
   with its own content security policy.

## Layout

```text
06_mcp_apps/
├── README.md
├── step_01_mcp_app_resource/
│   ├── server.py          the MCP server: tool, ui:// resource, _meta link
│   ├── data.py            deterministic sales rows
│   ├── view.html          the view the resource serves
│   ├── host.py            the browser host's process and model call
│   ├── host.html          the host page: CSP, sandboxed iframe, chat
│   ├── mcp-http.mjs       MCP client for the browser
│   ├── bridge.mjs         the host side of the postMessage bridge
│   ├── llm.py             one model call
│   ├── bridge.test.mjs    node --test
│   ├── test_step.py       offline pytest
│   ├── demo.py            the recorded run, saves demo.png
│   ├── demo.png
│   ├── package.json
│   └── README.md
├── step_02_mcp_app_in_a_real_host/
│   ├── .agents/mcp.json   the server over stdio, for the harness
│   ├── harness/           the harness codelab's step 26 loop as a text host
│   ├── server.py          unchanged from step 01
│   ├── data.py            unchanged
│   ├── view.html          unchanged
│   ├── host.py            unchanged
│   ├── host.html          unchanged
│   ├── mcp-http.mjs       unchanged
│   ├── bridge.mjs         unchanged
│   ├── llm.py             unchanged
│   ├── bridge.test.mjs    unchanged
│   ├── test_step.py       step 01's tests plus the harness as a host
│   ├── demo.py            the recorded run, in the terminal
│   ├── package.json
│   └── README.md
└── step_03_mcp_app_hybrid/
    ├── server.py          the lemonade_report tool: components + generated; bundles the view's modules into the resource
    ├── report.py          the static spec, the generation prompt, the server's model call, the fallback region
    ├── data.py            unchanged
    ├── view.html          the hybrid view: step 01's bridge, a catalog, a nested sandbox
    ├── catalog.mjs        four renderers keyed by component name
    ├── sandbox.mjs        the inner boundary: CSP, meta injection, the one accepted event shape
    ├── host.py            step 01's host on port 8768; the app's context goes into the next turn
    ├── host.html          step 01's page, showing the model context
    ├── mcp-http.mjs       unchanged
    ├── bridge.mjs         unchanged
    ├── llm.py             complete() for the host, generate() for the server
    ├── bridge.test.mjs    unchanged
    ├── catalog.test.mjs   node --test for the catalog and the inner boundary
    ├── test_step.py       offline pytest with two fake models
    ├── demo.py            the recorded run, saves demo.png and demo_generated.png
    ├── demo.png
    ├── demo_generated.png
    ├── package.json
    └── README.md
```

Step 02 is step 01 plus a second host: every server and browser-host file
is byte-for-byte the same, and the new files are the harness copy and the
stdio configuration that points it at the server. Step 03 keeps step 01's
bridge, client and resource policy unchanged and changes what the tool
returns and what the view does with it: the report's hybrid, with the
open-ended part in a second sandbox inside the first.
