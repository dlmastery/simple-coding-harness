import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { tokenize, splitStatements, parseProgram, parse, catalogFromSchema, StreamingParser } from "../openui-parse.mjs";

const catalog = catalogFromSchema(JSON.parse(readFileSync(new URL("../catalog.json", import.meta.url), "utf-8")));

test("tokenize: strings with escapes, numbers, words", () => {
  const kinds = tokenize('a = Text("say \\"hi\\"", -2.5, true, null)').map((t) => t.kind);
  assert.deepEqual(kinds, ["IDENT", "EQUALS", "TYPE", "LPAREN", "STR", "COMMA", "NUM", "COMMA", "BOOL", "COMMA", "NULL", "RPAREN", "EOF"]);
  assert.equal(tokenize('"say \\"hi\\""')[0].value, 'say "hi"');
});

test("splitStatements holds back the unfinished line", () => {
  const { complete, pending } = splitStatements('root = Stack([a])\na = Text("un');
  assert.deepEqual(complete, ["root = Stack([a])"]);
  assert.equal(pending, 'a = Text("un');
});

test("a newline inside brackets does not end the statement", () => {
  const { complete } = splitStatements("root = Stack([\n  a,\n  b\n])\n");
  assert.equal(complete.length, 1);
});

test("forward references resolve; missing ones become placeholders", () => {
  const result = parse('root = Stack([a, b])\na = Text("A")\n', catalog);
  assert.equal(result.root.props.children[0].typeName, "Text");
  assert.deepEqual(result.root.props.children[1], { type: "placeholder", name: "b" });
  assert.deepEqual(result.unresolved, ["b"]);
});

test("positional arguments map to catalog property names", () => {
  const result = parse('root = Metric("Revenue", 482, "+12%")\n', catalog);
  assert.deepEqual(result.root.props, { label: "Revenue", value: 482, delta: "+12%" });
});

test("unknown components are reported and dropped", () => {
  const result = parse('root = Stack([x])\nx = Gauge(1)\n', catalog);
  assert.deepEqual(result.root.props.children, []);
  assert.deepEqual(result.errors, ["unknown component Gauge"]);
});

test("fences and comments are ignored", () => {
  const program = parseProgram('```openui\nroot = Text("a") // a comment\n# another\n```\n');
  assert.deepEqual([...program.statements.keys()], ["root"]);
});

test("streaming: the tree grows as chunks arrive", () => {
  const sp = new StreamingParser(catalog);
  let r = sp.push('root = Stack([t])\nt = Text("Lemo');
  assert.equal(r.incomplete, true);
  assert.deepEqual(r.unresolved, ["t"]);
  r = sp.push('nade")\n');
  assert.equal(r.incomplete, false);
  assert.equal(r.root.props.children[0].props.text, "Lemonade");
  assert.deepEqual(sp.finish().unresolved, []);
});
