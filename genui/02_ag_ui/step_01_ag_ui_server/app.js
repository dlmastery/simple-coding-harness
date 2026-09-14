// The page is an AG-UI client written by hand: it posts a RunAgentInput,
// reads the event stream, and renders TEXT_MESSAGE_* events into a chat.
// Everything the protocol needs from a client is in this one file.

import { readEvents } from "/sse.mjs";

const chat = document.getElementById("chat");
const wire = document.getElementById("wire");
const status = document.getElementById("status");
const form = document.getElementById("ask");
const promptBox = document.getElementById("prompt");

const threadId = crypto.randomUUID();
const messages = []; // the AG-UI message list, kept across runs

function addMessage(role, content, id) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.dataset.id = id;
  div.textContent = content;
  chat.appendChild(div);
  return div;
}

async function runAgent(text) {
  messages.push({ id: crypto.randomUUID(), role: "user", content: text });
  addMessage("user", text);
  wire.textContent = "";
  status.textContent = "running";

  const input = {
    threadId,
    runId: crypto.randomUUID(),
    messages,
    tools: [],
    context: [],
    forwardedProps: {},
    state: {},
  };
  const response = await fetch("/agent", {
    method: "POST",
    headers: { "content-type": "application/json", accept: "text/event-stream" },
    body: JSON.stringify(input),
  });

  let current = null; // the assistant message being streamed
  for await (const event of readEvents(response)) {
    wire.textContent += JSON.stringify(event) + "\n";
    switch (event.type) {
      case "TEXT_MESSAGE_START":
        current = { id: event.messageId, role: event.role, content: "" };
        current.element = addMessage(event.role, "", event.messageId);
        break;
      case "TEXT_MESSAGE_CONTENT":
        current.content += event.delta;
        current.element.textContent = current.content;
        break;
      case "TEXT_MESSAGE_END":
        messages.push({ id: current.id, role: current.role, content: current.content });
        current = null;
        break;
      case "RUN_FINISHED":
        status.textContent = "finished";
        break;
      case "RUN_ERROR":
        status.textContent = `error: ${event.message}`;
        break;
    }
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  runAgent(promptBox.value.trim());
});
