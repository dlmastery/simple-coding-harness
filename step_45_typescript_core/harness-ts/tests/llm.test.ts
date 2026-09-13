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

test("entry drops nulls and pins the tool call shape, like model_dump(exclude_none=True)", () => {
  assert.deepEqual(entry(say("text")), { role: "assistant", content: "text" });
  const reply = use(call("c1", "bash", { command: "ls" }));
  assert.deepEqual(entry(reply), {
    role: "assistant",
    tool_calls: [{ id: "c1", type: "function", function: { name: "bash", arguments: '{"command":"ls"}' } }],
  });
  assert.deepEqual(entry({ content: "x", tool_calls: [] }), { role: "assistant", content: "x" });
});
