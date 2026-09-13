import assert from "node:assert/strict";
import { appendFileSync, copyFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import * as session from "../session.ts";
import type { Message } from "../types.ts";
import { workspace } from "./fake.ts";

const FIXTURES = join(dirname(fileURLToPath(import.meta.url)), "fixtures");
workspace();

test("save appends only what is new; rewind and compaction are entries, not rewrites", () => {
  session.state.current = "ts-written";
  session.state.written = 0;
  const messages: Message[] = [{ role: "system", content: "s" }, { role: "user", content: "one" }];
  session.save(messages);
  messages.push({ role: "assistant", content: "two" });
  session.save(messages);
  session.rewindTo(2);
  session.save([...messages.slice(0, 2), { role: "assistant", content: "three" }]);
  session.compacted([{ role: "system", content: "s + summary" }, { role: "assistant", content: "three" }]);

  const lines = readFileSync(session.pathFor("ts-written"), "utf-8").trim().split("\n").map((l) => JSON.parse(l));
  assert.deepEqual(lines.map((l) => Object.keys(l)[0]), ["role", "role", "role", "rewind_to", "role", "compacted"]);
  assert.deepEqual(session.load("ts-written"), [{ role: "system", content: "s + summary" }, { role: "assistant", content: "three" }]);
});

test("a session written by the Python harness loads to the same messages", () => {
  copyFileSync(join(FIXTURES, "python_session.jsonl"), session.pathFor("from-python"));
  assert.deepEqual(session.load("from-python"), [
    { role: "system", content: "You are a coding agent.\n\n<summary>\n## Goal\nGreet.\n</summary>" },
    { role: "user", content: "say héllo instead" },
    { role: "assistant", content: "héllo" },
    { role: "user", content: "thanks" },
  ]);
  assert.equal(session.title(session.load("from-python")), "say héllo instead");
});

test("a half-written last line, step 44 stamps and usage entries are skipped", () => {
  copyFileSync(join(FIXTURES, "python_session.jsonl"), session.pathFor("torn"));
  appendFileSync(session.pathFor("torn"), [
    '{"role": "assistant", "content": "stamped", "ts": 1789300000.5}',
    '{"usage": {"prompt_tokens": 1}, "index": 4, "ts": 1789300000.6}',
    '{"role": "assistant", "content": "cut off he',
  ].join("\n"));
  const loaded = session.load("torn");
  assert.equal(loaded.length, 5);
  assert.deepEqual(loaded.at(-1), { role: "assistant", content: "stamped" });
});

test("openSession becomes the past chat and keeps appending to it", () => {
  const messages = session.openSession("from-python");
  assert.equal(session.state.current, "from-python");
  assert.equal(session.state.written, 4);
  messages.push({ role: "assistant", content: "welcome" });
  session.save(messages);
  assert.equal(session.load("from-python").length, 5);
  assert.ok(session.allSessions().some((s) => s.id === "from-python" && s.title === "say héllo instead"));
});
