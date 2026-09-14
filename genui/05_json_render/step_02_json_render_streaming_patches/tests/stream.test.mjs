// Offline checks of the streaming side: the library's compiler on the fixture
// stream, cut at arbitrary points, and the registry rendering a spec that is
// still arriving. react-dom/server stands in for the browser.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToString } from "react-dom/server";
import htm from "htm";
import { createSpecStreamCompiler } from "@json-render/core";
import { Renderer, JSONUIProvider } from "@json-render/react";
import { PROMPT } from "../catalog.mjs";
import { registry } from "../registry.mjs";

const html = htm.bind(React.createElement);
const FIXTURE = readFileSync(new URL("./patches.jsonl", import.meta.url), "utf-8");

function render(spec) {
  return renderToString(html`
    <${JSONUIProvider} registry=${registry} initialState=${{ ...(spec.state ?? {}) }}>
      <${Renderer} spec=${spec} registry=${registry} />
    <//>`);
}

test("the prompt asks for JSONL patches and no longer for one object", () => {
  assert.match(PROMPT, /OUTPUT FORMAT \(JSONL, RFC 6902 JSON Patch\)/);
  assert.doesNotMatch(PROMPT, /Reply with ONE JSON object/);
});

test("chunk boundaries do not matter: 7-byte pushes equal one push", () => {
  const whole = createSpecStreamCompiler();
  whole.push(FIXTURE);
  const pieces = createSpecStreamCompiler();
  let applied = 0;
  for (let i = 0; i < FIXTURE.length; i += 7) {
    applied += pieces.push(FIXTURE.slice(i, i + 7)).newPatches.length;
  }
  assert.deepEqual(pieces.getResult(), whole.getResult());
  assert.equal(pieces.getPatches().length, 13);
  assert.equal(applied, 12, "the last line has no newline, so getResult applies it");
});

test("the compiled spec reflects every operation", () => {
  const compiler = createSpecStreamCompiler();
  compiler.push(FIXTURE);
  const spec = compiler.getResult();
  assert.equal(spec.elements["card-1"].props.subtitle, "Week 33", "replace");
  assert.equal("delta" in spec.elements["metric-1"].props, false, "remove");
  assert.deepEqual(spec.elements["table-1"].props.rows, [["Mon", "12"], ["Tue", "30"]], "add with - appends");
  assert.deepEqual(spec.state.days, [{ id: "mon", cups: 12 }]);
});

test("a partial spec renders what has arrived, and the state that has arrived", () => {
  const compiler = createSpecStreamCompiler();
  const lines = FIXTURE.split("\n");
  compiler.push(lines.slice(0, 5).join("\n") + "\n");
  const spec = compiler.getResult();
  const out = render(spec);
  assert.match(out, /<h2>Lemonade<\/h2>/);
  assert.match(out, /\$250/, "state patch applied before the metric renders");
  assert.doesNotMatch(out, /Best day/, "metric-2 has not arrived");
});

test("a root-only spec needs the elements guard the page adds", () => {
  const compiler = createSpecStreamCompiler();
  compiler.push('{"op":"add","path":"/root","value":"card-1"}\n');
  const rootOnly = compiler.getResult();
  assert.throws(() => render(rootOnly), /elements|undefined/);
  assert.equal(render({ ...rootOnly, elements: {} }), "");
});
