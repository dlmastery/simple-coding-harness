import assert from "node:assert/strict";
import { test } from "node:test";

import { basePrompt, compact, needed, previousSummary, render, safeBoundary, tailStart } from "../compact.ts";
import { setClient } from "../llm.ts";
import type { Message } from "../types.ts";
import { call, fakeClient, say, type Request } from "./fake.ts";

function transcript(): Message[] {
  return [
    { role: "system", content: "base prompt" },
    { role: "user", content: "first ask" },
    { role: "assistant", content: null, tool_calls: [call("t1", "bash", { command: "ls" })] },
    { role: "tool", tool_call_id: "t1", content: "a.py\n" },
    { role: "assistant", content: "done with first" },
    { role: "user", content: "second ask " + "x".repeat(400) },
    { role: "assistant", content: "done with second" },
  ];
}

test("needed compares prompt tokens with the compaction threshold", () => {
  assert.ok(!needed({ prompt_tokens: 1000, completion_tokens: 1, reasoning_tokens: null, cached_tokens: null }));
  assert.ok(needed({ prompt_tokens: 120_000, completion_tokens: 1, reasoning_tokens: null, cached_tokens: null }));
});

test("a cut never orphans a tool result", () => {
  const messages = transcript();
  assert.equal(safeBoundary(messages, 3), 4); // index 3 is a tool result; 4 is a fresh exchange
  assert.equal(safeBoundary(messages, 2), 2); // index 2 opens an exchange: the call and its result both stay in the tail
  assert.equal(safeBoundary(messages, 5), 5);
  assert.equal(tailStart(messages, 10), 6); // the last message alone overflows: cut right before it
  assert.equal(tailStart(messages, 1_000_000), 1); // everything fits: cut nowhere
});

test("compact folds the summary into the system prompt and keeps the tail", async () => {
  const requests: Request[] = [];
  setClient(fakeClient([say("## Goal\nList files.")], requests));
  const messages = transcript();
  const kept = await compact(messages, 100);

  assert.equal(kept.length, 3);
  assert.equal(kept[0].role, "system");
  assert.ok(kept[0].content!.startsWith("base prompt\n\n<summary>"));
  assert.ok(kept[0].content!.includes("## Goal\nList files.\n</summary>"));
  assert.equal(kept[1].content, messages[5].content);
  assert.equal(kept[2].content, "done with second");

  assert.ok(!("tools" in requests[0])); // the summariser has no tools
  const seen = requests[0].messages[1].content;
  assert.ok(seen.includes("USER: first ask"));
  assert.ok(seen.includes("[called bash: {\"command\":\"ls\"}]"));
  assert.ok(seen.includes("TOOL RESULT: a.py"));
  assert.ok(!seen.includes("second ask"));

  // a second compaction carries the earlier note forward and does not stack summaries
  setClient(fakeClient([say("## Goal\nStill listing.")], requests));
  kept.push({ role: "user", content: "third ask " + "y".repeat(400) }, { role: "assistant", content: "done with third" });
  const again = await compact(kept, 100);
  assert.ok(requests[1].messages[1].content.startsWith("PREVIOUS HANDOFF NOTE"));
  assert.equal(again[0].content!.split("<summary>").length, 2);
  assert.equal(basePrompt(again[0].content!), "base prompt");
  assert.ok(previousSummary(again[0].content!).includes("Still listing."));
  setClient(null);
});

test("render flattens roles and tool calls; the system prompt is left out", () => {
  const text = render(transcript().slice(0, 4));
  assert.ok(!text.includes("base prompt"));
  assert.ok(text.startsWith("USER: first ask"));
  assert.ok(text.includes("ASSISTANT: \n[called bash:"));
});
