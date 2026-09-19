// Step 02 - a tolerant parser for JSON that is still arriving.
// Mirrors partial_json.py: open strings, objects and arrays are closed; a key
// without a value, or a number or literal cut in the middle, is dropped.
// Containers the parser had to close are recorded in PARTIAL, so a renderer
// can tell "closed by the model" from "closed by us". Text that is not JSON
// at all (a code fence, prose) throws: the caller keeps its last render.

export const PARTIAL = new WeakSet();

export function isPartial(value) {
  return typeof value === "object" && value !== null && PARTIAL.has(value);
}

class Incomplete extends Error {}

const LITERALS = { true: true, false: false, null: null };
const ESCAPES = { n: "\n", t: "\t", r: "\r", b: "\b", f: "\f" };
const JSON_NUMBER = /^-?\d+(\.\d+)?([eE][-+]?\d+)?$/;
const HEX4 = /^[0-9a-fA-F]{4}$/;
export const MAX_DEPTH = 64; // deeper than any layout; a runaway stream cannot overflow the stack

class Parser {
  constructor(text) {
    this.text = text;
    this.i = 0;
    this.depth = 0;
  }
  atEnd() { return this.i >= this.text.length; }
  peek() { return this.text[this.i]; }
  skipWs() { while (!this.atEnd() && " \t\r\n".includes(this.peek())) this.i += 1; }

  value() {
    this.skipWs();
    if (this.atEnd()) throw new Incomplete();
    const c = this.peek();
    if (c === "{" || c === "[") {
      if (++this.depth > MAX_DEPTH) throw new Error(`nested deeper than ${MAX_DEPTH} at ${this.i}`);
      try { return c === "{" ? this.obj() : this.arr(); } finally { this.depth -= 1; }
    }
    if (c === '"') return this.string()[0];
    if ("tfn".includes(c)) return this.literal();
    if (c === "-" || (c >= "0" && c <= "9")) return this.number();
    throw new Error(`unexpected ${JSON.stringify(c)} at ${this.i}`);
  }

  obj() {
    this.i += 1; // {
    const out = {};
    PARTIAL.add(out);
    for (;;) {
      this.skipWs();
      if (this.atEnd()) return out;
      const c = this.peek();
      if (c === "}") { this.i += 1; PARTIAL.delete(out); return out; }
      if (c === ",") { this.i += 1; continue; }
      if (c !== '"') throw new Error(`expected a key at ${this.i}`);
      const [key, closed] = this.string();
      if (!closed) return out;
      this.skipWs();
      if (this.atEnd()) return out;
      if (this.peek() !== ":") throw new Error(`expected ':' at ${this.i}`);
      this.i += 1;
      try { out[key] = this.value(); } catch (e) { if (e instanceof Incomplete) return out; throw e; }
    }
  }

  arr() {
    this.i += 1; // [
    const out = [];
    PARTIAL.add(out);
    for (;;) {
      this.skipWs();
      if (this.atEnd()) return out;
      const c = this.peek();
      if (c === "]") { this.i += 1; PARTIAL.delete(out); return out; }
      if (c === ",") { this.i += 1; continue; }
      try { out.push(this.value()); } catch (e) { if (e instanceof Incomplete) return out; throw e; }
    }
  }

  string() {
    // [text, closed]. An open string returns what it has so far.
    this.i += 1;
    let parts = "";
    while (!this.atEnd()) {
      const c = this.peek();
      if (c === '"') { this.i += 1; return [parts, true]; }
      if (c === "\\") {
        if (this.i + 1 >= this.text.length) break;
        const e = this.text[this.i + 1];
        if (e === "u") {
          const hex = this.text.slice(this.i + 2, this.i + 6);
          if (hex.length < 4) break;
          if (!HEX4.test(hex)) throw new Error(`bad unicode escape at ${this.i}`);
          parts += String.fromCharCode(parseInt(hex, 16));
          this.i += 6;
          continue;
        }
        parts += ESCAPES[e] ?? e;
        this.i += 2;
        continue;
      }
      parts += c;
      this.i += 1;
    }
    this.i = this.text.length; // a cut escape is consumed too: the rest is coming
    return [parts, false];
  }

  number() {
    const match = /[-+0-9.eE]+/y;
    match.lastIndex = this.i;
    const raw = match.exec(this.text)[0];
    this.i += raw.length;
    if (/[-+.eE]$/.test(raw) && this.atEnd()) throw new Incomplete(); // "-", "1.", "2e": more digits are coming
    if (!JSON_NUMBER.test(raw)) throw new Error(`bad number at ${this.i}`);
    return Number(raw);
  }

  literal() {
    const rest = this.text.slice(this.i, this.i + 5);
    for (const [word, value] of Object.entries(LITERALS)) {
      if (rest.startsWith(word)) { this.i += word.length; return value; }
      if (word.startsWith(rest) && this.i + rest.length >= this.text.length) {
        this.i = this.text.length;
        throw new Incomplete(); // "tr", "nul": the rest is coming
      }
    }
    throw new Error(`bad literal at ${this.i}`);
  }
}

export function parsePartial(text) {
  // The value so far, or null when nothing parseable has arrived.
  const parser = new Parser(text);
  parser.skipWs();
  if (parser.atEnd()) return null;
  try { return parser.value(); } catch (e) { if (e instanceof Incomplete) return null; throw e; }
}
