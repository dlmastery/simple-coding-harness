import assert from "node:assert/strict";
import { test } from "node:test";

import { setClient } from "../llm.ts";
import * as subagent from "../subagent.ts";
import * as tools from "../tools.ts";
import { ui } from "../ui.ts";
import { call, fakeClient, say, use, workspace, type Request } from "./fake.ts";

workspace();

test("toolset withholds edits, the plan and recursion", async () => {
  const names = new Set((await subagent.toolset()).map((s) => s.function.name));
  const expected = new Set(Object.keys(tools.TOOLS).filter((n) => !subagent.WITHHELD.has(n)));
  assert.deepEqual(names, expected);
  for (const withheld of ["task", "write_todos", "str_replace", "write_file"]) assert.ok(!names.has(withheld));
  assert.ok(names.has("bash"));
});

test("the subagent starts empty and returns only its report", async () => {
  const requests: Request[] = [];
  setClient(fakeClient([use(call("s1", "bash", { command: "echo found-it" })), say("report: found-it at x.py:3")], requests));

  assert.equal(await subagent.task({ description: "where is found-it?" }), "report: found-it at x.py:3");
  const first = requests[0];
  assert.deepEqual(first.messages.map((m: { role: string }) => m.role), ["system", "user"]); // rule 1
  assert.ok(!first.tools.some((s: { function: { name: string } }) => s.function.name === "task")); // rule 2
  const fed = requests[1].messages[3];
  assert.equal(fed.role, "tool");
  assert.ok(fed.content.includes("found-it")); // rule 3
  setClient(null);
});

test("the main agent gets the report and the same permissions", async () => {
  ui.approve = async () => false;
  const [, blocked] = await tools.execute(call("m1", "bash", { command: "sudo ls" }));
  assert.ok(blocked.startsWith("Blocked by policy"));
  const [, declined] = await tools.execute(call("m2", "bash", { command: "python -c 1" }));
  assert.equal(declined, "The user denied this tool call.");
  ui.approve = async () => true;
  assert.equal(tools.TOOLS.task, subagent.task);
  assert.ok(tools.TOOL_SCHEMAS.some((s) => s.function.name === "task"));
});

test("a runaway subagent is cut off", async () => {
  subagent.setMaxTurns(2);
  setClient(fakeClient([
    { content: "still looking", tool_calls: [call("x", "bash", { command: "echo more" })] },
    { content: "still looking", tool_calls: [call("y", "bash", { command: "echo more" })] },
  ]));
  const out = await subagent.task({ description: "q" });
  assert.ok(out.startsWith("(stopped after 2 turns"));
  assert.ok(out.includes("still looking"));
  subagent.setMaxTurns(12);
  setClient(null);
});
