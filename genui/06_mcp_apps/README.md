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
