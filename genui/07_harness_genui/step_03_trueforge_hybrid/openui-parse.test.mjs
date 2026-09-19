// The JS parser must agree with openui_parse.py on the same program, partial() included.
import { test } from "node:test";
import assert from "node:assert/strict";
import { Parser, parse, tokenize } from "./web/openui-parse.mjs";

const PROGRAM = `root = Stack([header, kpis, note], "column", "l")
header = TextContent("Lemonade stand", "large-heavy")
kpis = Stack([Card([TextContent("Cups", "small"), TextContent("" + cups, "large-heavy")])], "row")
cups = 370
note = TextContent("Done \\"today\\".", "default")
`;

test("tokenizer covers every literal", () => {
  const tokens = tokenize('x = Card(["a\\"b", -1.5, 3, true, null], y)');
  assert.deepEqual(tokens[5], { kind: "str", value: 'a"b' });
  assert.deepEqual(tokens[7], { kind: "num", value: -1.5 });
  assert.equal(tokens.length, 18);
});

test("forward references resolve into one tree", () => {
  const parsed = parse(PROGRAM);
  assert.deepEqual(parsed.errors, []);
  assert.deepEqual(parsed.pending(), []);
  const tree = parsed.tree();
  assert.equal(tree.type, "Stack");
  const [header, kpis, note] = tree.args[0];
  assert.deepEqual(header, { type: "TextContent", args: ["Lemonade stand", "large-heavy"] });
  assert.deepEqual(kpis.args[0][0].args[0][1].args, ["370", "large-heavy"]);
  assert.equal(note.args[0], 'Done "today".');
});

test("streaming feed holds back unfinished lines and marks pending", () => {
  const parser = new Parser();
  parser.feed('root = Stack([header, kpis], "col');
  assert.deepEqual(parser.tree(), { type: "Pending", ref: "root" });
  parser.feed('umn")\nheader = TextContent("Hi")\n');
  assert.deepEqual(parser.pending(), ["kpis"]);
  assert.deepEqual(parser.tree().args[0][1], { type: "Pending", ref: "kpis" });
  parser.feed('kpis = Stack([\n  header,\n  header\n], "row")\n');
  assert.deepEqual(parser.pending(), []);
  assert.equal(parser.tree().args[0][1].args[0].length, 2);
});

test("one unbalanced line does not hold back the rest; + on non-numbers is text", () => {
  const parsed = parse('a = Stack([x)\nb = TextContent("hi")\nroot = Stack([a, b])\n');
  assert.deepEqual([...parsed.statements.keys()], ["b", "root"]);
  assert.equal(parsed.errors.length, 1);
  assert.deepEqual(parsed.tree().args[0][1], { type: "TextContent", args: ["hi"] });
  assert.deepEqual(parse("root = Stack([x, y])\nx = null + 1\ny = 2 + 3\n").tree().args[0], ["null1", 5]);
});

test("errors are collected, cycles are marked", () => {
  const parsed = parse("a = Card(1))\nb = 1\nc = ?\nd = a\n");
  assert.equal(parsed.errors.length, 2);
  assert.equal(parsed.tree("d").type, "Pending");
  assert.deepEqual(parse("a = b\nb = a\n").tree("a"), { type: "Cycle", ref: "a" });
});

test("partial reads the open artifact line as far as it goes", () => {
  const parser = new Parser();
  parser.feed('root = Stack([intro, artifact])\nintro = TextContent("Hi")\nartifact = HtmlArtifact("Counter", "<html><body>a ');
  assert.deepEqual(parser.partial(), { name: "artifact", type: "HtmlArtifact", args: ["Counter", "<html><body>a "] });
  assert.deepEqual(parser.tree().args[0][1], { type: "HtmlArtifact", args: ["Counter", "<html><body>a "], partial: true });
  assert.deepEqual(parser.pending(), ["artifact"]);
  parser.feed('b</body></html>")\n');
  assert.equal(parser.partial(), null);
  assert.deepEqual(parser.pending(), []);
  assert.equal(parser.tree().args[0][1].args[1], "<html><body>a b</body></html>");
  assert.equal(parser.tree().args[0][1].partial, undefined);
});

test("partial decodes closed strings and scalars, and is null for other shapes", () => {
  const parser = new Parser();
  parser.feed('t = Tag("a", null, 3, -1.5');
  assert.deepEqual(parser.partial(), { name: "t", type: "Tag", args: ["a", "null", 3, -1.5] });
  const other = new Parser();
  other.feed("n = 42");
  assert.equal(other.partial(), null);
});
