// Step 03 - node --test: the view's catalog and the inner boundary, no browser.
import { test } from "node:test";
import assert from "node:assert/strict";

import { esc, Metric, Table, BarChart, Text, render, renderComponents, RENDERERS } from "./catalog.mjs";
import { CSP, META, sandboxed, isEvent } from "./sandbox.mjs";

// --- the catalog -----------------------------------------------------------

test("the catalog has exactly the four components the server's spec uses", () => {
  assert.deepEqual(Object.keys(RENDERERS).sort(), ["BarChart", "Metric", "Table", "Text"]);
});

test("every prop is escaped before it becomes markup", () => {
  assert.equal(esc('<b>&"'), "&lt;b&gt;&amp;&quot;");
  const html = Metric({ title: "<script>", value: "1", delta: "up" });
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>/);
  assert.match(Text({ text: "a & b" }), /a &amp; b/);
});

test("a table gets one header per column and one row per row", () => {
  const html = Table({ columns: ["day", "cups"], rows: [["Mon", "37"], ["Tue", "51"]] });
  assert.equal((html.match(/<th /g) || []).length, 2);
  assert.equal((html.match(/<tr>/g) || []).length, 3);
  assert.match(html, /<th class="num">cups<\/th>/);
});

test("a bar chart scales to the largest value and labels up to 14 bars", () => {
  const html = BarChart({ labels: ["Mon", "Tue"], values: [25, 50] });
  assert.match(html, /height:50%/);
  assert.match(html, /height:100%/);
  assert.match(html, /<span>Mon<\/span>/);
  const many = BarChart({ labels: Array(20).fill("d"), values: Array(20).fill(1) });
  assert.doesNotMatch(many, /<span>/);
  assert.match(BarChart({ labels: [], values: [] }), /class="bars"/);
});

test("an unknown component becomes a visible stub, not markup", () => {
  assert.match(render("GeneratedView", { html: "<b>x</b>" }), /unknown component: GeneratedView/);
  assert.doesNotMatch(render("GeneratedView", { html: "<b>x</b>" }), /<b>x<\/b>/);
});

test("renderComponents puts the metrics in one row and keeps the rest in order", () => {
  const html = renderComponents([
    { component: "Text", props: { text: "first" } },
    { component: "Metric", props: { title: "a", value: "1", delta: "" } },
    { component: "Metric", props: { title: "b", value: "2", delta: "" } },
    { component: "BarChart", props: { labels: ["x"], values: [1] } },
  ]);
  assert.match(html, /^<div class="cards">/);
  assert.equal((html.match(/class="card"/g) || []).length, 2);
  assert.ok(html.indexOf("first") < html.indexOf('class="bars"'));
  assert.equal(renderComponents([]), "");
  assert.equal(renderComponents(undefined), "");
});

// --- the inner boundary ----------------------------------------------------

test("the inner policy allows inline style and script and nothing else", () => {
  assert.match(CSP, /default-src 'none'/);
  assert.match(CSP, /script-src 'unsafe-inline'/);
  assert.doesNotMatch(CSP, /'self'/);
  assert.doesNotMatch(CSP, /connect-src/);   // default-src 'none' covers it: no network at all
  assert.match(META, /^<meta http-equiv="Content-Security-Policy"/);
});

test("the csp meta lands first in head, or first in the document", () => {
  const doc = "<!doctype html><html><head><title>x</title></head><body></body></html>";
  const out = sandboxed(doc);
  assert.ok(out.indexOf(META) < out.indexOf("<title>"));
  assert.ok(out.startsWith("<!doctype html><html><head><meta http-equiv"));
  assert.ok(sandboxed("<p>no head</p>").startsWith(META));
  assert.ok(sandboxed("<HEAD lang=en>a</HEAD>").startsWith("<HEAD lang=en><meta http-equiv"));
});

test("only one message shape crosses the inner boundary", () => {
  assert.equal(isEvent({ type: "event", name: "price_changed", payload: { price: 2 } }), true);
  assert.equal(isEvent({ type: "event", name: "no payload" }), true);
  assert.equal(isEvent({ jsonrpc: "2.0", id: 1, method: "tools/call" }), false);  // the region cannot speak MCP Apps
  assert.equal(isEvent({ type: "event" }), false);
  assert.equal(isEvent({ type: "evil", name: "x" }), false);
  assert.equal(isEvent("event"), false);
  assert.equal(isEvent(null), false);
});
