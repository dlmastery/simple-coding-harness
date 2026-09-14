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

function fakeServer(received) {
  const server = http.createServer((req, res) => {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      received.push(JSON.parse(body));
      res.writeHead(200, { "content-type": "text/event-stream" });
      for (const event of SCRIPT) res.write(`data: ${JSON.stringify(event)}\n\n`);
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
