import { test } from "node:test";
import assert from "node:assert/strict";

import { parsePartial, isPartial } from "../page/partial-json.mjs";

const FULL = JSON.stringify({
  root: "r",
  elements: {
    r: { type: "Card", props: { title: 'Lemonade "stand" é' }, children: ["a", "b"] },
    a: { type: "Metric", props: { title: "Cups", value: "412", delta: "+12%" } },
    b: { type: "Chart", props: { kind: "bar", labels: ["Mon"], values: [1.5, -2, 300, true, null] } },
  },
});

test("a complete document parses like JSON.parse and is not partial", () => {
  const value = parsePartial(FULL);
  assert.deepEqual(value, JSON.parse(FULL));
  assert.equal(isPartial(value), false);
  assert.equal(isPartial(value.elements.r), false);
});

test("every prefix parses without throwing", () => {
  for (let n = 0; n <= FULL.length; n++) parsePartial(FULL.slice(0, n));
});

test("open containers are marked partial, closed ones inside them are not", () => {
  const cut = FULL.indexOf('"a":{') + 5; // inside element a, after root closed
  const value = parsePartial(FULL.slice(0, cut));
  assert.equal(isPartial(value), true);
  assert.equal(isPartial(value.elements), true);
  assert.equal(isPartial(value.elements.r), false);
  assert.deepEqual(value.elements.r.children, ["a", "b"]);
});

test("cut scalars are dropped, cut strings are kept", () => {
  assert.deepEqual(parsePartial('{"a": tr'), {});
  assert.deepEqual(parsePartial('{"a": -'), {});
  assert.deepEqual(parsePartial('{"a": 1.'), {});
  assert.deepEqual(parsePartial('{"a": 1.5, "b": nul'), { a: 1.5 });
  assert.deepEqual(parsePartial('{"title": "Lemon'), { title: "Lemon" });
  assert.deepEqual(parsePartial('{"title": "Lemon\\'), { title: "Lemon" });
  assert.deepEqual(parsePartial('{"ti'), {});
  assert.equal(parsePartial("   "), null);
});
