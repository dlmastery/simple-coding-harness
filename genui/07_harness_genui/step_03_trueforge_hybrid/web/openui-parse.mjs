// Generative UI step 03 - the OpenUI Lang parser, same shape as openui_parse.py.
//
// Statements `name = expr`, one per line. Values: "strings", numbers,
// true/false/null, [lists], Component(args), a + b, and references to other
// statements, forward or backward. feed() takes any chunk; tree() resolves
// from "root" with missing statements marked {type: "Pending", ref}.
//
// New in step 03: partial() reads the held-back line leniently, so a long
// statement such as `art = HtmlArtifact("Title", "<html>...` appears in the
// tree as {type: "HtmlArtifact", args, partial: true} while its document
// string is still arriving.

const TOKEN = /\s*(?:("(?:[^"\\]|\\.)*")|(-?\d+(?:\.\d+)?)|([A-Za-z_]\w*)|([()\[\],+=]))/y;
const ESCAPES = { n: "\n", t: "\t", '"': '"', "\\": "\\" };
const PARTIAL_HEAD = /^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\(([\s\S]*)$/;
const SCALAR = /-?\d+(?:\.\d+)?|[A-Za-z_]\w*/y;

// Decode the double-quoted string at `start`: [value, index after it, closed].
// An unterminated string decodes as far as the text goes, a trailing lone
// backslash dropped, so a streaming document can be shown part-way.
export function readString(text, start) {
  let out = "";
  let i = start + 1;
  while (i < text.length) {
    const ch = text[i];
    if (ch === "\\") {
      if (i + 1 >= text.length) break;
      out += ESCAPES[text[i + 1]] ?? text[i + 1];
      i += 2;
    } else if (ch === '"') {
      return [out, i + 1, true];
    } else {
      out += ch;
      i++;
    }
  }
  return [out, text.length, false];
}

export function tokenize(line) {
  const tokens = [];
  line = line.trim();
  TOKEN.lastIndex = 0;
  while (TOKEN.lastIndex < line.length) {
    const start = TOKEN.lastIndex;
    const m = TOKEN.exec(line);
    if (!m || m.index !== start || m[0].length === 0) throw new Error(`unexpected text at ${start}: ${line.slice(start, start + 12)}`);
    if (m[1] !== undefined) tokens.push({ kind: "str", value: m[1].slice(1, -1).replace(/\\(.)/g, (_, c) => ESCAPES[c] ?? c) });
    else if (m[2] !== undefined) tokens.push({ kind: "num", value: Number(m[2]) });
    else if (m[3] !== undefined) tokens.push({ kind: "id", value: m[3] });
    else tokens.push({ kind: "punct", value: m[4] });
  }
  return tokens;
}

// True when brackets balance and no string is open: the line can be parsed.
export function complete(line) {
  let depth = 0;
  let inStr = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inStr) {
      if (ch === "\\") i++;
      else if (ch === '"') inStr = false;
    } else if (ch === '"') inStr = true;
    else if (ch === "(" || ch === "[") depth++;
    else if (ch === ")" || ch === "]") depth--;
  }
  return depth <= 0 && !inStr;
}

export function parseStatement(line) {
  if (!line.trim() || line.trimStart().startsWith("#")) return null;
  const tokens = tokenize(line);
  if (tokens.length < 3 || tokens[0].kind !== "id" || tokens[1].value !== "=") throw new Error(`expected \`name = value\`: ${line.trim()}`);
  const [expr, end] = parseExpr(tokens, 2);
  if (end !== tokens.length) throw new Error(`trailing tokens in ${line.trim()}`);
  return { name: tokens[0].value, expr };
}

function parseExpr(tokens, i) {
  let [left, next] = parseValue(tokens, i);
  while (next < tokens.length && tokens[next].value === "+" && tokens[next].kind === "punct") {
    const [right, after] = parseValue(tokens, next + 1);
    left = ["add", left, right];
    next = after;
  }
  return [left, next];
}

function parseValue(tokens, i) {
  const token = tokens[i];
  if (!token) throw new Error("unexpected end of statement");
  if (token.kind === "str") return [["str", token.value], i + 1];
  if (token.kind === "num") return [["num", token.value], i + 1];
  if (token.kind === "id") {
    if (token.value === "true" || token.value === "false") return [["bool", token.value === "true"], i + 1];
    if (token.value === "null") return [["null", null], i + 1];
    if (tokens[i + 1] && tokens[i + 1].value === "(" && tokens[i + 1].kind === "punct") {
      const [args, next] = parseList(tokens, i + 2, ")");
      return [["call", token.value, args], next];
    }
    return [["ref", token.value], i + 1];
  }
  if (token.kind === "punct" && token.value === "[") {
    const [items, next] = parseList(tokens, i + 1, "]");
    return [["list", items], next];
  }
  throw new Error(`unexpected token ${token.value}`);
}

function parseList(tokens, i, closer) {
  const items = [];
  for (;;) {
    if (i >= tokens.length) throw new Error(`missing ${closer}`);
    if (tokens[i].kind === "punct" && tokens[i].value === closer) return [items, i + 1];
    const [item, next] = parseExpr(tokens, i);
    items.push(item);
    i = next;
    if (tokens[i] && tokens[i].kind === "punct" && tokens[i].value === ",") i++;
  }
}

export class Parser {
  constructor() {
    this.statements = new Map();
    this.buffer = "";
    this.errors = [];
  }

  // Add a chunk. Every complete statement it finishes is parsed now; an
  // unfinished line (open bracket, open string, no newline) is held back.
  feed(text) {
    this.buffer += text;
    for (;;) {
      let start = 0;
      let cut = -1;
      while (cut === -1) {
        const nl = this.buffer.indexOf("\n", start);
        if (nl === -1) return;
        if (complete(this.buffer.slice(0, nl))) cut = nl;
        start = nl + 1;
      }
      const line = this.buffer.slice(0, cut);
      this.buffer = this.buffer.slice(cut + 1);
      this.addLine(line.replace(/\n/g, " "));
    }
  }

  // The line in progress, read leniently: {name, type, args} or null. Only
  // the shape `name = Component(scalar, scalar, ...)` is read, which is what
  // a streaming HtmlArtifact looks like; the open string at the end is
  // decoded as far as it goes.
  partial() {
    const head = PARTIAL_HEAD.exec(this.buffer);
    if (!head) return null;
    const [, name, type, rest] = head;
    const args = [];
    let i = 0;
    while (i < rest.length) {
      const ch = rest[i];
      if (ch === " " || ch === "," || ch === "\n") i++;
      else if (ch === '"') {
        const [value, next, closed] = readString(rest, i);
        args.push(value);
        i = next;
        if (!closed) break;
      } else {
        SCALAR.lastIndex = i;
        const m = SCALAR.exec(rest);
        if (!m) break;
        args.push(/^-?\d/.test(m[0]) ? Number(m[0]) : m[0]);
        i = SCALAR.lastIndex;
      }
    }
    return { name, type, args };
  }

  close() {
    if (this.buffer.trim()) this.addLine(this.buffer);
    this.buffer = "";
  }

  addLine(line) {
    try {
      const statement = parseStatement(line);
      if (statement) this.statements.set(statement.name, statement.expr);
    } catch (e) {
      this.errors.push(e.message);
    }
  }

  tree(name = "root") {
    if (!this.statements.has(name)) return { type: "Pending", ref: name };
    return this.resolve(this.statements.get(name), new Set([name]));
  }

  resolve(expr, path) {
    const [kind] = expr;
    if (kind === "str" || kind === "num" || kind === "bool" || kind === "null") return expr[1];
    if (kind === "list") return expr[1].map((item) => this.resolve(item, path));
    if (kind === "add") {
      const left = this.resolve(expr[1], path);
      const right = this.resolve(expr[2], path);
      return typeof left === "string" || typeof right === "string" ? `${left}${right}` : left + right;
    }
    if (kind === "call") return { type: expr[1], args: expr[2].map((a) => this.resolve(a, path)) };
    const name = expr[1];
    if (path.has(name)) return { type: "Cycle", ref: name };
    if (!this.statements.has(name)) {
      const partial = this.partial(); // the line in progress, if it is this statement
      if (partial && partial.name === name) return { type: partial.type, args: partial.args, partial: true };
      return { type: "Pending", ref: name };
    }
    return this.resolve(this.statements.get(name), new Set([...path, name]));
  }

  // Every referenced name that has no statement yet.
  pending() {
    const missing = [];
    const walk = (expr) => {
      const [kind] = expr;
      if (kind === "ref" && !this.statements.has(expr[1]) && !missing.includes(expr[1])) missing.push(expr[1]);
      else if (kind === "list") expr[1].forEach(walk);
      else if (kind === "call") expr[2].forEach(walk);
      else if (kind === "add") { walk(expr[1]); walk(expr[2]); }
    };
    for (const expr of this.statements.values()) walk(expr);
    return missing;
  }
}

export function parse(program) {
  const parser = new Parser();
  parser.feed(program.endsWith("\n") ? program : program + "\n");
  parser.close();
  return parser;
}
