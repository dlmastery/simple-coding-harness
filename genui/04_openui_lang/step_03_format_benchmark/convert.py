"""Step 03 - project one OpenUI Lang tree into the three JSON-shaped formats.

The report's benchmark generated OpenUI Lang once per scenario and then
projected the parsed tree into Thesys C1 JSON, json-render's element map
(streamed as RFC 6902 patches) and YAML, so that all four texts describe
exactly the same UI. This file is a Python port of those converters
(`benchmarks/*-converter.ts` in the OpenUI repository):

    to_c1(tree)        nested component tree, {"component", "props"} per node
    to_spec(tree)      json-render spec: {"root": id, "elements": {id: ...}}
    to_jsonl(spec)     one JSON Patch "add" per line, the json-render stream
    to_yaml(spec)      the spec as YAML, empty children removed

The tree comes from openui_parse.py (element nodes with named props). Two
details matter for the token counts: numbers are printed the way JavaScript
prints them (5.0 is 5), and the YAML emitter follows the `yaml` npm package's
defaults (80-column folding, quoting rules), because the report's numbers
were measured on that package's output.
"""

from __future__ import annotations

import json
import re


def is_element(value) -> bool:
    return isinstance(value, dict) and value.get("type") == "element" and isinstance(value.get("typeName"), str)


def js_numbers(value):
    """Floats with no fraction become ints, as JSON.stringify would print them."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [js_numbers(v) for v in value]
    if isinstance(value, dict):
        return {k: js_numbers(v) for k, v in value.items()}
    return value


# ── Thesys C1 JSON ──────────────────────────────────────────────────────────

def to_c1(tree: dict) -> dict:
    """The legacy nested shape: every node is {"component": name, "props": {...}}."""
    def convert(value):
        if isinstance(value, list):
            return [convert(v) for v in value]
        if is_element(value):
            return {"component": value["typeName"], "props": convert(value["props"])}
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items() if k != "__typename"}
        return value
    return {"component": convert(js_numbers(tree)), "error": None}


def c1_text(tree: dict) -> str:
    """JSON.stringify(c1, null, 2), which is what the report measured."""
    return json.dumps(to_c1(tree), indent=2, ensure_ascii=False)


# ── json-render element map ─────────────────────────────────────────────────

def to_spec(tree: dict) -> dict:
    """Flatten the tree into {"root": id, "elements": {id: {type, props, children}}}.

    Ids are numbered in pre-order (`stack-1` is the root) but inserted in
    post-order, so a child's entry always precedes its parent's: streamed
    as patches, every element arrives after the elements it references.
    Any prop that holds element nodes becomes part of `children`.
    """
    elements: dict[str, dict] = {}
    counter = 0

    def process(node):
        nonlocal counter
        if not is_element(node):
            return None
        counter += 1
        element_id = f"{node['typeName'].lower()}-{counter}"
        props, children = {}, []
        for key, value in node["props"].items():
            if isinstance(value, list):
                if any(is_element(v) for v in value):
                    children.extend(cid for cid in (process(v) for v in value) if cid)
                else:
                    props[key] = value
                continue
            child_id = process(value)
            if child_id:
                children.append(child_id)
            else:
                props[key] = value
        elements[element_id] = {"type": node["typeName"], "props": props, "children": children}
        return element_id

    root = process(js_numbers(tree))
    if root is None:
        raise ValueError("the tree has no root element")
    return {"root": root, "elements": elements}


def compact(value) -> str:
    """JSON.stringify(value): no spaces, unicode kept."""
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def to_jsonl(spec: dict) -> str:
    """The json-render stream: one RFC 6902 `add` per line, root first."""
    lines = [compact({"op": "add", "path": "/root", "value": spec["root"]})]
    for element_id, element in spec["elements"].items():
        lines.append(compact({"op": "add", "path": f"/elements/{element_id}", "value": element}))
    return "\n".join(lines)


# ── YAML, the way the `yaml` npm package prints it ──────────────────────────

LINE_WIDTH = 80
MIN_CONTENT_WIDTH = 20
NOT_PLAIN = re.compile(r"^[\n\t ,\[\]{}#&*!|>'\"%@`]|^[?-]$|^[?-][ \t]|[\n:][ \t]|[ \t]\n|[\n\t ]#|[\n\t :]$")
LOOKS_TYPED = re.compile(r"^(?:[-+]?[0-9]+|[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?|0x[0-9a-fA-F]+|0o[0-7]+|[Tt]rue|TRUE|[Ff]alse|FALSE|~|[Nn]ull|NULL|\.inf|-\.inf|\.nan)?$")


def fold(text: str, indent: str, indent_at_start: int | None = None, block: bool = False) -> str:
    """Break a scalar at spaces so lines stay under 80 columns (foldFlowLines)."""
    end_step = max(1 + MIN_CONTENT_WIDTH, 1 + LINE_WIDTH - len(indent))
    if len(text) <= end_step:
        return text
    folds: list[int] = []
    end = LINE_WIDTH - len(indent)
    if indent_at_start is not None:
        if indent_at_start > LINE_WIDTH - max(2, MIN_CONTENT_WIDTH):
            folds.append(0)
        else:
            end = LINE_WIDTH - indent_at_start
    split = None
    prev = None
    i = -1
    if block:
        i = more_indented(text, i, len(indent))
        if i != -1:
            end = i + end_step
    while True:
        i += 1
        if i >= len(text):
            break
        ch = text[i]
        if ch == "\n":
            if block:
                i = more_indented(text, i, len(indent))
            end = i + len(indent) + end_step
            split = None
        else:
            if ch == " " and prev and prev not in " \n\t":
                nxt = text[i + 1] if i + 1 < len(text) else ""
                if nxt and nxt not in " \n\t":
                    split = i
            if i >= end and split:
                folds.append(split)
                end = split + end_step
                split = None
        prev = ch
    if not folds:
        return text
    out = text[:folds[0]]
    for n, at in enumerate(folds):
        stop = folds[n + 1] if n + 1 < len(folds) else len(text)
        out = f"\n{indent}{text[:stop]}" if at == 0 else out + f"\n{indent}{text[at + 1:stop]}"
    return out


def more_indented(text: str, i: int, indent: int) -> int:
    """Skip lines that are indented deeper than the block (they are never folded)."""
    end, start = i, i + 1
    ch = text[start] if start < len(text) else ""
    while ch in (" ", "\t") and ch:
        if i < start + indent:
            i += 1
            ch = text[i] if i < len(text) else ""
        else:
            while True:
                i += 1
                ch = text[i] if i < len(text) else ""
                if not ch or ch == "\n":
                    break
            end, start = i, i + 1
            ch = text[start] if start < len(text) else ""
    return end


def quoted(value: str, indent: str) -> str:
    if '"' in value and "'" not in value:
        return "'" + value.replace("'", "''") + "'"
    return json.dumps(value, ensure_ascii=False)


def block_scalar(value: str, indent: str) -> str:
    """`|-` literal, or `>-` folded when a line is longer than fits."""
    stripped = value.rstrip("\n")
    chomp = "-" if not value.endswith("\n") else ("" if value.endswith("\n") and not value.endswith("\n\n") else "+")
    literal = not any(len(line) > LINE_WIDTH - len(indent) for line in stripped.split("\n"))
    if not literal:
        folded = re.sub(r"\n+", lambda m: "\n" + m.group(0), stripped)
        folded = re.sub(r"(?:^|\n)([\t ].*)(?:([\n\t ]*)\n(?![\n\t ]))?", r"\1\2", folded)
        folded = re.sub(r"\n+", lambda m: m.group(0) + indent, folded)
        return f">{chomp}\n{indent}{fold(folded, indent, len(indent), block=True)}"
    return f"|{chomp}\n{indent}" + stripped.replace("\n", "\n" + indent)


def scalar(value, indent: str, indent_at_start: int | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(js_numbers(value))
    if NOT_PLAIN.search(value):
        return quoted(value, indent) if "\n" not in value else block_scalar(value, indent)
    if "\n" in value:
        return block_scalar(value, indent)
    if LOOKS_TYPED.match(value):
        return quoted(value, indent)
    return fold(value, indent, indent_at_start)


def to_yaml(spec: dict) -> str:
    """The spec as YAML, `children: []` removed as adding no information."""
    trimmed = {"root": spec["root"], "elements": {}}
    for element_id, element in spec["elements"].items():
        entry = {"type": element["type"], "props": element["props"]}
        if element["children"]:
            entry["children"] = element["children"]
        trimmed["elements"][element_id] = entry
    return emit(js_numbers(trimmed), "")


def emit(value, indent: str) -> str:
    """A block mapping or sequence at `indent`; scalars inline."""
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            head = f"{key}:"
            if isinstance(item, (dict, list)) and item:
                lines.append(head + "\n" + indent + "  " + emit(item, indent + "  "))
            elif isinstance(item, (dict, list)):
                lines.append(head + " " + ("{}" if isinstance(item, dict) else "[]"))
            else:
                lines.append(head + " " + scalar(item, indent + "  ", len(head) + 1))
        return ("\n" + indent).join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)) and item:
                lines.append("- " + emit(item, indent + "  "))
            elif isinstance(item, (dict, list)):
                lines.append("- " + ("{}" if isinstance(item, dict) else "[]"))
            else:
                lines.append("- " + scalar(item, indent + "  ", None))
        return ("\n" + indent).join(lines)
    return scalar(value, indent, None)
