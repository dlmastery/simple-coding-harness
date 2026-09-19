// @ag-ui/client's HttpAgent against a fake server that replays the exact
// stream bridge.py produces. Offline: the "server" is a Node http server
// on a random port that writes scripted events.
import http from "node:http";
import { test } from "node:test";
import assert from "node:assert/strict";
import { HttpAgent } from "@ag-ui/client";

const SCRIPT = [
  { type: "RUN_STARTED", threadId: "t", runId: "r" },
  { type: "STATE_SNAPSHOT", snapshot: { todos: [] } },
  { type: "TOOL_CALL_START", toolCallId: "c1", toolCallName: "write_file", parentMessageId: "m1" },
  { type: "TOOL_CALL_ARGS", toolCallId: "c1", delta: '{"path":"hello.py","content":"print(1)"}' },
  { type: "TOOL_CALL_END", toolCallId: "c1" },
  { type: "TOOL_CALL_RESULT", messageId: "tm1", toolCallId: "c1", content: "Wrote hello.py", role: "tool" },
  { type: "CUSTOM", name: "permission", value: { reason: "run: python hello.py", decision: "allow" } },
  { type: "STATE_DELTA", delta: [{ op: "replace", path: "/todos", value: [{ content: "write it", status: "completed" }] }] },
  { type: "TEXT_MESSAGE_START", messageId: "m2", role: "assistant" },
  { type: "TEXT_MESSAGE_CONTENT", messageId: "m2", delta: "Done." },
  { type: "TEXT_MESSAGE_END", messageId: "m2" },
  { type: "RUN_FINISHED", threadId: "t", runId: "r", usage: [{ model: "fake", inputTokens: 10, outputTokens: 5 }] },
];

// A run the bridge cut short: the model called a tool, then failed. The
// tool call has no result, so a client that kept it would send a history
// the API refuses on every later run.
const FAILED = [
  { type: "RUN_STARTED", threadId: "t", runId: "r2" },
  { type: "TOOL_CALL_START", toolCallId: "c9", toolCallName: "bash" },
  { type: "TOOL_CALL_ARGS", toolCallId: "c9", delta: '{"command":"ls"}' },
  { type: "TOOL_CALL_END", toolCallId: "c9" },
  { type: "RUN_ERROR", message: "model down" },
];

function fakeServer(received, script = SCRIPT) {
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      received.push(JSON.parse(body));
      res.writeHead(200, { "content-type": "text/event-stream" });
      res.write(": keepalive\n\n"); // the bridge writes these while the model is silent
      // LF framing only: @ag-ui/client 0.0.59 splits events on "\n\n" and would choke on CRLF
      for (const event of script) res.write(`data: ${JSON.stringify(event)}\n\n`);
      res.end();
    });
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

test("HttpAgent reads the bridge's stream and rebuilds messages and state", async () => {
  const received = [];
  const server = await fakeServer(received);
  const agent = new HttpAgent({ url: `http://127.0.0.1:${server.address().port}/agent`, threadId: "t" });
  agent.addMessage({ id: "u1", role: "user", content: "write hello.py" });

  const seen = [];
  const tools = [];
  const result = await agent.runAgent({}, {
    onEvent: ({ event }) => seen.push(event.type),
    onToolCallEndEvent: ({ toolCallName, toolCallArgs }) => tools.push([toolCallName, toolCallArgs.path]),
  });
  server.close();

  assert.deepEqual(seen, SCRIPT.map((e) => e.type));
  assert.deepEqual(tools, [["write_file", "hello.py"]]);
  assert.deepEqual(agent.state, { todos: [{ content: "write it", status: "completed" }] });
  assert.deepEqual(agent.messages.map((m) => m.role), ["user", "assistant", "tool", "assistant"]);
  assert.equal(agent.messages[1].toolCalls[0].function.name, "write_file");
  assert.equal(result.newMessages.length, 3);
  // the request carried the whole RunAgentInput
  assert.deepEqual(Object.keys(received[0]).sort(), ["context", "forwardedProps", "messages", "runId", "state", "threadId", "tools"]);
});

test("a RUN_ERROR resolves runAgent and leaves the dangling call: the page must roll back", async () => {
  const received = [];
  const server = await fakeServer(received, FAILED);
  const agent = new HttpAgent({ url: `http://127.0.0.1:${server.address().port}/agent`, threadId: "t" });
  agent.addMessage({ id: "u1", role: "user", content: "list the files" });
  const mark = agent.messages.length;
  const errors = [];
  await agent.runAgent({}, { onRunErrorEvent: ({ event }) => errors.push(event.message) }); // resolves, in 0.0.59
  server.close();
  assert.deepEqual(errors, ["model down"]);
  assert.deepEqual(agent.messages.map((m) => m.role), ["user", "assistant"], "the client keeps the unanswered tool call");
  agent.messages = agent.messages.slice(0, mark); // what app.js does after a run that did not finish
  assert.deepEqual(agent.messages.map((m) => m.role), ["user"]);
});
