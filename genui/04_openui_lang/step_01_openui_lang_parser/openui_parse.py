"""Step 01 - a small parser for the core of OpenUI Lang.

OpenUI Lang is a line-oriented language. Every line is one statement:

    identifier = Expression

An expression is a string, a number, true/false/null, a list, an object, a
reference to another statement, or a component call `Type(arg, arg, ...)`.
Component arguments are positional. The catalog (a JSON Schema document with
one entry per component under `$defs`) names them: the order of `properties`
is the order of the arguments.

References may point forward: `root = Stack([chart])` is valid before `chart`
is defined. While the program streams in, a reference with no definition yet
becomes a placeholder node, so the layout renders as a skeleton first.

The pipeline is: tokenize -> split into statements -> parse each expression
into a small AST -> resolve references into one tree of element nodes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Tokens ──────────────────────────────────────────────────────────────────

PUNCT = {"(": "LPAREN", ")": "RPAREN", "[": "LBRACK", "]": "RBRACK",
         "{": "LBRACE", "}": "RBRACE", ",": "COMMA", ":": "COLON", "=": "EQUALS"}
NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass
class Token:
    kind: str
    value: object = None


def tokenize(src: str) -> list[Token]:
    """Turn one statement (or a whole program) into a flat token list.

    Newlines are tokens because they end statements. Strings use double quotes
    with JSON escapes; an unclosed string at the end of the input is closed,
    which is what a streaming parser wants.
    """
    tokens: list[Token] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\r":
            i += 1
        elif c == "\n":
            tokens.append(Token("NEWLINE"))
            i += 1
        elif c in PUNCT:
            tokens.append(Token(PUNCT[c]))
            i += 1
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            raw = src[i:j + 1] if j < n else src[i:] + '"'
            tokens.append(Token("STR", json.loads(raw)))
            i = j + 1
        elif m := NUMBER.match(src, i):
            text = m.group()
            tokens.append(Token("NUM", float(text) if any(ch in text for ch in ".eE") else int(text)))
            i = m.end()
        elif m := WORD.match(src, i):
            word = m.group()
            if word in ("true", "false"):
                tokens.append(Token("BOOL", word == "true"))
            elif word == "null":
                tokens.append(Token("NULL"))
            else:
                # PascalCase is a component name, anything else a reference
                tokens.append(Token("TYPE" if word[0].isupper() else "IDENT", word))
            i = m.end()
        else:
            i += 1  # any other character is ignored, as in the reference lexer
    tokens.append(Token("EOF"))
    return tokens


# ── Statements ──────────────────────────────────────────────────────────────

def strip_noise(text: str) -> str:
    """Remove markdown fences and `//` or `#` comments outside strings."""
    if "```" in text:
        blocks = re.findall(r"```[^\n]*\n(.*?)(?:```|$)", text, flags=re.S)
        text = "\n".join(blocks) if blocks else text
    lines = []
    for line in text.split("\n"):  # not splitlines(): the last newline matters
        in_str = False
        i = 0
        while i < len(line):
            c = line[i]
            if in_str:
                if c == "\\":
                    i += 1
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "#" or line.startswith("//", i):
                line = line[:i].rstrip()
                break
            i += 1
        lines.append(line)
    return "\n".join(lines)


def split_statements(text: str) -> tuple[list[str], str]:
    """Cut the text into complete statements and the incomplete tail.

    A statement ends at a newline that is outside every bracket and string.
    Text after the last such newline is held back as `pending`: it is a line
    the model has not finished yet.
    """
    complete: list[str] = []
    depth, in_str, esc = 0, False, False
    start = 0
    for i, c in enumerate(text):
        if esc:
            esc = False
        elif in_str:
            if c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif c == "\n" and depth == 0:
            line = text[start:i].strip()
            if line:
                complete.append(line)
            start = i + 1
    return complete, text[start:]


# ── Expressions ─────────────────────────────────────────────────────────────
# AST nodes are plain dicts: {"k": "Str", "v": ...}, {"k": "Ref", "n": ...},
# {"k": "Comp", "name": ..., "args": [...]}, {"k": "Arr", "els": [...]}, ...


class ParseError(ValueError):
    pass


class _Cursor:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def take(self, kind: str | None = None) -> Token:
        tok = self.tokens[self.pos]
        if kind and tok.kind != kind:
            raise ParseError(f"expected {kind}, got {tok.kind}")
        self.pos += 1
        return tok


def parse_expression(cur: _Cursor) -> dict:
    tok = cur.take()
    if tok.kind == "STR":
        return {"k": "Str", "v": tok.value}
    if tok.kind == "NUM":
        return {"k": "Num", "v": tok.value}
    if tok.kind == "BOOL":
        return {"k": "Bool", "v": tok.value}
    if tok.kind == "NULL":
        return {"k": "Null"}
    if tok.kind == "IDENT":
        return {"k": "Ref", "n": tok.value}
    if tok.kind == "TYPE":
        if cur.peek().kind != "LPAREN":
            return {"k": "Ref", "n": tok.value}
        cur.take("LPAREN")
        return {"k": "Comp", "name": tok.value, "args": parse_sequence(cur, "RPAREN")}
    if tok.kind == "LBRACK":
        return {"k": "Arr", "els": parse_sequence(cur, "RBRACK")}
    if tok.kind == "LBRACE":
        entries = []
        while cur.peek().kind not in ("RBRACE", "EOF"):
            key = cur.take()
            if key.kind not in ("IDENT", "TYPE", "STR"):
                raise ParseError(f"object key expected, got {key.kind}")
            cur.take("COLON")
            entries.append((key.value, parse_expression(cur)))
            if cur.peek().kind == "COMMA":
                cur.take()
        cur.take("RBRACE")
        return {"k": "Obj", "entries": entries}
    raise ParseError(f"unexpected token {tok.kind}")


def parse_sequence(cur: _Cursor, closer: str) -> list[dict]:
    """Comma-separated expressions up to `closer`. Newlines inside are skipped."""
    items = []
    while True:
        while cur.peek().kind == "NEWLINE":
            cur.take()
        if cur.peek().kind == closer:
            cur.take()
            return items
        if cur.peek().kind == "EOF":
            raise ParseError(f"unterminated sequence, expected {closer}")
        items.append(parse_expression(cur))
        while cur.peek().kind == "NEWLINE":
            cur.take()
        if cur.peek().kind == "COMMA":
            cur.take()


def parse_statement(line: str) -> tuple[str, dict]:
    """`name = Expression` -> (name, ast)."""
    cur = _Cursor(tokenize(line))
    name = cur.take()
    if name.kind not in ("IDENT", "TYPE"):
        raise ParseError(f"statement must start with a name, got {name.kind}")
    cur.take("EQUALS")
    expr = parse_expression(cur)
    return name.value, expr


@dataclass
class Program:
    """The statements seen so far, in order, plus the unfinished tail."""

    statements: dict[str, dict] = field(default_factory=dict)
    pending: str = ""
    errors: list[str] = field(default_factory=list)


def parse_program(text: str) -> Program:
    program = Program()
    complete, program.pending = split_statements(strip_noise(text))
    for line in complete:
        try:
            name, expr = parse_statement(line)
            program.statements[name] = expr
        except (ParseError, json.JSONDecodeError) as err:
            program.errors.append(f"{line[:40]!r}: {err}")
    return program


# ── Resolution ──────────────────────────────────────────────────────────────


def load_catalog(path: str | Path) -> dict[str, list[str]]:
    """Component name -> ordered parameter names, from a JSON Schema `$defs`."""
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    return {name: list(d.get("properties", {})) for name, d in schema["$defs"].items()}


@dataclass
class ParseResult:
    root: dict | None
    unresolved: list[str]
    errors: list[str]
    statement_count: int
    incomplete: bool


def resolve(program: Program, catalog: dict[str, list[str]], root: str = "root") -> ParseResult:
    """Follow references from `root` and build one tree of element nodes.

    A reference with no statement yet becomes {"type": "placeholder"}; the
    renderer draws it as a skeleton. Positional arguments become named props
    using the catalog order.
    """
    unresolved: list[str] = []
    errors: list[str] = list(program.errors)
    visiting: set[str] = set()

    def value(node: dict) -> object:
        k = node["k"]
        if k in ("Str", "Num", "Bool"):
            return node["v"]
        if k == "Null":
            return None
        if k == "Arr":
            items = [(e, value(e)) for e in node["els"]]
            # a dropped component (unknown name) leaves no hole in a list
            return [v for e, v in items if not (v is None and e["k"] in ("Comp", "Ref"))]
        if k == "Obj":
            return {key: value(v) for key, v in node["entries"]}
        if k == "Ref":
            return reference(node["n"])
        if k == "Comp":
            return element(node)
        raise ParseError(f"unknown node kind {k}")

    def reference(name: str) -> object:
        if name not in program.statements or name in visiting:
            unresolved.append(name)
            return {"type": "placeholder", "name": name}
        visiting.add(name)
        try:
            result = value(program.statements[name])
        finally:
            visiting.discard(name)
        if isinstance(result, dict) and result.get("type") == "element":
            result["statementId"] = name
        return result

    def element(node: dict) -> object:
        name = node["name"]
        if name not in catalog:
            errors.append(f"unknown component {name}")
            return None
        params = catalog[name]
        if len(node["args"]) > len(params):
            errors.append(f"{name} takes {len(params)} arguments, got {len(node['args'])}")
        props = {param: value(arg) for param, arg in zip(params, node["args"])}
        return {"type": "element", "typeName": name, "props": props}

    tree = reference(root) if root in program.statements else None
    if tree is None:
        unresolved.append(root)
    return ParseResult(
        root=tree if isinstance(tree, dict) and tree.get("type") == "element" else None,
        unresolved=sorted(set(unresolved)),
        errors=errors,
        statement_count=len(program.statements),
        incomplete=bool(program.pending.strip()),
    )


def parse(text: str, catalog: dict[str, list[str]]) -> ParseResult:
    """One-shot: text in, tree out."""
    return resolve(parse_program(text), catalog)


class StreamingParser:
    """Feed chunks as they arrive; every push returns the tree so far."""

    def __init__(self, catalog: dict[str, list[str]]):
        self.catalog = catalog
        self.buffer = ""

    def push(self, chunk: str) -> ParseResult:
        self.buffer += chunk
        return parse(self.buffer, self.catalog)

    def finish(self) -> ParseResult:
        """The stream ended: the pending tail is a whole statement now."""
        if self.buffer and not self.buffer.endswith("\n"):
            self.buffer += "\n"
        return parse(self.buffer, self.catalog)


if __name__ == "__main__":
    import sys

    here = Path(__file__).parent
    source = Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else (here / "program.oui").read_text(encoding="utf-8")
    result = parse(source, load_catalog(here / "catalog.json"))
    print(json.dumps(result.root, indent=1))
    print("unresolved:", result.unresolved, "errors:", result.errors)
