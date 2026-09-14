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
