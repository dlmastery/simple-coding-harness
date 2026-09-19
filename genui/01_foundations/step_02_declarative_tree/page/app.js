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
  wire.textContent = "";
  status.textContent = "";
  events.length = 0;
  timeline.length = 0;
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
        spec = partialSpec(text, spec);
        dashboard.innerHTML = renderSpec(spec, mode);
      } else if (message.done) {
        wire.textContent += "\n" + JSON.stringify({ ...message, spec: undefined });
        if (message.spec) dashboard.innerHTML = renderSpec(message.spec, mode);
        const ms = Math.round(performance.now() - started);
        if (message.error) status.textContent = `${ms} ms · error: ${message.error}`;
        else status.textContent = message.mode === "static" ? `${ms} ms` : `${ms} ms · ${message.valid ? "valid" : "invalid: " + message.errors.join("; ")}`;
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
