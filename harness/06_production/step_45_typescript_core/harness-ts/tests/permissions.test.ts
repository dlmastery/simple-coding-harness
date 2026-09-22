import assert from "node:assert/strict";
import { join } from "node:path";
import { test } from "node:test";

import { check, decide, fnmatch, insideProject, setProject, splitCommand } from "../permissions.ts";

test("read-only commands are allowed, unknown ones ask, risky ones are denied", () => {
  assert.equal(decide("ls -la"), "allow");
  assert.equal(decide("git status --short"), "allow");
  assert.equal(decide("python -c 1"), "ask");
  assert.equal(decide("sudo ls"), "deny");
  assert.equal(decide("git push origin main"), "deny");
});

test("the strictest verdict of a compound command wins", () => {
  assert.equal(decide("ls | grep x"), "allow");
  assert.equal(decide("ls && python setup.py"), "ask");
  assert.equal(decide("ls; rm -rf build"), "deny");
});

test("separators inside quotes do not split the command", () => {
  assert.deepEqual(splitCommand('echo "a | b" && ls; cat x || rm y'), ['echo "a | b"', "ls", "cat x", "rm y"]);
  assert.deepEqual(splitCommand("grep 'a;b' file"), ["grep 'a;b' file"]);
  assert.equal(decide('echo "a; rm x"'), "allow");
});

test("fnmatch follows the Python rules", () => {
  assert.ok(fnmatch("git log --oneline", "git log*"));
  assert.ok(!fnmatch("gitk", "git *"));
  assert.ok(fnmatch("cat a.txt", "cat *"));
  assert.ok(fnmatch("x1", "x[0-9]"));
  assert.ok(!fnmatch("xa", "x[!a-z]"));
  assert.ok(fnmatch("a.b", "a.b"));
  assert.ok(!fnmatch("axb", "a.b"));
});

test("writes outside the project ask; inside they are allowed", () => {
  const project = join(process.cwd(), "fence");
  setProject(project);
  assert.deepEqual(check("write_file", { path: join(project, "a.txt"), content: "" }), ["allow", null]);
  const [action, reason] = check("str_replace", { path: join(process.cwd(), "elsewhere.txt"), old_str: "a", new_str: "b" });
  assert.equal(action, "ask");
  assert.match(reason ?? "", /str_replace outside/);
  assert.ok(insideProject(project));
  assert.ok(!insideProject(join(process.cwd(), "fence-sibling")));
  assert.deepEqual(check("read_file", { path: "/etc/hosts" }), ["allow", null]);
  const [bashAction, bashReason] = check("bash", { command: "curl x" });
  assert.equal(bashAction, "deny");
  assert.equal(bashReason, "run: curl x");
});
