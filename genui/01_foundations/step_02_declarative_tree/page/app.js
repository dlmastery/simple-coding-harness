// Step 02 - three modes on one page: static (step 01), tree, flat.
// In tree and flat mode the JSON is parsed after every delta with the
// tolerant parser and the whole layout is re-rendered from what has arrived.
import { render, renderSpec } from "./render.mjs";
import { parsePartial } from "./partial-json.mjs";

const dashboard = document.querySelector("#dashboard");
const wire = document.querySelector("#wire");
const status = document.querySelector("#status");
const events = []; // every message, in order; demo.py reads it as window.__events
const timeline = []; // [ms since the run started] per delta; demo.py reads it as window.__timeline
window.__events = events;
window.__timeline = timeline;
window.__replay = (text, mode) => {
  // demo.py replays a recorded prefix of the JSON to photograph a moment of the stream
  dashboard.className = mode;
  dashboard.innerHTML = renderSpec(parsePartial(text), mode);
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

export async function run(prompt, mode) {
  dashboard.innerHTML = "";
  dashboard.className = mode;
  wire.textContent = "";
  status.textContent = "";
  events.length = 0;
  timeline.length = 0;
  document.body.dataset.state = "running";
  const started = performance.now();
  let text = "";
  const response = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, mode }),
  });
  for await (const message of readSSE(response)) {
    events.push(message);
    if (message.component) {
      wire.textContent += JSON.stringify(message) + "\n";
      dashboard.insertAdjacentHTML("beforeend", render(message.component, message.props));
    } else if (message.delta !== undefined) {
      text += message.delta;
      timeline.push(Math.round(performance.now() - started));
      wire.textContent = text;
      dashboard.innerHTML = renderSpec(parsePartial(text), mode);
    } else if (message.done) {
      wire.textContent += "\n" + JSON.stringify({ ...message, spec: undefined });
      if (message.spec) dashboard.innerHTML = renderSpec(message.spec, mode);
      const ms = Math.round(performance.now() - started);
      status.textContent = message.mode === "static" ? `${ms} ms` : `${ms} ms · ${message.valid ? "valid" : "invalid: " + message.errors.join("; ")}`;
    } else if (message.note !== undefined) {
      wire.textContent += JSON.stringify(message) + "\n";
    }
  }
  document.body.dataset.state = "done";
}

document.querySelector("#form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(document.querySelector("#prompt").value, document.querySelector("#mode").value);
});
