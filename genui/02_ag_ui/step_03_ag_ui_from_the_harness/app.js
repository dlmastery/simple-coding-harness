// The page no longer parses SSE or keeps messages and state by hand.
// @ag-ui/client's HttpAgent does all of that: it posts the RunAgentInput,
// reads the stream, verifies the event order, applies STATE_* events to
// agent.state and rebuilds agent.messages from TEXT_* and TOOL_* events.
// The page only subscribes to what it wants to draw.

import { HttpAgent } from "/vendor/ag-ui-client.js";

const chat = document.getElementById("chat");
const todos = document.getElementById("todos");
const usage = document.getElementById("usage");
const wire = document.getElementById("wire");
const status = document.getElementById("status");
const form = document.getElementById("ask");
const promptBox = document.getElementById("prompt");

const agent = new HttpAgent({ url: "/agent" });

function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = content;
  chat.appendChild(div);
  return div;
}

function showTodos(state) {
  todos.replaceChildren();
  for (const todo of state.todos || []) {
    const li = document.createElement("li");
    li.className = todo.status;
    li.textContent = `${{ pending: "[ ]", in_progress: "[~]", completed: "[x]" }[todo.status]} ${todo.content}`;
    todos.appendChild(li);
  }
}

let textElement = null;
const toolElements = {};
let running = false; // one run at a time: HttpAgent would happily start a second

agent.subscribe({
  onEvent({ event }) {
    wire.textContent += JSON.stringify(event) + "\n";
  },
  onTextMessageStartEvent() {
    textElement = addMessage("assistant", "");
  },
  onTextMessageContentEvent({ textMessageBuffer }) {
    if (textElement) textElement.textContent = textMessageBuffer; // the client keeps the buffer
  },
  onToolCallStartEvent({ event }) {
    toolElements[event.toolCallId] = addMessage("tool", `${event.toolCallName}(`);
  },
  onToolCallArgsEvent({ event, toolCallName, toolCallBuffer }) {
    // toolCallBuffer holds the arguments so far, before this delta is added
    toolElements[event.toolCallId].textContent = `${toolCallName}(${toolCallBuffer}${event.delta}`;
  },
  onToolCallEndEvent({ event, toolCallName, toolCallArgs }) {
    toolElements[event.toolCallId].textContent = `${toolCallName}(${JSON.stringify(toolCallArgs)})`;
  },
  onToolCallResultEvent({ event }) {
    const result = document.createElement("span");
    result.className = "result";
    result.textContent = event.content;
    toolElements[event.toolCallId]?.appendChild(result);
  },
  onCustomEvent({ event }) {
    if (event.name === "permission") addMessage("permission", `permission: ${event.value.reason} -> ${event.value.decision}`);
  },
  onStateChanged({ state }) {
    showTodos(state);
  },
  onRunFinishedEvent({ event }) {
    const [u] = event.usage || [];
    if (u) usage.textContent = `${u.model}: ${u.inputTokens} in, ${u.outputTokens} out`;
    status.textContent = "finished";
  },
  onRunErrorEvent({ event }) {
    status.textContent = `error: ${event.message}`;
  },
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = promptBox.value.trim();
  if (!text || running) return;
  running = true;
  addMessage("user", text);
  agent.addMessage({ id: crypto.randomUUID(), role: "user", content: text });
  const mark = agent.messages.length; // the history a failed run is rolled back to
  wire.textContent = "";
  status.textContent = "running";
  try {
    // A 4xx/5xx, a dead server or an illegal event order reject here. A
    // RUN_ERROR does not: the client resolves and keeps the half-built
    // assistant message, whose tool calls have no results, so the page cuts
    // the run's messages itself; the API refuses such a history otherwise.
    await agent.runAgent();
  } catch (error) {
    status.textContent = `error: ${error.message}`;
  } finally {
    if (status.textContent !== "finished") agent.messages = agent.messages.slice(0, mark);
    running = false;
  }
});
