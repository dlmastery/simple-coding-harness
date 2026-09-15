"""Generative UI step 03 - the HtmlArtifact half, on the Python side.

The page does the rendering (web/render.mjs, web/sandbox.mjs). The demo and
the tests still need to know what the agent put into an artifact: which
statements are HtmlArtifact calls, their title and document, how many
tokens the document took, and the document the iframe will get, with the
Content Security Policy injected first in <head>. This module mirrors
web/sandbox.mjs so the CSP rule is tested in Python as well as in Node.
"""

import re
from dataclasses import dataclass

import openui_parse

# No network at all: no scripts, styles, fonts or images from a URL, no
# fetch, no WebSocket. Inline style and script stay allowed because that is
# what the instructions tell the agent to write. Images may be data: URIs.
CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:"
META = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
CSP_META_RE = re.compile(r"""<meta[^>]+http-equiv\s*=\s*["']?content-security-policy["']?[^>]*>""", re.IGNORECASE)
HEAD_RE = re.compile(r"<head[^>]*>", re.IGNORECASE)
MAX_DOCUMENT_CHARS = 200_000


@dataclass
class Artifact:
    name: str
    title: str
    document: str
    partial: bool = False


def find_artifacts(parser_or_program):
    """Every HtmlArtifact in a parsed program (or program text), in statement order.

    The statements' ASTs are walked, so an artifact inline in a list is found
    too. The line still streaming, if it is an artifact, comes last with
    partial=True, so a test can look at its document part-way.
    """
    parser = parser_or_program if isinstance(parser_or_program, openui_parse.Parser) else openui_parse.parse(parser_or_program)
    found = []

    def walk(name, expr):
        kind = expr[0]
        if kind == "call" and expr[1] == "HtmlArtifact":
            args = [a[1] if a[0] == "str" else "" for a in expr[2]] + ["", ""]
            found.append(Artifact(name, args[0], args[1]))
        if kind == "call":
            [walk(name, a) for a in expr[2]]
        elif kind == "list":
            [walk(name, a) for a in expr[1]]
        elif kind == "add":
            walk(name, expr[1]), walk(name, expr[2])

    for name, statement in parser.statements.items():
        walk(name, statement.expr)
    partial = parser.partial()
    if partial is not None and partial[1] == "HtmlArtifact":
        args = [str(a) for a in partial[2]] + ["", ""]
        found.append(Artifact(partial[0], args[0], args[1], partial=True))
    return found


def sandboxed(html):
    """The document with our CSP first in <head>; any CSP the model wrote is removed."""
    cleaned = CSP_META_RE.sub("", html)
    head = HEAD_RE.search(cleaned)
    if head:
        return cleaned[: head.end()] + META + cleaned[head.end():]
    return META + cleaned


def check_document(html):
    """Findings about the document. The CSP blocks each of them; this is for the reader."""
    problems = []
    if len(html) > MAX_DOCUMENT_CHARS:
        problems.append(f"document is {len(html)} characters, limit {MAX_DOCUMENT_CHARS}")
    for match in re.finditer(r"""\b(?:src|href)\s*=\s*["']?((?:https?:)?//[^"'\s>]+)""", html, re.IGNORECASE):
        problems.append(f"external resource: {match.group(1)}")
    if re.search(r"\bfetch\s*\(|XMLHttpRequest|WebSocket|navigator\.sendBeacon|\bimport\s*\(", html):
        problems.append("network call in script")
    if re.search(r"""<meta[^>]+http-equiv\s*=\s*["']?refresh""", html, re.IGNORECASE):
        problems.append("meta refresh")
    return problems


def count_tokens(text):
    """o200k_base tokens with tiktoken; a character estimate when it is not installed."""
    try:
        import tiktoken
    except ImportError:
        return max(1, len(text) // 4)
    return len(tiktoken.get_encoding("o200k_base").encode(text))
