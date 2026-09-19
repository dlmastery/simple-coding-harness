"""Step 04 - find HtmlArtifact statements in an OpenUI Lang program.

The server never parses the program (the page does, with lang-core). The
demo and the tests still need to know what the model put into the artifact:
its title, its document, and how many tokens the document took. This module
reads the two string arguments of every `HtmlArtifact(...)` call with the
language's string rules: double quotes, backslash escapes, one line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CALL_RE = re.compile(r"\bHtmlArtifact\(")
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}


@dataclass
class Artifact:
    title: str
    document: str


def read_string(text: str, start: int) -> tuple[str, int]:
    """Decode the double-quoted string at `start`; return (value, index after the closing quote)."""
    assert text[start] == '"', f"expected a string at {start}"
    out = []
    i = start + 1
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out.append(ESCAPES.get(text[i + 1], text[i + 1]))
            i += 2
        elif ch == '"':
            return "".join(out), i + 1
        else:
            out.append(ch)
            i += 1
    raise ValueError("unterminated string")


def find_artifacts(program: str) -> list[Artifact]:
    """Every HtmlArtifact(title, document) in the program, in order."""
    found = []
    for match in CALL_RE.finditer(program):
        i = match.end()
        args = []
        while len(args) < 2:
            while program[i] in " ,":
                i += 1
            value, i = read_string(program, i)
            args.append(value)
        found.append(Artifact(*args))
    return found


def count_tokens(text: str) -> int:
    """o200k_base tokens with tiktoken; a character estimate when it is not installed or its vocabulary cannot be loaded (offline)."""
    try:
        import tiktoken

        return len(tiktoken.get_encoding("o200k_base").encode(text))
    except Exception:  # noqa: BLE001 - ImportError, or the one-time download failed
        return max(1, len(text) // 4)
