// Step 01 - the same small OpenUI Lang parser, in JavaScript, for the page.
//
// Mirrors openui_parse.py function for function: tokenize -> splitStatements
// -> parseStatement -> resolve. The tests compare the two on program.oui.

const PUNCT = { "(": "LPAREN", ")": "RPAREN", "[": "LBRACK", "]": "RBRACK",
  "{": "LBRACE", "}": "RBRACE", ",": "COMMA", ":": "COLON", "=": "EQUALS" };
const NUMBER = /-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
const WORD = /[A-Za-z_][A-Za-z0-9_]*/y;

export function tokenize(src) {
  const tokens = [];
  let i = 0;
  const n = src.length;
  while (i < n) {
    const c = src[i];
    if (c === " " || c === "\t" || c === "\r") {
      i++;
    } else if (c === "\n") {
      tokens.push({ kind: "NEWLINE" });
      i++;
    } else if (c in PUNCT) {
      tokens.push({ kind: PUNCT[c] });
      i++;
    } else if (c === '"') {
      let j = i + 1;
      while (j < n && src[j] !== '"') j += src[j] === "\\" ? 2 : 1;
      const raw = j < n ? src.slice(i, j + 1) : src.slice(i) + '"';
      tokens.push({ kind: "STR", value: JSON.parse(raw) });
      i = j + 1;
    } else if ((NUMBER.lastIndex = i, NUMBER.test(src)) && NUMBER.lastIndex > i) {
      tokens.push({ kind: "NUM", value: Number(src.slice(i, NUMBER.lastIndex)) });
      i = NUMBER.lastIndex;
    } else if ((WORD.lastIndex = i, WORD.test(src)) && WORD.lastIndex > i) {
      const word = src.slice(i, WORD.lastIndex);
      if (word === "true" || word === "false") tokens.push({ kind: "BOOL", value: word === "true" });
      else if (word === "null") tokens.push({ kind: "NULL" });
      // PascalCase is a component name, anything else a reference
      else tokens.push({ kind: /^[A-Z]/.test(word) ? "TYPE" : "IDENT", value: word });
      i = WORD.lastIndex;
    } else {
      i++; // any other character is ignored, as in the reference lexer
    }
  }
  tokens.push({ kind: "EOF" });
  return tokens;
}

export function stripNoise(text) {
  if (text.includes("```")) {
    const blocks = [...text.matchAll(/```[^\n]*\n([\s\S]*?)(?:```|$)/g)].map((m) => m[1]);
    if (blocks.length) text = blocks.join("\n");
  }
  return text.split("\n").map((line) => {
    let inStr = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (inStr) {
        if (c === "\\") i++;
        else if (c === '"') inStr = false;
      } else if (c === '"') inStr = true;
      else if (c === "#" || line.startsWith("//", i)) return line.slice(0, i).trimEnd();
    }
    return line;
  }).join("\n");
}

// Complete statements end at a newline outside every bracket and string.
// The tail after the last such newline is held back as `pending`.
export function splitStatements(text) {
  const complete = [];
  let depth = 0, inStr = false, esc = false, start = 0;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (esc) esc = false;
    else if (inStr && c !== "\n") {
      if (c === "\\") esc = true;
      else if (c === '"') inStr = false;
    } else if (c === '"') inStr = true;
    else if ("([{".includes(c)) depth++;
    else if (")]}".includes(c)) depth = Math.max(0, depth - 1);
    else if (c === "\n") {
      if (inStr) { inStr = false; depth = 0; } // an unclosed string: the line is broken, end it here whatever the brackets say
      if (depth === 0) {
        const line = text.slice(start, i).trim();
        if (line) complete.push(line);
        start = i + 1;
      }
    }
  }
  return { complete, pending: text.slice(start) };
}

class Cursor {
  constructor(tokens) { this.tokens = tokens; this.pos = 0; }
  peek() { return this.tokens[this.pos]; }
  take(kind) {
    const tok = this.tokens[this.pos];
    if (kind && tok.kind !== kind) throw new Error(`expected ${kind}, got ${tok.kind}`);
    this.pos++;
    return tok;
  }
}

function parseExpression(cur) {
  const tok = cur.take();
  switch (tok.kind) {
    case "STR": return { k: "Str", v: tok.value };
    case "NUM": return { k: "Num", v: tok.value };
    case "BOOL": return { k: "Bool", v: tok.value };
    case "NULL": return { k: "Null" };
    case "IDENT": return { k: "Ref", n: tok.value };
    case "TYPE":
      if (cur.peek().kind !== "LPAREN") return { k: "Ref", n: tok.value };
      cur.take("LPAREN");
      return { k: "Comp", name: tok.value, args: parseSequence(cur, "RPAREN") };
    case "LBRACK": return { k: "Arr", els: parseSequence(cur, "RBRACK") };
    case "LBRACE": {
      const entries = [];
      while (cur.peek().kind !== "RBRACE" && cur.peek().kind !== "EOF") {
        const key = cur.take();
        if (!["IDENT", "TYPE", "STR"].includes(key.kind)) throw new Error(`object key expected, got ${key.kind}`);
        cur.take("COLON");
        entries.push([key.value, parseExpression(cur)]);
        if (cur.peek().kind === "COMMA") cur.take();
      }
      cur.take("RBRACE");
      return { k: "Obj", entries };
    }
    default: throw new Error(`unexpected token ${tok.kind}`);
  }
}

function parseSequence(cur, closer) {
  const items = [];
  for (;;) {
    while (cur.peek().kind === "NEWLINE") cur.take();
    if (cur.peek().kind === closer) { cur.take(); return items; }
    if (cur.peek().kind === "EOF") throw new Error(`unterminated sequence, expected ${closer}`);
    items.push(parseExpression(cur));
    while (cur.peek().kind === "NEWLINE") cur.take();
    if (cur.peek().kind === "COMMA") cur.take();
  }
}

export function parseStatement(line) {
  const cur = new Cursor(tokenize(line));
  const name = cur.take();
  if (name.kind !== "IDENT" && name.kind !== "TYPE") throw new Error(`statement must start with a name, got ${name.kind}`);
  cur.take("EQUALS");
  return [name.value, parseExpression(cur)];
}

export function parseProgram(text) {
  const program = { statements: new Map(), pending: "", errors: [] };
  const { complete, pending } = splitStatements(stripNoise(text));
  program.pending = pending;
  for (const line of complete) {
    try {
      const [name, expr] = parseStatement(line);
      program.statements.set(name, expr);
    } catch (err) {
      program.errors.push(`${JSON.stringify(line.slice(0, 40))}: ${err.message}`);
    }
  }
  return program;
}

// Component name -> ordered parameter names, from a JSON Schema `$defs`.
export function catalogFromSchema(schema) {
  const catalog = new Map();
  for (const [name, def] of Object.entries(schema.$defs)) catalog.set(name, Object.keys(def.properties ?? {}));
  return catalog;
}

// Follow references from `root` and build one tree of element nodes.
// A reference with no statement yet becomes {type: "placeholder"}.
export function resolve(program, catalog, root = "root") {
  const unresolved = new Set();
  const errors = [...program.errors];
  const visiting = new Set();
  const resolved = new Map(); // a statement referenced twice is resolved once

  function value(node) {
    switch (node.k) {
      case "Str": case "Num": case "Bool": return node.v;
      case "Null": return null;
      case "Arr": {
        const out = [];
        for (const e of node.els) {
          const v = value(e);
          if (v === null && (e.k === "Comp" || e.k === "Ref")) continue; // a dropped component leaves no hole
          out.push(v);
        }
        return out;
      }
      case "Obj": return Object.fromEntries(node.entries.map(([key, v]) => [key, value(v)]));
      case "Ref": return reference(node.n);
      case "Comp": return element(node);
      default: throw new Error(`unknown node kind ${node.k}`);
    }
  }

  function reference(name) {
    if (resolved.has(name)) return resolved.get(name);
    if (!program.statements.has(name) || visiting.has(name)) {
      unresolved.add(name);
      return { type: "placeholder", name };
    }
    visiting.add(name);
    let result;
    try { result = value(program.statements.get(name)); } finally { visiting.delete(name); }
    if (result && result.type === "element") result.statementId = name;
    resolved.set(name, result);
    return result;
  }

  function element(node) {
    const params = catalog.get(node.name);
    if (!params) { errors.push(`unknown component ${node.name}`); return null; }
    if (node.args.length > params.length) errors.push(`${node.name} takes ${params.length} arguments, got ${node.args.length}`);
    const props = {};
    node.args.slice(0, params.length).forEach((arg, i) => { props[params[i]] = value(arg); });
    return { type: "element", typeName: node.name, props };
  }

  const tree = program.statements.has(root) ? reference(root) : null;
  if (tree === null) unresolved.add(root);
  return {
    root: tree && tree.type === "element" ? tree : null,
    unresolved: [...unresolved].sort(),
    errors,
    statementCount: program.statements.size,
    incomplete: program.pending.trim().length > 0,
  };
}

export function parse(text, catalog) {
  return resolve(parseProgram(text), catalog);
}

// Feed chunks as they arrive; every push returns the tree so far.
export class StreamingParser {
  constructor(catalog) { this.catalog = catalog; this.buffer = ""; }
  push(chunk) { this.buffer += chunk; return parse(this.buffer, this.catalog); }
  finish() {
    if (this.buffer && !this.buffer.endsWith("\n")) this.buffer += "\n";
    return parse(this.buffer, this.catalog);
  }
}
