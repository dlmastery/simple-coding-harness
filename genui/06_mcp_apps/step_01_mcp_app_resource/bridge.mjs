// Step 01 - the host side of the MCP Apps bridge.
//
// The view runs in a sandboxed iframe and speaks JSON-RPC over postMessage.
// The host answers ui/initialize with its context and capabilities, waits
// for ui/notifications/initialized, then delivers the tool input and the
// tool result as notifications. From then on the view may call tools and
// read resources through the host, send a message to the chat, or ask for
// a link to be opened. The host proxies to the MCP server, or refuses.
//
// The class below has no DOM in it: `send` is injected, so the tests drive
// it with plain objects. `attach` wires it to a real iframe.

export const APP_MIME_TYPE = "text/html;profile=mcp-app";
export const PROTOCOL_VERSION = "2025-06-18";

/** The spec's restrictive default: nothing leaves the frame unless the resource declared a domain. */
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

/** A declared domain is an origin, nothing else: no `;` or space that would smuggle a directive into the policy. */
export function isDomain(value) {
  if (typeof value !== "string" || /[;\s'"]/.test(value)) return false;
  try { return Boolean(new URL(value.includes("://") ? value : `https://${value}`).hostname); } catch { return false; }
}

/** The CSP string for a resource: the restrictive default plus what `_meta.ui.csp` declares. Malformed entries are dropped. */
export function cspFor(uiMeta = {}) {
  const csp = uiMeta.csp ?? {};
  const directives = Object.fromEntries(Object.entries(RESTRICTIVE_CSP).map(([k, v]) => [k, [...v]]));
  const allow = (name, domains) => {
    const clean = (Array.isArray(domains) ? domains : []).filter(isDomain);
    if (!clean.length) return;
    directives[name] = directives[name].filter((v) => v !== "'none'").concat(clean);
  };
  allow("connect-src", csp.connectDomains);
  for (const name of ["script-src", "style-src", "img-src", "font-src", "media-src"]) allow(name, csp.resourceDomains);
  allow("frame-src", csp.frameDomains);
  allow("base-uri", csp.baseUriDomains);
  return Object.entries(directives).map(([name, values]) => `${name} ${values.join(" ")}`).join("; ");
}

/** The view's HTML with the CSP right after the doctype, before any element: a script written before
 *  <head>, or a <head> inside a comment, would otherwise run ahead of the policy. A <meta> before <html>
 *  is legal HTML; the parser opens <html> and <head> for it. */
export function withCsp(html, csp) {
  const meta = `<meta http-equiv="Content-Security-Policy" content="${csp.replaceAll('"', "&quot;")}">`;
  const doctype = /^\s*<!doctype[^>]*>/i.exec(html);
  const at = doctype ? doctype[0].length : 0;
  return html.slice(0, at) + meta + html.slice(at);
}

/** `_meta.ui` for a resource: the content item wins, the listing entry is the fallback. */
export function uiMetaOf(content, listing) {
  return content?._meta?.ui ?? listing?._meta?.ui ?? {};
}

export class HostBridge {
  constructor({ send, tool, tools, callTool, readResource, onMessage, onOpenLink, onModelContext, onSizeChanged, onLog, hostContext = {} }) {
    this.send = send;                      // (message) => void, towards the view
    this.tool = tool;                      // the tool definition the view was opened for
    this.tools = tools ?? (tool ? [tool] : []);  // every tool the view may call: the server's list, checked on each call
    this.callTool = callTool;              // (name, args) => Promise<CallToolResult>
    this.readResource = readResource;      // (uri) => Promise<ReadResourceResult>
    this.onMessage = onMessage;            // ui/message: the view speaks into the chat
    this.onOpenLink = onOpenLink;          // ui/open-link
    this.onModelContext = onModelContext;  // ui/update-model-context: context for the next turn
    this.onSizeChanged = onSizeChanged;    // ui/notifications/size-changed
    this.onLog = onLog;                    // (direction, message), every message that crosses
    this.hostContext = hostContext;
    this.initialized = false;
    this.queue = [];                       // notifications held until the view says initialized
    this.pending = new Map();              // id -> resolve, for the host's own requests to the view
    this.nextId = 1;
  }

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

  initializeResult() {
    return {
      protocolVersion: PROTOCOL_VERSION,
      hostInfo: { name: "genui-minimal-host", version: "0.1.0" },
      hostCapabilities: this.hostCapabilities(),
      hostContext: {
        theme: "light",
        displayMode: "inline",
        availableDisplayModes: ["inline"],
        platform: "web",
        locale: "en-US",
        toolInfo: { tool: this.tool },
        ...this.hostContext,
      },
    };
  }

  /** One message from the view. Returns the response to send back, or undefined for a notification.
   *  The shape is checked first: a JSON-RPC id is a string or a number, a method is a string, params an
   *  object. Anything else is dropped without an answer. */
  async handle(message) {
    if (!message || typeof message !== "object" || message.jsonrpc !== "2.0") return;
    const { id, method } = message;
    const params = message.params !== null && typeof message.params === "object" ? message.params : {};
    if (id !== undefined && typeof id !== "string" && typeof id !== "number") return;
    if (method !== undefined && typeof method !== "string") return;
    this.onLog?.("view->host", message);
    if (method === undefined) {  // a response to a host request, such as ui/resource-teardown
      this.pending.get(id)?.(message.result ?? message.error);
      this.pending.delete(id);
      return;
    }
    if (id === undefined) {
      this.notification(method, params);
      return;
    }
    try {
      return { jsonrpc: "2.0", id, result: await this.dispatch(method, params) };
    } catch (error) {
      return { jsonrpc: "2.0", id, error: { code: -32000, message: error.message } };
    }
  }

  /** The tool a view may call: one the server listed, whose `_meta.ui.visibility` includes "app". Throws otherwise. */
  allowedTool(name) {
    const tool = this.tools.find((t) => t.name === name);
    if (!tool) throw new Error(`the view may not call ${name}: not a tool of this server`);
    if (!(tool._meta?.ui?.visibility ?? ["model", "app"]).includes("app")) throw new Error(`the view may not call ${name}: visibility is model-only`);
    return tool;
  }

  notification(method, params) {
    if (method === "ui/notifications/initialized") {
      this.initialized = true;
      for (const queued of this.queue.splice(0)) this.post(queued);
    } else if (method === "ui/notifications/size-changed") {
      this.onSizeChanged?.(params);
    }
  }

  async dispatch(method, params) {
    switch (method) {
      case "ui/initialize":
        return this.initializeResult();
      case "tools/call":
        this.allowedTool(params.name);  // the allowlist runs before the call, so a refusal and a failure look the same to the view: an error reply
        return this.callTool(params.name, params.arguments !== null && typeof params.arguments === "object" ? params.arguments : {});
      case "resources/read":
        if (typeof params.uri !== "string" || !params.uri.startsWith("ui://")) throw new Error("the view may read ui:// resources only");
        return this.readResource(params.uri);
      case "ui/message":
        await this.onMessage?.(params);
        return {};
      case "ui/open-link":
        await this.onOpenLink?.(params.url);
        return {};
      case "ui/update-model-context":
        await this.onModelContext?.(params);
        return {};
      case "ping":
        return {};
      default:
        throw new Error(`the host does not support ${method}`);
    }
  }

  post(message) {
    this.onLog?.("host->view", message);
    this.send(message);
  }

  /** A request from the host to the view. Resolves with the view's answer, or after `timeout` ms. */
  request(method, params, timeout = 1000) {
    const id = this.nextId++;
    return new Promise((resolve) => {
      this.pending.set(id, resolve);
      setTimeout(() => { this.pending.delete(id); resolve(undefined); }, timeout);
      this.post({ jsonrpc: "2.0", id, method, params });
    });
  }

  /** The graceful end: the host asks, the view answers, then the host may remove the frame. */
  async teardown(reason) {
    if (this.initialized) await this.request("ui/resource-teardown", { reason });
    this.initialized = false;
    if (this.detach) this.detach();  // the window listener goes with the frame
  }

  /** A notification to the view; held back until the view has said initialized. */
  notify(method, params) {
    const message = { jsonrpc: "2.0", method, params };
    if (this.initialized) this.post(message);
    else this.queue.push(message);
  }

  /** The data delivery: the arguments first, then the result, or the reason it did not come. */
  async deliver(args, resultPromise) {
    this.notify("ui/notifications/tool-input", { arguments: args });
    try {
      this.notify("ui/notifications/tool-result", await resultPromise);
    } catch (error) {
      this.notify("ui/notifications/tool-cancelled", { reason: error.message });
    }
  }

  /** Wire the bridge to an iframe: only messages from that frame are read, and the listener is removed at teardown. */
  attach(iframe) {
    this.send = (message) => iframe.contentWindow?.postMessage(message, "*");
    const onMessage = (event) => {
      if (event.source !== iframe.contentWindow) return;
      this.handle(event.data).then((reply) => reply && this.post(reply));
    };
    window.addEventListener("message", onMessage);
    this.detach = () => window.removeEventListener("message", onMessage);
    return this;
  }
}
