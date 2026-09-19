// The page is still a hand-written AG-UI client. New in this step: it
// keeps a `state` object, applies STATE_SNAPSHOT and STATE_DELTA to it and
// renders the dashboard from it; it shows tool calls as they stream; and it
// offers one client tool, confirm_purchase, that it executes itself.

import { applyPatch } from "/json-patch.mjs";
import { renderDashboard } from "/render.mjs";
import { readEvents } from "/sse.mjs";

const chat = document.getElementById("chat");
const dashboard = document.getElementById("dashboard");
const wire = document.getElementById("wire");
const status = document.getElementById("status");
const form = document.getElementById("ask");
const promptBox = document.getElementById("prompt");

// A tool the page runs. The server only sees its schema and streams the call.
const CLIENT_TOOLS = [
  {
    name: "confirm_purchase",
    description: "Ask the user to confirm a purchase before recording it. Returns 'confirmed' or 'declined'.",
    parameters: {
      type: "object",
      properties: { item: { type: "string" }, cost: { type: "number" } },
      required: ["item", "cost"],
    },
  },
];

const threadId = crypto.randomUUID();
const messages = []; // the AG-UI message list, kept across runs
let state = {};      // the shared state, kept across runs
let running = false; // one run at a time: a second submit would interleave two streams
const pendingConfirms = []; // confirm panels waiting for a click; a new prompt declines them

function addMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = content;
  chat.appendChild(div);
  return div;
}

function showState() {
  dashboard.replaceChildren(renderDashboard(state.dashboard || {}));
}

function parseArgs(call) {
  // The arguments the model wrote, or nothing: a call that is not JSON still gets its panel.
  try {
    return JSON.parse(call.function.arguments || "{}");
  } catch {
    return {};
  }
}

function askToConfirm(call) {
  // The client tool: a panel with two buttons. The answer becomes a tool
  // message, and the next run starts from it with no new user message.
  const args = parseArgs(call);
  const panel = addMessage("confirm", "");
  const label = document.createElement("span");
  label.textContent = `Confirm purchase: ${args.item} for $${args.cost}?`;
  panel.appendChild(label);
  const answerWith = (answer) => {
    panel.replaceChildren(document.createTextNode(`${label.textContent} ${answer}`));
    messages.push({ id: crypto.randomUUID(), role: "tool", toolCallId: call.id, content: answer });
    pendingConfirms.splice(pendingConfirms.indexOf(pending), 1);
  };
  const pending = { call, decline: () => answerWith("declined") };
  pendingConfirms.push(pending);
  for (const [text, answer] of [["Confirm", "confirmed"], ["Decline", "declined"]]) {
    const button = document.createElement("button");
    button.textContent = text;
    button.dataset.answer = answer;
    if (answer === "declined") button.className = "secondary";
    button.onclick = () => {
      answerWith(answer);
      runAgent();
    };
    panel.appendChild(button);
  }
}

async function runAgent(text) {
  if (running) return; // the submit is dropped, not queued: the page is one conversation
  // A prompt typed while a confirm panel waits answers it "declined" first:
  // the history must not carry a tool call without its result.
  while (pendingConfirms.length) pendingConfirms[0].decline();
  if (text) {
    messages.push({ id: crypto.randomUUID(), role: "user", content: text });
    addMessage("user", text);
  }
  running = true;
  wire.textContent = "";
  status.textContent = "running";
  const mark = messages.length; // everything pushed from here belongs to this run

  const input = {
    threadId,
    runId: crypto.randomUUID(),
    messages,
    tools: CLIENT_TOOLS,
    context: [],
    forwardedProps: {},
    state,
  };
  let assistant = null;   // the assistant message being built (text and tool calls)
  let textElement = null;
  const toolElements = {}; // tool call id -> its line in the chat
  const pendingClientCalls = [];

  function currentAssistant() {
    if (!assistant) {
      assistant = { id: crypto.randomUUID(), role: "assistant", content: "", toolCalls: [] };
      messages.push(assistant); // pushed now, so tool results land after it
    }
    return assistant;
  }

  function findCall(id) {
    return assistant?.toolCalls.find((c) => c.id === id);
  }

  try {
    const response = await fetch("/agent", {
      method: "POST",
      headers: { "content-type": "application/json", accept: "text/event-stream" },
      body: JSON.stringify(input),
    });
    if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);

    for await (const event of readEvents(response)) {
      wire.textContent += JSON.stringify(event) + "\n";
      switch (event.type) {
        case "STATE_SNAPSHOT":
          state = event.snapshot;
          showState();
          break;
        case "STATE_DELTA":
          applyPatch(state, event.delta);
          showState();
          break;
        case "TEXT_MESSAGE_START":
          currentAssistant().id = event.messageId;
          textElement = addMessage("assistant", "");
          break;
        case "TEXT_MESSAGE_CONTENT":
          if (!assistant || !textElement) break; // a delta for a message that never started
          assistant.content += event.delta;
          textElement.textContent = assistant.content;
          break;
        case "TOOL_CALL_START": {
          const call = { id: event.toolCallId, type: "function", function: { name: event.toolCallName, arguments: "" } };
          currentAssistant().toolCalls.push(call);
          toolElements[call.id] = addMessage("tool", `${call.function.name}(`);
          break;
        }
        case "TOOL_CALL_ARGS": {
          const call = findCall(event.toolCallId);
          if (!call) break;
          call.function.arguments += event.delta;
          toolElements[call.id].textContent = `${call.function.name}(${call.function.arguments}`;
          break;
        }
        case "TOOL_CALL_END": {
          const call = findCall(event.toolCallId);
          if (!call) break;
          toolElements[call.id].textContent += ")";
          if (CLIENT_TOOLS.some((t) => t.name === call.function.name)) pendingClientCalls.push(call);
          break;
        }
        case "TOOL_CALL_RESULT":
          messages.push({ id: event.messageId, role: "tool", toolCallId: event.toolCallId, content: event.content });
          if (toolElements[event.toolCallId]) toolElements[event.toolCallId].textContent += ` -> ${event.content}`;
          assistant = null; // the next model reply is a new assistant message
          break;
        case "RUN_FINISHED":
          status.textContent = "finished";
          break;
        case "RUN_ERROR":
          throw new Error(event.message);
      }
    }
    if (status.textContent === "running") throw new Error("the stream ended without RUN_FINISHED");
    for (const call of pendingClientCalls) askToConfirm(call);
  } catch (error) {
    // A RUN_ERROR, a 4xx/5xx, a dead server, a cut stream: the run is rolled
    // back. Its half-built assistant message would carry tool calls with no
    // results, and the API refuses such a history on every later run.
    messages.length = mark;
    status.textContent = `error: ${error.message ?? error}`;
  } finally {
    running = false;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  runAgent(promptBox.value.trim());
});
