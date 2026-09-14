import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement as h } from "react";
import { renderToString } from "react-dom/server";
import { Renderer, createParser, createStreamingParser } from "@openuidev/react-lang";
import { library, PROMPT_OPTIONS } from "../library.mjs";

const schema = library.toJSONSchema();

test("the catalog has eight components with positional order from the Zod keys", () => {
  assert.deepEqual(Object.keys(schema.$defs), ["Stack", "Text", "Metric", "Table", "BarChart", "Card", "Button", "Input"]);
  assert.deepEqual(Object.keys(schema.$defs.Metric.properties), ["label", "value", "delta"]);
  assert.deepEqual(schema.$defs.Metric.required, ["label", "value"]);
});

test("library.prompt() writes one signature per component", () => {
  const prompt = library.prompt(PROMPT_OPTIONS);
  assert.match(prompt, /^Metric\(label: string, value: string \| number, delta\?: string\)/m);
  assert.match(prompt, /root = Stack\(/);
  assert.ok(prompt.startsWith(PROMPT_OPTIONS.preamble));
});

test("createParser maps positional arguments to named props", () => {
  const parser = createParser(schema, "Stack");
  const result = parser.parse('root = Stack([m])\nm = Metric("Revenue", 482, "+12%")\n');
  assert.equal(result.root.typeName, "Stack");
  assert.deepEqual(result.root.props.children[0].props, { label: "Revenue", value: 482, delta: "+12%" });
  assert.deepEqual(result.meta.unresolved, []);
});

test("an unknown component is reported with a code", () => {
  const result = createParser(schema, "Stack").parse("root = Stack([g])\ng = Gauge(1)\n");
  assert.equal(result.meta.errors[0].code, "unknown-component");
});

test("the streaming parser resolves forward references as chunks arrive", () => {
  const sp = createStreamingParser(schema, "Stack");
  let result = sp.push('root = Stack([title, chart])\ntitle = Text("Lemo');
  assert.equal(result.meta.incomplete, true);
  assert.ok(result.meta.unresolved.includes("chart"));
  result = sp.push('nade")\nchart = BarChart("Cups", ["Mon"], [3])\n');
  assert.equal(result.meta.unresolved.length, 0);
  assert.deepEqual(result.root.props.children.map((c) => c.typeName), ["Text", "BarChart"]);
});

test("<Renderer> renders the catalog components from OpenUI Lang", () => {
  const response = 'root = Stack([m, t])\nm = Metric("Cups", 241, "+8%")\nt = Table(["A"], [[1]])\n';
  const html = renderToString(h(Renderer, { response, library, isStreaming: false }));
  assert.match(html, /class="metric"/);
  assert.match(html, /<div class="value">241<\/div>/);
  assert.match(html, /<td>1<\/td>/);
});
