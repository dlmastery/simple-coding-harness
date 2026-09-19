// Step 01 - read the SSE stream, append one rendered component per message.
import { render } from "./render.mjs";

const dashboard = document.querySelector("#dashboard");
const wire = document.querySelector("#wire");
const events = []; // every message, in order; demo.py reads it as window.__events
window.__events = events;

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

export async function run(prompt) {
  dashboard.innerHTML = "";
  wire.textContent = "";
  events.length = 0;
  document.body.dataset.state = "running";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
    for await (const message of readSSE(response)) {
      events.push(message);
      wire.textContent += JSON.stringify(message) + "\n";
      if (message.component) dashboard.insertAdjacentHTML("beforeend", render(message.component, message.props));
    }
  } catch (error) {
    // a dead server or a cut stream: say so instead of staying "running" forever
    events.push({ done: true, error: String(error.message ?? error) });
    wire.textContent += `error: ${error.message ?? error}\n`;
  } finally {
    document.body.dataset.state = "done";
  }
}

document.querySelector("#form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(document.querySelector("#prompt").value);
});
