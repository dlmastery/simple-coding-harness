// Step 01 - node --test: the host bridge and the browser MCP client, no browser, no network.
import { test } from "node:test";
import assert from "node:assert/strict";

import { HostBridge, cspFor, withCsp, uiMetaOf, RESTRICTIVE_CSP } from "./bridge.mjs";
import { McpHttpClient, parseBody, uiResourceUri, toolsForModel, UI_EXTENSION, APP_MIME_TYPE } from "./mcp-http.mjs";

// --- CSP -------------------------------------------------------------------

test("no csp metadata gives the spec's restrictive default", () => {
  const csp = cspFor({});
  assert.match(csp, /default-src 'none'/);
  assert.match(csp, /connect-src 'none'/);
  assert.match(csp, /frame-src 'none'/);
  assert.match(csp, /script-src 'self' 'unsafe-inline'/);
  assert.equal(Object.keys(RESTRICTIVE_CSP).length, csp.split("; ").length);
});

test("declared domains widen exactly the matching directives", () => {
  const csp = cspFor({ csp: { connectDomains: ["https://api.example.com"], resourceDomains: ["https://cdn.example.com"] } });
  assert.match(csp, /connect-src https:\/\/api\.example\.com/);
  assert.doesNotMatch(csp, /connect-src 'none'/);
  assert.match(csp, /script-src 'self' 'unsafe-inline' https:\/\/cdn\.example\.com/);
  assert.match(csp, /img-src 'self' data: https:\/\/cdn\.example\.com/);
  assert.match(csp, /frame-src 'none'/);
});

test("the csp meta tag lands first in head", () => {
  const html = withCsp("<!doctype html><html><head><title>x</title></head><body></body></html>", "default-src 'none'");
  assert.match(html, /<head><meta http-equiv="Content-Security-Policy" content="default-src 'none'"><title>/);
  assert.match(withCsp("<p>no head</p>", "x"), /^<meta http-equiv/);
});

test("content-level _meta.ui wins over the listing entry", () => {
  const content = { _meta: { ui: { prefersBorder: false } } };
  const listing = { _meta: { ui: { prefersBorder: true, csp: { connectDomains: ["a"] } } } };
  assert.deepEqual(uiMetaOf(content, listing), { prefersBorder: false });
  assert.deepEqual(uiMetaOf({}, listing), listing._meta.ui);
  assert.deepEqual(uiMetaOf({}, undefined), {});
});

// --- the bridge ------------------------------------------------------------

function bridge(extra = {}) {
  const sent = [];
  const b = new HostBridge({
    send: (m) => sent.push(m),
    tool: { name: "lemonade_dashboard", inputSchema: { type: "object" } },
    callTool: async (name, args) => ({ content: [{ type: "text", text: `${name} ${JSON.stringify(args)}` }], structuredContent: { ok: true } }),
    readResource: async (uri) => ({ contents: [{ uri, mimeType: APP_MIME_TYPE, text: "<p>hi</p>" }] }),
    ...extra,
  });
  return { b, sent };
}

test("ui/initialize answers with host info, capabilities and the tool", async () => {
  const { b } = bridge({ hostContext: { theme: "dark" } });
  const reply = await b.handle({ jsonrpc: "2.0", id: 1, method: "ui/initialize", params: { appInfo: { name: "v", version: "1" } } });
  assert.equal(reply.id, 1);
  assert.equal(reply.result.hostInfo.name, "genui-minimal-host");
  assert.ok(reply.result.hostCapabilities.serverTools);
  assert.equal(reply.result.hostContext.theme, "dark");
  assert.equal(reply.result.hostContext.toolInfo.tool.name, "lemonade_dashboard");
});

test("tool input and result wait for initialized, then arrive in order", async () => {
  const { b, sent } = bridge();
  const delivered = b.deliver({ days: 3 }, Promise.resolve({ content: [], structuredContent: { days: 3 } }));
  await delivered;
  assert.equal(sent.length, 0, "nothing crosses before the view says initialized");
  await b.handle({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} });
  assert.deepEqual(sent.map((m) => m.method), ["ui/notifications/tool-input", "ui/notifications/tool-result"]);
  assert.deepEqual(sent[0].params, { arguments: { days: 3 } });
  assert.deepEqual(sent[1].params.structuredContent, { days: 3 });
});

test("a failed tool call becomes ui/notifications/tool-cancelled", async () => {
  const { b, sent } = bridge();
  await b.handle({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} });
  await b.deliver({}, Promise.reject(new Error("server gone")));
  assert.equal(sent.at(-1).method, "ui/notifications/tool-cancelled");
  assert.equal(sent.at(-1).params.reason, "server gone");
});

test("tools/call and resources/read are proxied; unknown methods are refused", async () => {
  const { b } = bridge();
  const call = await b.handle({ jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "lemonade_dashboard", arguments: { days: 14 } } });
  assert.equal(call.result.content[0].text, 'lemonade_dashboard {"days":14}');
  const read = await b.handle({ jsonrpc: "2.0", id: 6, method: "resources/read", params: { uri: "ui://x" } });
  assert.equal(read.result.contents[0].mimeType, APP_MIME_TYPE);
  const bad = await b.handle({ jsonrpc: "2.0", id: 7, method: "ui/request-display-mode", params: { mode: "fullscreen" } });
  assert.equal(bad.error.code, -32000);
  assert.match(bad.error.message, /does not support/);
});

test("ui/message, ui/open-link and size-changed reach the host callbacks", async () => {
  const seen = { messages: [], links: [], sizes: [] };
  const { b } = bridge({
    onMessage: (p) => seen.messages.push(p.content.text),
    onOpenLink: (url) => seen.links.push(url),
    onSizeChanged: (p) => seen.sizes.push(p),
  });
  await b.handle({ jsonrpc: "2.0", id: 1, method: "ui/message", params: { role: "user", content: { type: "text", text: "why?" } } });
  await b.handle({ jsonrpc: "2.0", id: 2, method: "ui/open-link", params: { url: "https://example.com" } });
  await b.handle({ jsonrpc: "2.0", method: "ui/notifications/size-changed", params: { width: 10, height: 20 } });
  assert.deepEqual(seen, { messages: ["why?"], links: ["https://example.com"], sizes: [{ width: 10, height: 20 }] });
});

test("teardown is a host request the view answers", async () => {
  const { b, sent } = bridge();
  await b.handle({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} });
  const done = b.teardown("test");
  const request = sent.at(-1);
  assert.equal(request.method, "ui/resource-teardown");
  await b.handle({ jsonrpc: "2.0", id: request.id, result: {} });
  await done;
  assert.equal(b.initialized, false);
});

// --- the browser MCP client ------------------------------------------------

test("parseBody reads a JSON body and an SSE body", () => {
  assert.deepEqual(parseBody("application/json", '{"jsonrpc":"2.0","id":1,"result":{}}'), [{ jsonrpc: "2.0", id: 1, result: {} }]);
  const sse = 'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"a":1}}\n\n';
  assert.deepEqual(parseBody("text/event-stream", sse), [{ jsonrpc: "2.0", id: 2, result: { a: 1 } }]);
  assert.deepEqual(parseBody("application/json", ""), []);
});

test("uiResourceUri reads the spec field and the deprecated flat one", () => {
  assert.equal(uiResourceUri({ _meta: { ui: { resourceUri: "ui://a" } } }), "ui://a");
  assert.equal(uiResourceUri({ _meta: { "ui/resourceUri": "ui://b" } }), "ui://b");
  assert.equal(uiResourceUri({}), undefined);
});

test("toolsForModel hides app-only tools and emits function schemas", () => {
  const tools = [
    { name: "a", description: "A", inputSchema: { type: "object" } },
    { name: "b", inputSchema: { type: "object" }, _meta: { ui: { visibility: ["app"] } } },
  ];
  const schemas = toolsForModel(tools);
  assert.deepEqual(schemas, [{ type: "function", function: { name: "a", description: "A", parameters: { type: "object" } } }]);
});

test("the client does the handshake with the ui extension and keeps the session id", async () => {
  const posts = [];
  const fakeFetch = async (url, init) => {
    const body = JSON.parse(init.body);
    posts.push({ headers: init.headers, body });
    const headers = new Map([["mcp-session-id", "s1"], ["content-type", "application/json"]]);
    if (!body.id) return { status: 202, ok: true, headers, text: async () => "" };
    const result = body.method === "initialize" ? { serverInfo: { name: "fake" } } : body.method === "tools/list" ? { tools: [{ name: "t" }] } : { content: [] };
    return { status: 200, ok: true, headers, text: async () => JSON.stringify({ jsonrpc: "2.0", id: body.id, result }) };
  };
  const client = new McpHttpClient("http://x/mcp", { fetch: fakeFetch });
  const init = await client.connect();
  assert.equal(init.serverInfo.name, "fake");
  assert.deepEqual(posts[0].body.params.capabilities.extensions, { [UI_EXTENSION]: { mimeTypes: [APP_MIME_TYPE] } });
  assert.equal(posts[1].body.method, "notifications/initialized");
  assert.equal(posts[1].headers["mcp-session-id"], "s1");
  assert.deepEqual(await client.listTools(), [{ name: "t" }]);
  await client.callTool("t", { x: 1 });
  assert.deepEqual(posts.at(-1).body.params, { name: "t", arguments: { x: 1 } });
});
