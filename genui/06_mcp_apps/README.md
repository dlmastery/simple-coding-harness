# 06 - MCP Apps: UI in a host you do not control

The second transport in the State of Generative UI report (June 2026,
https://www.openui.com/blog/state-of-generative-ui-report). Sub-theme 02
put the agent inside a product you own. Here the agent lives in someone
else's chat client, and you ship the interface to it as an MCP resource:
a `ui://` URI, an HTML document, a tool that points at it, and a JSON-RPC
bridge over `postMessage` between the sandboxed iframe and the host. The
spec is SEP-1865, kept in the ext-apps repository
(https://github.com/modelcontextprotocol/ext-apps). Both steps use the
Python `mcp` package (FastMCP) on the server and no SDK anywhere else.

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
└── step_02_mcp_app_in_a_real_host/
    ├── .agents/mcp.json   the server over stdio, for the harness
    ├── harness/           the harness codelab's step 26 loop as a text host
    ├── server.py          unchanged from step 01
    ├── data.py            unchanged
    ├── view.html          unchanged
    ├── host.py            unchanged
    ├── host.html          unchanged
    ├── mcp-http.mjs       unchanged
    ├── bridge.mjs         unchanged
    ├── llm.py             unchanged
    ├── bridge.test.mjs    unchanged
    ├── test_step.py       step 01's tests plus the harness as a host
    ├── demo.py            the recorded run, in the terminal
    ├── package.json
    └── README.md
```

Step 02 is step 01 plus a second host: every server and browser-host file
is byte-for-byte the same, and the new files are the harness copy and the
stdio configuration that points it at the server.
