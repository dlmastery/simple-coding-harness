import { test } from "node:test";
import assert from "node:assert/strict";
import { applyPatch, splitPointer } from "./json-patch.mjs";

test("splitPointer unescapes ~1 and ~0", () => {
  assert.deepEqual(splitPointer("/a/b~1c/0/~0"), ["a", "b/c", "0", "~"]);
  assert.deepEqual(splitPointer(""), []);
});

test("applyPatch appends, replaces and removes", () => {
  const state = { dashboard: { metrics: [], table: null } };
  applyPatch(state, [
    { op: "add", path: "/dashboard/metrics/-", value: { title: "Cups", value: "120" } },
    { op: "add", path: "/dashboard/metrics/0", value: { title: "Cash", value: "$60" } },
    { op: "replace", path: "/dashboard/table", value: { columns: ["day"], rows: [["Mon"]] } },
  ]);
  assert.deepEqual(state.dashboard.metrics.map((m) => m.title), ["Cash", "Cups"]);
  assert.equal(state.dashboard.table.columns[0], "day");
  applyPatch(state, [{ op: "remove", path: "/dashboard/metrics/0" }, { op: "remove", path: "/dashboard/table" }]);
  assert.deepEqual(state, { dashboard: { metrics: [{ title: "Cups", value: "120" }] } });
});

test("applyPatch refuses prototype keys, bad indexes, missing parents and unknown ops", () => {
  const state = { list: [1], obj: {} };
  for (const bad of [
    { op: "add", path: "/__proto__/polluted", value: 1 },
    { op: "add", path: "/obj/constructor/prototype/polluted", value: 1 },
    { op: "add", path: "/list/x", value: 1 },
    { op: "add", path: "/nowhere/k", value: 1 },
    { op: "move", path: "/list/0", from: "/obj" },
    { op: "replace", path: "", value: {} },
  ]) {
    assert.throws(() => applyPatch(state, [bad]), new RegExp(""), JSON.stringify(bad));
  }
  assert.equal({}.polluted, undefined);
  assert.deepEqual(state, { list: [1], obj: {} });
});
