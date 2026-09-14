// Step 04 - the loop closes. A Button click, or an event posted by a
// GeneratedView, goes to /api/action with the session id; the server runs
// the next model turn and the page renders the new layout the same way.
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
const inbox = []; // events the page acted on; demo.py reads it as window.__inbox
window.__events = events;
window.__timeline = timeline;
window.__inbox = inbox;
window.__replay = (text, mode) => {
  // demo.py replays a recorded prefix of the JSON to photograph a moment of the stream
  dashboard.className = mode;
  dashboard.innerHTML = renderSpec(parsePartial(text), mode);
  wire.textContent = text;
};

let session = null; // set by the first declarative run; every action carries it
let currentMode = "flat";

async function* readSSE(response) {
  // Frames are separated by a blank line; each frame has one "data: " line.
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      for (const line of frame.split("\n")) {
        if (line.startsWith("data: ")) yield JSON.parse(line.slice(6));
      }
    }
  }
}

async function consume(response, mode) {
  // One SSE stream, whichever endpoint produced it: render as it arrives, keep the session.
  document.body.dataset.state = "running";
  const started = performance.now();
  let text = "";
  for await (const message of readSSE(response)) {
    events.push(message);
    if (message.component) {
      wire.textContent += JSON.stringify(message) + "\n";
      dashboard.insertAdjacentHTML("beforeend", render(message.component, message.props));
    } else if (message.delta !== undefined) {
      text += message.delta;
      timeline.push(Math.round(performance.now() - started));
      wire.textContent = text;
      if (mode !== "html") dashboard.innerHTML = renderSpec(parsePartial(text), mode);
    } else if (message.done) {
      wire.textContent += "\n" + JSON.stringify({ ...message, spec: undefined, html: undefined, raw: undefined });
      if (message.spec) dashboard.innerHTML = renderSpec(message.spec, mode);
      if (message.html !== undefined) mount(frame, message.html);
      if (message.session) session = message.session;
      const ms = Math.round(performance.now() - started);
      const verdict = message.valid === undefined ? "" : ` · ${message.valid ? "valid" : "invalid: " + message.errors.join("; ")}`;
      const turn = message.turn ? ` · turn ${message.turn}` : "";
      status.textContent = `${ms} ms${verdict}${turn}`;
    } else if (message.note !== undefined) {
      wire.textContent += JSON.stringify(message) + "\n";
    }
  }
  document.body.dataset.state = "done";
}

export async function run(prompt, mode) {
  dashboard.innerHTML = "";
  dashboard.className = mode;
  currentMode = mode;
  session = null;
  frame.hidden = mode !== "html";
  frame.srcdoc = "";
  wire.textContent = "";
  inboxPanel.textContent = "";
  status.textContent = "";
  events.length = 0;
  timeline.length = 0;
  inbox.length = 0;
  const response = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, mode }),
  });
  await consume(response, mode);
}

export async function act(action, payload, source) {
  // The event goes to the server as the next user turn; the reply is a whole new layout.
  const event = { source, action, payload };
  inbox.push(event);
  inboxPanel.textContent += JSON.stringify(event) + "\n";
  if (!session) return; // html mode, or nothing rendered yet: logged, not acted on
  timeline.length = 0;
  const response = await fetch("/api/action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session, action, payload }),
  });
  await consume(response, currentMode);
}

dashboard.addEventListener("click", (event) => {
  // Every Button in the catalog carries data-action; the click is the event.
  const button = event.target.closest("button.action");
  if (button) act(button.dataset.action, { label: button.textContent }, "button");
});

window.addEventListener("message", (event) => {
  // Only a window the page mounted, and only the one shape the host accepts.
  const frames = [frame, ...dashboard.querySelectorAll("iframe.generated")];
  if (!frames.some((f) => f.contentWindow === event.source) || !isEvent(event.data)) return;
  act(event.data.name, event.data.payload ?? null, "generated");
});

document.querySelector("#form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(document.querySelector("#prompt").value, document.querySelector("#mode").value);
});
