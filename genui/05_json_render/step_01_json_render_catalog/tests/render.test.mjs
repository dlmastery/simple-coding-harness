// Offline checks of the catalog, the prompt and the registry. The registry is
// rendered with react-dom/server, so the real @json-render/react code runs
// here with no browser.
import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToString } from "react-dom/server";
import htm from "htm";
import { Renderer, JSONUIProvider } from "@json-render/react";
import { catalog, PROMPT } from "../catalog.mjs";
import { registry } from "../registry.mjs";

const html = htm.bind(React.createElement);

const SPEC = {
  root: "card-1",
  elements: {
    "card-1": { type: "Card", props: { title: "Lemonade", subtitle: null }, children: ["row-1", "table-1", "chart-1"] },
    "row-1": { type: "Row", props: { gap: "large" }, children: ["metric-1", "metric-2"] },
    "metric-1": { type: "Metric", props: { label: "Sales", value: "$250", delta: "+8%" }, children: [] },
    "metric-2": { type: "Metric", props: { label: "Best day", value: { $state: "/sales/bestDay" }, delta: null }, children: [] },
    "table-1": { type: "Table", props: { columns: ["Day", "Cups"], rows: [["Mon", "12"], ["Tue", "30"]] }, children: [] },
    "chart-1": { type: "Chart", props: { kind: "bar", labels: ["Mon", "Tue"], values: [12, 30] }, children: [] },
  },
  state: { sales: { bestDay: "Tuesday" } },
};

function render(spec) {
  return renderToString(html`
    <${JSONUIProvider} registry=${registry} initialState=${spec.state ?? {}}>
      <${Renderer} spec=${spec} registry=${registry} />
    <//>`);
}

test("the catalog has the six components and the prompt names each one", () => {
  assert.deepEqual(catalog.componentNames, ["Card", "Row", "Text", "Metric", "Table", "Chart"]);
  for (const name of catalog.componentNames) {
    assert.match(PROMPT, new RegExp(`^- ${name}: `, "m"));
  }
  assert.match(PROMPT, /Reply with ONE JSON object/);
});

test("the library accepts the spec shape", () => {
  const result = catalog.validate(SPEC);
  assert.equal(result.success, true, JSON.stringify(result));
});

test("the registry renders a spec, children in order, $state resolved", () => {
  const out = render(SPEC);
  assert.match(out, /<h2>Lemonade<\/h2>/);
  assert.match(out, /class="row gap-large"/);
  assert.ok(out.indexOf("Sales") < out.indexOf("Best day"), "metrics keep their order");
  assert.match(out, /Tuesday/, "the $state prop reads from spec.state");
  assert.match(out, /<td>30<\/td>/);
  assert.match(out, /class="bar" style="height:100%"/, "the tallest bar fills the chart");
});

test("a missing child renders nothing for that branch and no error", () => {
  const spec = { root: "card-1", elements: { "card-1": { type: "Card", props: { title: "Empty" }, children: ["ghost"] } } };
  const out = render(spec);
  assert.match(out, /<h2>Empty<\/h2>/);
  assert.doesNotMatch(out, /ghost/);
});
