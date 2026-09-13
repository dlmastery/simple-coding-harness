import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { turn } from "../agent.ts";
import { STUB, TRIMMED } from "../history.ts";
import { setClient } from "../llm.ts";
import * as session from "../session.ts";
import { TODOS } from "../todos.ts";
import type { Message } from "../types.ts";
import { call, fakeClient, say, use, workspace, type Request } from "./fake.ts";

const dir = workspace();

test("one turn: tool calls run, results go back to the model, the session log fills as it goes", async () => {
  writeFileSync(join(dir, "notes.txt"), "line\n".repeat(200));
  const requests: Request[] = [];
  setClient(fakeClient([
    use(call("c1", "read_file", { path: "notes.txt" }), call("c2", "write_file", { path: "out.txt", content: "done" })),
    say("wrote out.txt"),
  ], requests));

  let messages: Message[] = [{ role: "system", content: "sys" }];
  messages = await turn(messages, "read notes and write out.txt");

  assert.deepEqual(messages.map((m) => m.role), ["system", "user", "assistant", "tool", "tool", "assistant"]);
  assert.equal(readFileSync(join(dir, "out.txt"), "utf-8"), "done");
  assert.equal(messages[3].tool_call_id, "c1");
  assert.equal(messages[4].content, "Wrote out.txt");
  assert.equal(messages[5].content, "wrote out.txt");

  // the late injection rides along on every request but never enters the transcript
  const sent = requests[0].messages;
  assert.equal(sent[sent.length - 1].role, "user");
  assert.match(sent[sent.length - 1].content, /<env>/);
  assert.equal(requests[1].messages.length, 6); // five transcript messages plus the injection
  assert.ok(requests[1].messages[3].content.startsWith("line\nline"));

  // strip ran after the turn: the long read shrank to a stub, the short write did not
  assert.ok(messages[3].content!.startsWith("line\n".repeat(STUB / 5)));
  assert.ok(messages[3].content!.includes(TRIMMED));
  assert.equal(messages[4].content, "Wrote out.txt");

  // the log has one line per message, written before strip touched them
  const lines = readFileSync(session.pathFor("test-session"), "utf-8").trim().split("\n").map((l) => JSON.parse(l));
  assert.equal(lines.length, 6);
  assert.equal(lines[3].content, "line\n".repeat(200));
  assert.deepEqual(session.load("test-session").map((m: Message) => m.role), messages.map((m) => m.role));
  setClient(null);
});

test("a denied tool call becomes a result the model sees", async () => {
  const { ui } = await import("../ui.ts");
  ui.approve = async () => false;
  const requests: Request[] = [];
  setClient(fakeClient([use(call("c3", "bash", { command: "python -c 1" })), say("ok")], requests));
  const messages = await turn([{ role: "system", content: "sys" }], "run it");
  assert.equal(messages[3].content, "The user denied this tool call.");
  assert.equal(requests[1].messages[3].content, "The user denied this tool call.");
  ui.approve = async () => true;
  setClient(null);
});

test("write_todos replaces the plan and the reminder shows it on the next call", async () => {
  const requests: Request[] = [];
  const todos = [{ content: "Fix it", activeForm: "Fixing it", status: "in_progress" }];
  setClient(fakeClient([use(call("c4", "write_todos", { todos })), say("planned")], requests));
  await turn([{ role: "system", content: "sys" }], "plan");
  assert.deepEqual(TODOS, todos);
  const injected = requests[1].messages.at(-1).content;
  assert.match(injected, /<todos>\n\[~\] Fix it\n<\/todos>/);
  setClient(null);
});
