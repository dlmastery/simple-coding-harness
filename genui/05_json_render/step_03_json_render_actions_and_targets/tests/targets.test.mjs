// Offline checks of the two targets: the React registry through
// react-dom/server and the ink registry through a fake terminal. The same
// scripted spec goes to both.
import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToString } from "react-dom/server";
import htm from "htm";
import { Renderer, JSONUIProvider } from "@json-render/react";
import { catalog, PROMPT } from "../catalog.mjs";
import { registry } from "../registry.mjs";
import { renderSpecToText } from "../ink_render.mjs";

const html = htm.bind(React.createElement);

const SPEC = {
  root: "card-1",
  elements: {
    "card-1": { type: "Card", props: { title: "Lemonade", subtitle: "Week 33" }, children: ["row-1", "table-1", "chart-1", "button-1", "button-2", "notes"] },
    "row-1": { type: "Row", props: { gap: "large" }, children: ["metric-1"] },
    "metric-1": { type: "Metric", props: { label: "Sales", value: { $state: "/sales/total" }, delta: "+8%" }, children: [] },
    "table-1": { type: "Table", props: { columns: ["Day", "Cups"], rows: [["Mon", "12"], ["Tue", "30"]] }, children: [] },
    "chart-1": { type: "Chart", props: { kind: "bar", labels: ["Mon", "Tue"], values: [12, 30] }, children: [] },
    "button-1": { type: "Button", props: { label: "Refresh", variant: "primary" }, on: { press: { action: "refresh_numbers" } }, children: [] },
    "button-2": { type: "Button", props: { label: "Notes", variant: "secondary" }, on: { press: { action: "setState", params: { statePath: "/showNotes", value: true } } }, children: [] },
    notes: { type: "Card", props: { title: "Notes" }, visible: { $state: "/showNotes" }, children: ["notes-text"] },
    "notes-text": { type: "Text", props: { text: "Saturday was the best day." }, children: [] },
  },
  state: { sales: { total: "$250" }, showNotes: false },
};

function renderReact(spec) {
  return renderToString(html`
    <${JSONUIProvider} registry=${registry} initialState=${{ ...(spec.state ?? {}) }}>
      <${Renderer} spec=${spec} registry=${registry} />
    <//>`);
}

test("the catalog has seven components and two actions, and the prompt lists them", () => {
  assert.equal(catalog.componentNames.length, 7);
  assert.deepEqual(catalog.actionNames, ["refresh_numbers", "show_details"]);
  assert.match(PROMPT, /^- Button: /m);
  assert.match(PROMPT, /^- refresh_numbers: /m);
  assert.match(PROMPT, /^- show_details: /m);
  assert.match(PROMPT, /^- setState: .*\[built-in\]/m);
});

test("the library accepts a spec with on and visible fields", () => {
  const result = catalog.validate(SPEC);
  assert.equal(result.success, true, JSON.stringify(result));
});

test("the React target renders buttons and hides the notes card", () => {
  const out = renderReact(SPEC);
  assert.match(out, /<button class="button primary">Refresh<\/button>/);
  assert.match(out, /<button class="button secondary">Notes<\/button>/);
  assert.match(out, /\$250/, "$state resolved");
  assert.doesNotMatch(out, /Saturday was the best day/, "visible is false");
  const shown = renderReact({ ...SPEC, state: { ...SPEC.state, showNotes: true } });
  assert.match(shown, /Saturday was the best day/);
});

test("the ink target renders the same spec as text", async () => {
  const out = await renderSpecToText(SPEC, { columns: 60 });
  assert.match(out, /Lemonade/);
  assert.match(out, /SALES/);
  assert.match(out, /\$250/, "$state resolved in the terminal too");
  assert.match(out, /Mon\s+12/);
  assert.match(out, /Tue\s+█+\s+30/, "the chart is a row of blocks");
  assert.match(out, /\[ Refresh \]/);
  assert.doesNotMatch(out, /Saturday was the best day/, "visible is false in the terminal too");
});

test("one spec, two renderers: every text the page shows, the terminal shows", async () => {
  const web = renderReact(SPEC).replace(/<[^>]+>/g, " ");
  const terminal = await renderSpecToText(SPEC, { columns: 60 });
  for (const text of ["Lemonade", "Week 33", "$250", "+8%", "Mon", "Refresh", "Notes"]) {
    assert.ok(web.includes(text), `web: ${text}`);
    assert.ok(terminal.includes(text), `terminal: ${text}`);
  }
});
