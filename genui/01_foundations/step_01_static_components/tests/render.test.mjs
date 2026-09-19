import { test } from "node:test";
import assert from "node:assert/strict";

import { render, Metric, Table, Chart } from "../page/render.mjs";

test("Metric renders the three props and marks a negative delta", () => {
  const html = Metric({ title: "Cups sold", value: "412", delta: "-3%" });
  assert.match(html, /Cups sold/);
  assert.match(html, /412/);
  assert.match(html, /delta down/);
});

test("props are escaped before they become markup", () => {
  const html = Metric({ title: "<img src=x onerror=alert(1)>", value: "1", delta: "+1" });
  assert.doesNotMatch(html, /<img/);
  assert.match(html, /&lt;img/);
});

test("Table renders one header per column and one row per row", () => {
  const html = Table({ columns: ["Day", "Cups"], rows: [["Mon", "40"], ["Tue", "52"]] });
  assert.equal((html.match(/<th>/g) || []).length, 2);
  assert.equal((html.match(/<tr>/g) || []).length, 3);
});

test("Chart draws one bar per value, or one polyline for a line chart", () => {
  const bars = Chart({ kind: "bar", labels: ["a", "b", "c"], values: [1, 2, 3] });
  assert.equal((bars.match(/<rect/g) || []).length, 3);
  const line = Chart({ kind: "line", labels: ["a", "b"], values: [1, 2] });
  assert.equal((line.match(/<polyline/g) || []).length, 1);
});

test("render falls back to a visible stub for an unknown component", () => {
  assert.match(render("Gauge", {}), /unknown component: Gauge/);
  assert.match(render("Metric", { title: "t", value: "v", delta: "+1" }), /class="card metric"/);
});

test("array props that are not arrays render as empty, not as a crash", () => {
  assert.match(Table({ columns: "Day", rows: "x" }), /<tbody><\/tbody>/);
  assert.match(Chart({ kind: "bar", labels: null, values: "1,2" }), /<svg/);
  assert.doesNotMatch(Chart({ kind: "bar", labels: ["a"], values: [-5] }), /height="-/);
});

test("prototype names are not components", () => {
  assert.match(render("constructor", {}), /unknown component: constructor/);
  assert.match(render("toString", {}), /unknown component/);
});
