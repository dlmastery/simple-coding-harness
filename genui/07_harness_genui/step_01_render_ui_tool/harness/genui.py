"""Generative UI step 01 - the catalog behind the render_ui tool.

A spec is a json-render element map: {"root": id, "elements": {id: {"type",
"props", "children"}}}. Every element type comes from CATALOG, so the model
can only place components that already exist. validate() returns a list of
problems; an empty list means the spec can be drawn on any surface.
"""

CATALOG = {
    "Card": {
        "description": "A titled box around other elements.",
        "props": {"title": "string"},
        "required": [],
        "children": True,
    },
    "Stack": {
        "description": "Lays its children out in a row or a column.",
        "props": {"direction": "string"},
        "required": ["direction"],
        "children": True,
    },
    "Text": {
        "description": "A paragraph of plain text.",
        "props": {"text": "string"},
        "required": ["text"],
        "children": False,
    },
    "Metric": {
        "description": "One number with a label and an optional delta such as '+12%'.",
        "props": {"label": "string", "value": "string", "delta": "string"},
        "required": ["label", "value"],
        "children": False,
    },
    "Table": {
        "description": "Column headers and rows of cells.",
        "props": {"columns": "list", "rows": "list"},
        "required": ["columns", "rows"],
        "children": False,
    },
    "Chart": {
        "description": "A bar or line chart of one series.",
        "props": {"kind": "string", "labels": "list", "values": "list", "title": "string"},
        "required": ["kind", "labels", "values"],
        "children": False,
    },
}

DIRECTIONS = {"row", "column"}
CHART_KINDS = {"bar", "line"}
TYPES = {"string": str, "list": list}


def validate(spec):
    """Every problem in a spec, as plain sentences. An empty list means valid.

    The spec is whatever the model put in the tool call, so every level is
    checked for its shape before it is read: a wrong shape is a sentence in
    the list, never an exception out of the validator.
    """
    problems = []
    if not isinstance(spec, dict) or "elements" not in spec or "root" not in spec:
        return ["spec must be an object with 'root' and 'elements'"]
    elements = spec["elements"]
    if not isinstance(elements, dict) or not elements:
        return ["'elements' must be a non-empty object keyed by id"]
    if not isinstance(spec["root"], str) or spec["root"] not in elements:
        problems.append(f"root {spec['root']!r} is not an element id")

    for eid, element in elements.items():
        if not isinstance(element, dict) or not isinstance(element.get("type"), str):
            problems.append(f"{eid}: an element needs a 'type'")
            continue
        entry = CATALOG.get(element["type"])
        if entry is None:
            problems.append(f"{eid}: unknown type '{element['type']}' (catalog: {', '.join(CATALOG)})")
            continue
        props = element.get("props") or {}
        if not isinstance(props, dict):
            problems.append(f"{eid}: props must be an object")
            continue
        for name in entry["required"]:
            if name not in props:
                problems.append(f"{eid}: {element['type']} needs prop '{name}'")
        for name, value in props.items():
            expected = entry["props"].get(name)
            if expected is None:
                problems.append(f"{eid}: {element['type']} has no prop '{name}'")
            elif not isinstance(value, TYPES[expected]):
                problems.append(f"{eid}: prop '{name}' must be a {expected}")
        children = element.get("children") or []
        if not isinstance(children, list) or not all(isinstance(c, str) for c in children):
            problems.append(f"{eid}: children must be a list of element ids")
            children = []
        if children and not entry["children"]:
            problems.append(f"{eid}: {element['type']} takes no children")
        for child in children:
            if child not in elements:
                problems.append(f"{eid}: child '{child}' is not an element id")
        if element["type"] == "Stack" and props.get("direction") not in DIRECTIONS:
            problems.append(f"{eid}: direction must be row or column")
        if element["type"] == "Chart":
            if props.get("kind") not in CHART_KINDS:
                problems.append(f"{eid}: chart kind must be bar or line")
            if len(props.get("labels") or []) != len(props.get("values") or []):
                problems.append(f"{eid}: labels and values must have the same length")
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in props.get("values") or []):
                problems.append(f"{eid}: values must be numbers")
        if element["type"] == "Table" and not all(isinstance(row, list) for row in props.get("rows") or []):
            problems.append(f"{eid}: every row must be a list of cells")

    if not problems:
        problems += cycles(spec)
    return problems


def cycles(spec):
    """A tree has no element that is its own descendant."""
    seen = set()

    def walk(eid, path):
        if eid in path:
            return [f"{eid}: element contains itself"]
        seen.add(eid)
        found = []
        for child in spec["elements"][eid].get("children") or []:
            found += walk(child, path | {eid})
        return found

    return walk(spec["root"], frozenset())


def catalog_prompt():
    """The catalog as text for the system prompt: one line per component."""
    lines = []
    for name, entry in CATALOG.items():
        props = ", ".join(f"{p}: {t}" for p, t in entry["props"].items())
        kids = " Takes children." if entry["children"] else ""
        lines.append(f"- {name}({props}): {entry['description']}{kids}")
    return "\n".join(lines)


def walk(spec, eid=None, depth=0):
    """Yield (depth, id, element) in render order, root first."""
    eid = spec["root"] if eid is None else eid
    element = spec["elements"][eid]
    yield depth, eid, element
    for child in element.get("children") or []:
        yield from walk(spec, child, depth + 1)


RENDER_UI_SCHEMA = {
    "type": "function",
    "function": {
        "name": "render_ui",
        "description": (
            "Show the user an interface instead of prose: a dashboard, a table, a "
            "chart, a set of metrics. Pass a json-render element map. Every "
            "element type must come from the catalog in the system prompt. "
            "Use it when a picture or a table says it better than text."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "object",
                    "description": (
                        "{root: id, elements: {id: {type, props, children}}}. children is a "
                        "list of element ids. ids are short words such as 'sales' or 'kpis'."
                    ),
                }
            },
            "required": ["spec"],
        },
    },
}
