import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { CAP, SPILLS, STUB, TRIMMED, cap, estimate, fit, strip, sweep } from "../history.ts";
import type { Message } from "../types.ts";

test("cap trims a long result and parks the whole text in a temp file until sweep", () => {
  const text = "x".repeat(CAP + 500);
  const capped = cap(text);
  assert.ok(capped.startsWith("x".repeat(CAP)));
  assert.ok(capped.includes(`${TRIMMED} 500 of ${CAP + 500} chars cut`));
  assert.equal(SPILLS.length, 1);
  const [path] = SPILLS;
  assert.ok(capped.includes(path));
  assert.equal(readFileSync(path, "utf-8"), text);
  sweep();
  assert.ok(!existsSync(path));
  assert.equal(SPILLS.length, 0);
  assert.equal(cap("short"), "short");
});

test("strip shrinks finished tool results once and leaves the rest alone", () => {
  const long = "y".repeat(STUB + 50);
  const messages: Message[] = [
    { role: "user", content: long },
    { role: "tool", tool_call_id: "a", content: long },
    { role: "tool", tool_call_id: "b", content: "tiny" },
  ];
  assert.equal(strip(messages), 1);
  assert.equal(messages[0].content, long);
  assert.ok(messages[1].content!.startsWith("y".repeat(STUB)));
  assert.ok(messages[1].content!.includes(`${TRIMMED} 50 more chars.`));
  assert.equal(messages[2].content, "tiny");
  assert.equal(strip(messages), 0); // a second pass is a no-op
});

test("fit drops whole tool results, oldest first, until the estimate fits", () => {
  const big = "z".repeat(4000);
  const messages: Message[] = [
    { role: "system", content: "s" },
    { role: "tool", tool_call_id: "1", content: big },
    { role: "tool", tool_call_id: "2", content: big },
    { role: "tool", tool_call_id: "3", content: big },
  ];
  const before = estimate(messages);
  assert.ok(before > 2000);
  const dropped = fit(messages, 1200);
  assert.equal(dropped, 2);
  assert.ok(messages[1].content!.includes("dropped to fit"));
  assert.ok(messages[2].content!.includes("dropped to fit"));
  assert.equal(messages[3].content, big);
  assert.equal(fit(messages, 1200), 0);
});
