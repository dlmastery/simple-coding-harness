import assert from "node:assert/strict";
import { test } from "node:test";

import { callLlm, entry, setClient } from "../llm.ts";
import { TOOL_SCHEMAS } from "../tools.ts";
import { call, fakeClient, say, use, type Request } from "./fake.ts";

test("callLlm sends the registry by default, nothing for [], and reads usage from the reply", async () => {
  const requests: Request[] = [];
  setClient(fakeClient([say("hi"), say("summary"), say("again")], requests));

  const { message, usage } = await callLlm([{ role: "user", content: "q" }]);
  assert.equal(message.content, "hi");
  assert.deepEqual(usage, { prompt_tokens: 10, completion_tokens: 4, reasoning_tokens: null, cached_tokens: 3 });
  assert.equal(requests[0].tools, TOOL_SCHEMAS);

  await callLlm([{ role: "user", content: "q" }], []);
  assert.ok(!("tools" in requests[1]));

  const subset = TOOL_SCHEMAS.slice(0, 1);
  await callLlm([{ role: "user", content: "q" }], subset);
  assert.equal(requests[2].tools, subset);
  setClient(null);
});

test("entry pins the reply to role, content and tool_calls, like StreamedMessage.model_dump", () => {
  assert.deepEqual(entry(say("text")), { role: "assistant", content: "text" }); // say() carries refusal: null - gone
  const reply = use(call("c1", "bash", { command: "ls" }));
  assert.deepEqual(entry(reply), {
    role: "assistant",
    content: null, // content stays, null included: the shape the API sends
    tool_calls: [{ id: "c1", type: "function", function: { name: "bash", arguments: '{"command":"ls"}' } }],
  });
  assert.deepEqual(entry({ content: "x", tool_calls: [] }), { role: "assistant", content: "x" });
  // what a reasoning model or the OpenAI server sends along is never echoed back on the next request
  assert.deepEqual(entry({ content: "x", tool_calls: null, reasoning: "hmm", annotations: [], refusal: null }), { role: "assistant", content: "x" });
});

test("a reply with no choices is an error the loop can report, not a TypeError", async () => {
  setClient({ chat: { completions: { async create() { return { choices: [], error: { message: "overloaded" } } as any; } } } });
  await assert.rejects(callLlm([{ role: "user", content: "q" }]), /overloaded/);
  setClient(null);
});
