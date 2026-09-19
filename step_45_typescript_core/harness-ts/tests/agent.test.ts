import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";

import { turn } from "../agent.ts";
import { STUB, TRIMMED } from "../history.ts";
import { setClient } from "../llm.ts";
import * as sandbox from "../sandbox.ts";
import * as session from "../session.ts";
import { TODOS, writeTodos } from "../todos.ts";
import { execute, readFile, strReplace, writeFile } from "../tools.ts";
import type { Message, ToolCall } from "../types.ts";
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

test("bad arguments, an unknown tool, a raising tool and a missing argument each get one tool message and the loop goes on", async () => {
  const broken: ToolCall = { id: "e1", type: "function", function: { name: "bash", arguments: "{not json" } };
  setClient(fakeClient([
    use(broken, call("e2", "no_such_tool", { x: 1 }), call("e3", "read_file", { path: "missing.txt" }), call("e4", "bash", {})),
    say("done"),
  ]));
  const messages = await turn([{ role: "system", content: "sys" }], "go");
  const results = Object.fromEntries(messages.filter((m) => m.role === "tool").map((m) => [m.tool_call_id, m.content]));
  assert.match(results.e1!, /^Error: the arguments of bash are not a JSON object: /);
  assert.equal(results.e2, "Error: no tool named 'no_such_tool'.");
  assert.match(results.e3!, /^Error: Error: ENOENT/);
  assert.equal(results.e4, "Blocked by policy: bash: missing argument 'command'");
  assert.deepEqual(messages.at(-1), { role: "assistant", content: "done" }); // every call answered, the loop went on
  const [args] = await execute({ id: "e5", type: "function", function: { name: "bash", arguments: "[1, 2]" } });
  assert.deepEqual(args, {}); // an array is not an object either
  setClient(null);
});

test("a UTF-8 round trip through the file tools, a parent directory made on the way, and an empty old_str refused", () => {
  const text = "héllo — ünïcode ✓\r\nsecond line\n";
  assert.equal(writeFile({ path: "deep/er/u.txt", content: text }), "Wrote deep/er/u.txt");
  assert.equal(readFileSync(join(dir, "deep/er/u.txt"), "utf-8"), text);
  assert.equal(readFile({ path: "deep/er/u.txt" }), text);
  assert.equal(strReplace({ path: "deep/er/u.txt", old_str: "ünïcode", new_str: "unicode" }), "Replaced 1 match(es) in deep/er/u.txt");
  assert.match(strReplace({ path: "deep/er/u.txt", old_str: "", new_str: "x" }), /^Error: old_str is empty/);
});

test("a command that outlives its timeout is killed and what it printed comes back", async () => {
  const started = Date.now();
  const script = "console.log('partial'); setTimeout(() => {}, 30000)";
  await assert.rejects(sandbox.run(`node -e "${script}"`, 1), (failure: unknown) => {
    assert.ok(failure instanceof sandbox.TimedOut);
    assert.match(failure.output, /partial/);
    return true;
  });
  assert.ok(Date.now() - started < 10000); // the kill reached the process; the promise did not wait for the 30 s timer
});

test("write_todos with a bad status is an error and leaves the list alone", () => {
  assert.equal(writeTodos({ todos: [{ content: "a", activeForm: "doing a", status: "in_progress" }] }), "[~] a");
  assert.equal(writeTodos({ todos: [{ content: "b", activeForm: "doing b", status: "done" as any }] }), "Error: item 0 has status 'done'; use one of pending, in_progress, completed.");
  assert.deepEqual(TODOS.map((t) => t.content), ["a"]);
  assert.equal(writeTodos({ todos: "nope" as any }), "Error: todos must be a list.");
  TODOS.length = 0;
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
