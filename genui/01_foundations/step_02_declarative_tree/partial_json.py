"""Step 02 - a tolerant parser for JSON that is still arriving.

`parse_partial(text)` returns the value the text describes so far. Open
strings are closed, open objects and arrays are closed, a key without a
value is dropped, a number or literal cut in the middle is dropped. Every
container that had to be closed by the parser comes back as a PartialDict
or PartialList, so a renderer can tell "closed by the model" from "closed
by us". The same rules live in page/partial-json.mjs.
"""

import re

NUMBER = re.compile(r"[-+0-9.eE]+")
LITERALS = {"true": True, "false": False, "null": None}


class PartialDict(dict):
    """An object the text had not closed yet."""


class PartialList(list):
    """An array the text had not closed yet."""


def is_partial(value):
    return isinstance(value, (PartialDict, PartialList))


class Incomplete(Exception):
    """End of text inside a value with nothing to show for it yet."""


class Parser:
    def __init__(self, text):
        self.text = text
        self.i = 0

    def at_end(self):
        return self.i >= len(self.text)

    def peek(self):
        return self.text[self.i]

    def skip_ws(self):
        while not self.at_end() and self.peek() in " \t\r\n":
            self.i += 1

    def value(self):
        self.skip_ws()
        if self.at_end():
            raise Incomplete
        c = self.peek()
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c == '"':
            return self.string()[0]
        if c in "tfn":
            return self.literal()
        if c == "-" or c.isdigit():
            return self.number()
        raise ValueError(f"unexpected {c!r} at {self.i}")

    def obj(self):
        self.i += 1  # {
        out = PartialDict()
        while True:
            self.skip_ws()
            if self.at_end():
                return out
            c = self.peek()
            if c == "}":
                self.i += 1
                return dict(out)  # closed by the model: a plain dict
            if c == ",":
                self.i += 1
                continue
            if c != '"':
                raise ValueError(f"expected a key at {self.i}")
            key, closed = self.string()
            if not closed:
                return out  # the key itself was cut
            self.skip_ws()
            if self.at_end():
                return out  # key but no colon yet
            if self.peek() != ":":
                raise ValueError(f"expected ':' at {self.i}")
            self.i += 1
            try:
                out[key] = self.value()
            except Incomplete:
                return out  # key and colon, but no value yet

    def arr(self):
        self.i += 1  # [
        out = PartialList()
        while True:
            self.skip_ws()
            if self.at_end():
                return out
            c = self.peek()
            if c == "]":
                self.i += 1
                return list(out)
            if c == ",":
                self.i += 1
                continue
            try:
                out.append(self.value())
            except Incomplete:
                return out

    def string(self):
        """(text, closed). An open string returns what it has so far."""
        self.i += 1  # opening quote
        parts = []
        while not self.at_end():
            c = self.peek()
            if c == '"':
                self.i += 1
                return "".join(parts), True
            if c == "\\":
                if self.i + 1 >= len(self.text):
                    break  # a lone backslash at the end: wait for the rest
                e = self.text[self.i + 1]
                if e == "u":
                    hex_digits = self.text[self.i + 2 : self.i + 6]
                    if len(hex_digits) < 4:
                        break
                    parts.append(chr(int(hex_digits, 16)))
                    self.i += 6
                    continue
                parts.append({"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f"}.get(e, e))
                self.i += 2
                continue
            parts.append(c)
            self.i += 1
        self.i = len(self.text)  # a cut escape is consumed too: the rest is coming
        return "".join(parts), False

    def number(self):
        match = NUMBER.match(self.text, self.i)
        raw = match.group(0)
        self.i = match.end()
        if self.at_end() and raw[-1] in "-+.eE":
            raise Incomplete  # "-", "1.", "2e": more digits are coming
        return int(raw) if re.fullmatch(r"-?\d+", raw) else float(raw)

    def literal(self):
        rest = self.text[self.i : self.i + 5]
        for word, value in LITERALS.items():
            if rest.startswith(word):
                self.i += len(word)
                return value
            if word.startswith(rest) and self.i + len(rest) >= len(self.text):
                self.i = len(self.text)
                raise Incomplete  # "tr", "nul": the rest is coming
        raise ValueError(f"bad literal at {self.i}")


def parse_partial(text):
    """The value so far, or None when nothing parseable has arrived."""
    parser = Parser(text)
    parser.skip_ws()
    if parser.at_end():
        return None
    try:
        return parser.value()
    except Incomplete:
        return None
