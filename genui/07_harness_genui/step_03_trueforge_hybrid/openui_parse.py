"""Generative UI step 03 - the step 02 OpenUI Lang parser, plus partial().

The language is a list of statements, one per line:

    root = Stack([header, kpis], "column", "l")
    header = TextContent("Lemonade stand", "large-heavy")
    kpis = Stack([Card([TextContent("" + total, "large-heavy")])], "row")
    total = 370

Values are strings, numbers, true/false/null, lists, inline component calls,
`+` (string concatenation), and identifiers that refer to other statements.
A reference may point forward to a statement that has not arrived yet; the
tree marks it as pending and fills it in when the line lands. That is what
makes the format stream: a page can draw the skeleton from the first line.

Parser.feed(text) takes any chunk of text; complete statements are parsed at
once, an unfinished line (open bracket, open string, no newline) is held
back. Parser.tree() resolves from "root" into plain Python: components are
{"type": name, "args": [...]}, pending references are {"type": "Pending",
"ref": id}.

New in step 03: Parser.partial() reads the held-back line leniently, so a
long statement such as `art = HtmlArtifact("Title", "<html>...` appears in
the tree as {"type": "HtmlArtifact", "args": [...], "partial": True} while
its document string is still arriving. tree() uses it for a reference whose
statement is the line in progress; everything else is step 02's parser.
"""

import re

TOKEN = re.compile(
    r'\s*(?:(?P<str>"(?:[^"\\]|\\.)*")|(?P<num>-?\d+(?:\.\d+)?)|(?P<id>[A-Za-z_]\w*)|(?P<punct>[()\[\],+=]))'
)
STRING_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
PARTIAL_HEAD = re.compile(r"\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\((.*)$", re.DOTALL)
SCALAR = re.compile(r"-?\d+(?:\.\d+)?|[A-Za-z_]\w*")


class ParseError(ValueError):
    pass


def read_string(text, start):
    """Decode the double-quoted string at `start`: (value, index after it, closed?).

    An unterminated string decodes as far as the text goes, a trailing lone
    backslash dropped, so a streaming document can be shown part-way.
    """
    out, i = [], start + 1
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            if i + 1 >= len(text):
                break
            out.append(STRING_ESCAPES.get(text[i + 1], text[i + 1]))
            i += 2
        elif ch == '"':
            return "".join(out), i + 1, True
        else:
            out.append(ch)
            i += 1
    return "".join(out), len(text), False


def tokenize(line):
    """A statement line to a list of (kind, value) tokens; kinds: str num id punct."""
    tokens, pos = [], 0
    line = line.strip()
    while pos < len(line):
        m = TOKEN.match(line, pos)
        if not m or m.end() == pos:
            raise ParseError(f"unexpected text at {pos}: {line[pos:pos + 12]!r}")
        pos = m.end()
        kind = m.lastgroup
        raw = m.group(kind)
        if kind == "str":
            raw = re.sub(r"\\(.)", lambda e: STRING_ESCAPES.get(e.group(1), e.group(1)), raw[1:-1])
        elif kind == "num":
            raw = float(raw) if "." in raw else int(raw)
        tokens.append((kind, raw))
    return tokens


def complete(line):
    """True when brackets balance and no string is open: the line can be parsed."""
    depth, in_str, i = 0, False, 0
    while i < len(line):
        ch = line[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        i += 1
    return depth <= 0 and not in_str


class Statement:
    """`name = expr`, with the expression kept as a small AST."""

    def __init__(self, name, expr):
        self.name = name
        self.expr = expr


def parse_statement(line):
    """One line to a Statement. Blank lines and # comments return None."""
    if not line.strip() or line.lstrip().startswith("#"):
        return None
    tokens = tokenize(line)
    if len(tokens) < 3 or tokens[0][0] != "id" or tokens[1] != ("punct", "="):
        raise ParseError(f"expected `name = value`: {line.strip()!r}")
    expr, end = parse_expr(tokens, 2)
    if end != len(tokens):
        raise ParseError(f"trailing tokens in {line.strip()!r}")
    return Statement(tokens[0][1], expr)


def parse_expr(tokens, i):
    """An expression: a value, or values joined by +. Returns (ast, next index)."""
    left, i = parse_value(tokens, i)
    while i < len(tokens) and tokens[i] == ("punct", "+"):
        right, i = parse_value(tokens, i + 1)
        left = ("add", left, right)
    return left, i


def parse_value(tokens, i):
    if i >= len(tokens):
        raise ParseError("unexpected end of statement")
    kind, value = tokens[i]
    if kind == "str":
        return ("str", value), i + 1
    if kind == "num":
        return ("num", value), i + 1
    if kind == "id":
        if value in ("true", "false"):
            return ("bool", value == "true"), i + 1
        if value == "null":
            return ("null", None), i + 1
        if i + 1 < len(tokens) and tokens[i + 1] == ("punct", "("):
            args, i = parse_list(tokens, i + 2, ")")
            return ("call", value, args), i
        return ("ref", value), i + 1
    if (kind, value) == ("punct", "["):
        items, i = parse_list(tokens, i + 1, "]")
        return ("list", items), i
    raise ParseError(f"unexpected token {value!r}")


def parse_list(tokens, i, closer):
    """Comma-separated expressions up to `closer`. Returns (items, next index)."""
    items = []
    while True:
        if i >= len(tokens):
            raise ParseError(f"missing {closer}")
        if tokens[i] == ("punct", closer):
            return items, i + 1
        item, i = parse_expr(tokens, i)
        items.append(item)
        if i < len(tokens) and tokens[i] == ("punct", ","):
            i += 1


class Parser:
    """Feed text in any pieces; read the resolved tree at any time."""

    def __init__(self):
        self.statements = {}   # name -> Statement, in arrival order
        self.buffer = ""       # text not yet ending in a newline, or unbalanced
        self.errors = []

    def feed(self, text):
        """Add a chunk. Every complete statement it finishes is parsed now."""
        self.buffer += text
        while True:
            # the first newline at which the text before it is balanced ends a statement
            start, cut = 0, None
            while cut is None:
                nl = self.buffer.find("\n", start)
                if nl == -1:
                    return  # the rest is an unfinished line: hold it back
                if complete(self.buffer[:nl]):
                    cut = nl
                start = nl + 1
            line, self.buffer = self.buffer[:cut], self.buffer[cut + 1:]
            self.add_line(line.replace("\n", " "))

    def partial(self):
        """The line in progress, read leniently: (name, type, args) or None.

        Only the shape `name = Component(scalar, scalar, ...)` is read, which
        is what a streaming HtmlArtifact looks like. Closed strings are
        decoded; the open one at the end is decoded as far as it goes.
        """
        head = PARTIAL_HEAD.match(self.buffer)
        if not head:
            return None
        name, kind, rest = head.group(1), head.group(2), head.group(3)
        args, i = [], 0
        while i < len(rest):
            ch = rest[i]
            if ch in " ,\n":
                i += 1
            elif ch == '"':
                value, i, closed = read_string(rest, i)
                args.append(value)
                if not closed:
                    break
            else:
                m = SCALAR.match(rest, i)
                if not m:
                    break
                raw = m.group(0)
                args.append(float(raw) if "." in raw else int(raw) if raw.lstrip("-").isdigit() else raw)
                i = m.end()
        return name, kind, args

    def close(self):
        """No more text is coming: parse whatever is still buffered."""
        if self.buffer.strip():
            self.add_line(self.buffer)
        self.buffer = ""

    def add_line(self, line):
        try:
            statement = parse_statement(line)
        except ParseError as e:
            self.errors.append(str(e))
            return
        if statement is not None:
            self.statements[statement.name] = statement

    # ----------------------------------------------------------- resolve

    def tree(self, name="root"):
        """The value behind `name`, with references followed and components as dicts."""
        if name not in self.statements:
            return {"type": "Pending", "ref": name}
        return self.resolve(self.statements[name].expr, {name})

    def resolve(self, expr, path):
        kind = expr[0]
        if kind in ("str", "num", "bool", "null"):
            return expr[1]
        if kind == "list":
            return [self.resolve(item, path) for item in expr[1]]
        if kind == "add":
            left, right = self.resolve(expr[1], path), self.resolve(expr[2], path)
            if isinstance(left, str) or isinstance(right, str):
                return f"{left}{right}"
            return left + right
        if kind == "call":
            return {"type": expr[1], "args": [self.resolve(a, path) for a in expr[2]]}
        name = expr[1]
        if name in path:
            return {"type": "Cycle", "ref": name}
        if name not in self.statements:
            partial = self.partial()  # the line in progress, if it is this statement
            if partial is not None and partial[0] == name:
                return {"type": partial[1], "args": partial[2], "partial": True}
            return {"type": "Pending", "ref": name}
        return self.resolve(self.statements[name].expr, path | {name})

    def pending(self):
        """Every referenced name that has no statement yet."""
        missing = []

        def walk(expr):
            kind = expr[0]
            if kind == "ref" and expr[1] not in self.statements and expr[1] not in missing:
                missing.append(expr[1])
            elif kind == "list":
                [walk(e) for e in expr[1]]
            elif kind == "call":
                [walk(e) for e in expr[2]]
            elif kind == "add":
                walk(expr[1]), walk(expr[2])

        for statement in self.statements.values():
            walk(statement.expr)
        return missing


def parse(program):
    """One-shot: the whole program to a Parser with every line consumed."""
    parser = Parser()
    parser.feed(program if program.endswith("\n") else program + "\n")
    parser.close()
    return parser


def outline(node, depth=0):
    """A component tree as indented lines, for the terminal."""
    pad = "  " * depth
    if isinstance(node, dict):
        if node["type"] in ("Pending", "Cycle"):
            return [f"{pad}({node['type'].lower()}: {node['ref']})"]
        scalars = [repr(a) if isinstance(a, str) else str(a) for a in node["args"] if not isinstance(a, (dict, list))]
        lines = [f"{pad}{node['type']}({', '.join(scalars)})"]
        for arg in node["args"]:
            if isinstance(arg, (dict, list)):
                lines += outline(arg, depth + 1)
        return lines
    if isinstance(node, list):
        if all(not isinstance(item, (dict, list)) for item in node):
            return [f"{pad}{node}"]
        return [line for item in node for line in outline(item, depth)]
    return [f"{pad}{node!r}"]
