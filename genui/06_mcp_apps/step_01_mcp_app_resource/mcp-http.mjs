// Step 01 - an MCP client for the browser, over streamable HTTP, with fetch.
//
// The host page is the MCP client. It needs four methods: initialize,
// tools/list, tools/call and resources/read. Each is one JSON-RPC message
// in one POST. The server answers with JSON (or with a short SSE stream:
// both are parsed). A session id travels in the mcp-session-id header once
// initialize has answered. That is the whole transport.

export const UI_EXTENSION = "io.modelcontextprotocol/ui";
export const APP_MIME_TYPE = "text/html;profile=mcp-app";
export const PROTOCOL_VERSION = "2025-06-18";

/** The JSON-RPC messages in a response body: one JSON object, or the data lines of an SSE stream. */
export function parseBody(contentType, text) {
  if ((contentType ?? "").includes("text/event-stream")) {
    return text
      .split(/\r?\n\r?\n/)
      .map((block) => block.split(/\r?\n/).filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).join("\n"))
      .filter(Boolean)
      .map((data) => JSON.parse(data));
  }
  return text.trim() ? [JSON.parse(text)] : [];
}

/** The ui:// resource a tool asks to be rendered with, or undefined for a plain tool. */
export function uiResourceUri(tool) {
  return tool._meta?.ui?.resourceUri ?? tool._meta?.["ui/resourceUri"];
}

/** OpenAI function schemas for the tools the model may see: visibility defaults to model and app. */
export function toolsForModel(tools) {
  return tools
    .filter((tool) => (tool._meta?.ui?.visibility ?? ["model", "app"]).includes("model"))
    .map((tool) => ({
      type: "function",
      function: { name: tool.name, description: tool.description ?? "", parameters: tool.inputSchema },
    }));
}

export class McpHttpClient {
  constructor(url, { fetch: fetchImpl = globalThis.fetch?.bind(globalThis), hostInfo = { name: "genui-minimal-host", version: "0.1.0" }, onWire } = {}) {
    this.url = url;
    this.fetch = fetchImpl;
    this.hostInfo = hostInfo;
    this.onWire = onWire;  // (direction, message) for the log panel
    this.sessionId = null;
    this.nextId = 1;
    this.server = null;
  }

  headers() {
    const headers = {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "MCP-Protocol-Version": PROTOCOL_VERSION,
    };
    if (this.sessionId) headers["mcp-session-id"] = this.sessionId;
    return headers;
  }

  async post(message) {
    this.onWire?.("->", message);
    const response = await this.fetch(this.url, { method: "POST", headers: this.headers(), body: JSON.stringify(message) });
    const session = response.headers.get("mcp-session-id");
    if (session) this.sessionId = session;
    if (response.status === 202) return [];  // a notification: accepted, nothing to read
    if (!response.ok) throw new Error(`MCP server answered ${response.status}`);
    const replies = parseBody(response.headers.get("content-type"), await response.text());
    for (const reply of replies) this.onWire?.("<-", reply);
    return replies;
  }

  async request(method, params = {}) {
    const id = this.nextId++;
    const replies = await this.post({ jsonrpc: "2.0", id, method, params });
    const reply = replies.find((message) => message.id === id);
    if (!reply) throw new Error(`no response to ${method}`);
    if (reply.error) throw new Error(`${method}: ${reply.error.message}`);
    return reply.result;
  }

  async notify(method, params = {}) {
    await this.post({ jsonrpc: "2.0", method, params });
  }

  /** The handshake. The host declares the MCP Apps extension and the MIME type it can render. */
  async connect() {
    this.server = await this.request("initialize", {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: { extensions: { [UI_EXTENSION]: { mimeTypes: [APP_MIME_TYPE] } } },
      clientInfo: this.hostInfo,
    });
    await this.notify("notifications/initialized");
    return this.server;
  }

  async listTools() {
    return (await this.request("tools/list")).tools;
  }

  async callTool(name, args = {}) {
    return this.request("tools/call", { name, arguments: args });
  }

  async readResource(uri) {
    return this.request("resources/read", { uri });
  }

  async close() {
    if (!this.sessionId) return;
    await this.fetch(this.url, { method: "DELETE", headers: this.headers() });
    this.sessionId = null;
  }
}
