// Step 03 - four modes on one page: static (step 01), tree and flat (step 02), html.
// In html mode the model's document is shown as it streams and, once complete,
// mounted in a sandboxed iframe. The iframe talks back only through postMessage.
import { render, renderSpec } from "./render.mjs";
import { parsePartial } from "./partial-json.mjs";
import { mount, isEvent } from "./sandbox.mjs";

const dashboard = document.querySelector("#dashboard");
const frame = document.querySelector("#frame");
const wire = document.querySelector("#wire");
const inboxPanel = document.querySelector("#inbox");
const status = document.querySelector("#status");
const events = []; // every message, in order; demo.py reads it as window.__events
const timeline = []; // [ms since the run started] per delta; demo.py reads it as window.__timeline
const inbox = []; // events the iframe posted; demo.py reads it as window.__inbox
window.__events = events;
window.__timeline = timeline;
window.__inbox = inbox;

window.addEventListener("message", (event) => {
  // Only the mounted iframe, and only the one shape the host accepts.
  if (event.source !== frame.contentWindow || !isEvent(event.data)) return;
  inbox.push(event.data);
  inboxPanel.textContent += JSON.stringify(event.data) + "\n";
});
window.__replay = (text, mode) => {
  // demo.py replays a recorded prefix of the JSON to photograph a moment of the stream
  dashboard.className = mode;
  dashboard.innerHTML = renderSpec(partialSpec(text, null), mode);
  wire.textContent = text;
};

async function* readSSE(response) {
  // Frames are separated by a blank line; each frame has one "data: " line.
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      for (const line of frame.split("\n")) {
        if (line.startsWith("data:")) yield JSON.parse(line.slice(5));
      }
    }
  }
}

export function partialSpec(text, last) {
  // The layout so far. Text that is not JSON (a fence, a sentence before the
  // document) keeps the last good layout instead of taking the page down.
  try {
    return parsePartial(text);
  } catch {
    return last;
  }
}

export async function run(prompt, mode) {
  dashboard.innerHTML = "";
  dashboard.className = mode;
  frame.hidden = mode !== "html";
  frame.srcdoc = "";
  wire.textContent = "";
  inboxPanel.textContent = "";
  status.textContent = "";
  events.length = 0;
  timeline.length = 0;
  inbox.length = 0;
  document.body.dataset.state = "running";
  const started = performance.now();
  let text = "";
  let spec = null;
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, mode }),
    });
    if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
    for await (const message of readSSE(response)) {
      events.push(message);
      if (message.component) {
        wire.textContent += JSON.stringify(message) + "\n";
        dashboard.insertAdjacentHTML("beforeend", render(message.component, message.props));
      } else if (message.delta !== undefined) {
        text += message.delta;
        timeline.push(Math.round(performance.now() - started));
        wire.textContent = text;
        if (mode !== "html") {
          spec = partialSpec(text, spec);
          dashboard.innerHTML = renderSpec(spec, mode);
        }
      } else if (message.done) {
        wire.textContent += "\n" + JSON.stringify({ ...message, spec: undefined, html: undefined, raw: undefined });
        if (message.spec) dashboard.innerHTML = renderSpec(message.spec, mode);
        if (message.html !== undefined) mount(frame, message.html);
        const ms = Math.round(performance.now() - started);
        const verdict = message.valid === undefined ? "" : ` · ${message.valid ? "valid" : "invalid: " + message.errors.join("; ")}`;
        status.textContent = message.error ? `${ms} ms · error: ${message.error}` : `${ms} ms${verdict}`;
      } else if (message.note !== undefined) {
        wire.textContent += JSON.stringify(message) + "\n";
      }
    }
  } catch (error) {
    // a dead server or a cut stream: say so instead of staying "running" forever
    events.push({ done: true, error: String(error.message ?? error) });
    status.textContent = `error: ${error.message ?? error}`;
  } finally {
    document.body.dataset.state = "done";
  }
}

document.querySelector("#form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(document.querySelector("#prompt").value, document.querySelector("#mode").value);
});
