import { test } from "node:test";
import assert from "node:assert/strict";

import { render, renderTree, renderFlat, renderSpec, Metric, Table, Chart, Card, Button, RENDERERS } from "../page/render.mjs";
import { parsePartial } from "../page/partial-json.mjs";

test("Metric renders the three props and marks a negative delta", () => {
  const html = Metric({ title: "Cups sold", value: "412", delta: "-3%" });
  assert.match(html, /Cups sold/);
  assert.match(html, /delta down/);
});

test("props are escaped before they become markup", () => {
  const html = Metric({ title: "<img src=x onerror=alert(1)>", value: "1", delta: "+1" });
  assert.doesNotMatch(html, /<img/);
  assert.match(html, /&lt;img/);
  assert.match(Button({ label: "Go", action: '" onclick="x' }), /data-action="&quot; onclick=&quot;x"/);
});

test("Table and Chart render one element per row, bar or point", () => {
  assert.equal((Table({ columns: ["Day", "Cups"], rows: [["Mon", "40"], ["Tue", "52"]] }).match(/<tr>/g) || []).length, 3);
  assert.equal((Chart({ kind: "bar", labels: ["a", "b", "c"], values: [1, 2, 3] }).match(/<rect/g) || []).length, 3);
  assert.equal((Chart({ kind: "line", labels: ["a", "b"], values: [1, 2] }).match(/<polyline/g) || []).length, 1);
});

test("layout components wrap their rendered children", () => {
  assert.match(Card({ title: "T" }, "<i>inner</i>"), /heading">T<\/div><i>inner<\/i>/);
  assert.match(render("Row", {}, "x"), /class="row">x</);
  assert.match(render("Gauge", {}), /unknown component: Gauge/);
});

const TREE = {
  type: "Card", props: { title: "Stand" },
  children: [{ type: "Row", props: {}, children: [
    { type: "Metric", props: { title: "Cups", value: "412", delta: "+12%" } },
    { type: "Metric", props: { title: "Revenue", value: "$625", delta: "+10%" } },
  ] }],
};

const FLAT = {
  root: "card",
  elements: {
    card: { type: "Card", props: { title: "Stand" }, children: ["row"] },
    row: { type: "Row", props: {}, children: ["m1", "m2"] },
    m1: { type: "Metric", props: { title: "Cups", value: "412", delta: "+12%" } },
    m2: { type: "Metric", props: { title: "Revenue", value: "$625", delta: "+10%" } },
  },
};

test("both walkers render the same complete layout", () => {
  const a = renderTree(TREE), b = renderFlat(FLAT);
  assert.equal(a, b);
  assert.equal((a.match(/class="card metric"/g) || []).length, 2);
  assert.equal(renderSpec(null, "flat"), "");
});

test("a cut nested tree renders its closed leaves inside pending parents", () => {
  const text = JSON.stringify(TREE);
  const cut = text.indexOf('"Revenue"');
  const html = renderTree(parsePartial(text.slice(0, cut)));
  assert.equal((html.match(/class="card metric"/g) || []).length, 2); // one closed, one half-written
  assert.equal((html.match(/pending-wrap/g) || []).length, 3); // Card, Row and the open Metric
  assert.match(html, /Cups/);
});

test("a cut flat map keeps every slot the root announced, as pending", () => {
  const text = JSON.stringify(FLAT);
  const cut = text.indexOf('"m1":{') + 6; // root and row closed, m1 just opened
  const html = renderFlat(parsePartial(text.slice(0, cut)));
  assert.equal((html.match(/class="card pending"/g) || []).length, 2); // m1 and m2 reserved
  assert.equal((html.match(/pending-wrap/g) || []).length, 0); // nothing half-rendered
  assert.match(html, /heading">Stand</);
});

test("a flat map with a cycle or a missing root does not loop", () => {
  assert.match(renderFlat({ root: "a", elements: { a: { type: "Row", props: {}, children: ["a"] } } }), /pending/);
  assert.match(renderFlat({ root: "x", elements: {} }), /pending/);
});

test("GeneratedView puts the html in a sandboxed iframe with the CSP, escaped as an attribute", () => {
  const html = `<div style="color:red">gauge</div><script>parent.postMessage({type:"event",name:"x"},"*")</script>`;
  const out = RENDERERS.GeneratedView({ html });
  assert.match(out, /^<iframe class="card generated" sandbox="allow-scripts" srcdoc="/);
  assert.doesNotMatch(out, /<div style/); // the document is an attribute value now
  assert.match(out, /&lt;div style=&quot;color:red&quot;&gt;/);
  assert.match(out, /Content-Security-Policy/);
  assert.match(render("GeneratedView", {}), /srcdoc="&lt;meta http-equiv/); // no html: an empty sandboxed document
});
