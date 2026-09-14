"""Step 04 - the component catalog, in two shapes, with one escape hatch.

Static mode (step 01) keeps its three tools. Declarative mode has a catalog
of eight components plus GeneratedView, whose one prop is HTML the model
writes and the page renders in a sandboxed iframe (step 03). The JSON
Schema the layout is validated against is built from the catalog, in two
shapes:

  tree: {"type": "Card", "props": {...}, "children": [ {...}, ... ]}
  flat: {"root": "r", "elements": {"r": {"type": "Card", "props": {...}, "children": ["a", "b"]}, "a": {...}}}

The flat shape is the one A2UI and json-render use. Step 02 shows why.
"""

import json

import jsonschema


def tool(name, description, properties):
    """One function-calling schema. Every property is required; nothing else is allowed."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
        },
    }


STRING = {"type": "string"}
STRINGS = {"type": "array", "items": STRING}

METRIC_PROPS = {
    "title": {"type": "string", "description": "Two or three words, such as 'Cups sold'."},
    "value": {"type": "string", "description": "The number as text, with its unit, such as '$412'."},
    "delta": {"type": "string", "description": "Change versus the previous period, such as '+12%'."},
}
TABLE_PROPS = {"columns": STRINGS, "rows": {"type": "array", "items": STRINGS}}
CHART_PROPS = {
    "kind": {"type": "string", "enum": ["bar", "line"]},
    "labels": STRINGS,
    "values": {"type": "array", "items": {"type": "number"}},
}

TOOL_SCHEMAS = [
    tool("show_metric", "Show one headline number with a short title and its change.", METRIC_PROPS),
    tool("show_table", "Show rows of detail with column headers.", TABLE_PROPS),
    tool("show_chart", "Show a trend or a comparison as a bar or line chart.", CHART_PROPS),
]

# tool name -> the component the page renders for it
COMPONENTS = {"show_metric": "Metric", "show_table": "Table", "show_chart": "Chart"}


def message_from_call(name, arguments):
    """One finished tool call -> the message the page renders, or None if it does not fit."""
    component = COMPONENTS.get(name)
    if component is None:
        return None
    try:
        props = json.loads(arguments)
    except json.JSONDecodeError:
        return None
    if not isinstance(props, dict):
        return None
    return {"component": component, "props": props}


# ------------------------------------------------------------- the catalog

# name -> (props schema, takes children?)
CATALOG = {
    "Card": ({"title": STRING}, True),
    "Row": ({}, True),
    "Column": ({}, True),
    "Text": ({"text": STRING}, False),
    "Metric": (METRIC_PROPS, False),
    "Table": (TABLE_PROPS, False),
    "Chart": (CHART_PROPS, False),
    "Button": ({"label": STRING, "action": STRING}, False),
    # The escape hatch: model-written HTML, rendered in the step 03 sandbox.
    "GeneratedView": ({"html": STRING}, False),
}


def node_schema(name, child_schema):
    """The schema of one node of one component. child_schema says what a child is."""
    props, has_children = CATALOG[name]
    schema = {
        "type": "object",
        "properties": {
            "type": {"const": name},
            "props": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False},
        },
        "required": ["type", "props"],
        "additionalProperties": False,
    }
    if has_children:
        schema["properties"]["children"] = {"type": "array", "items": child_schema}
    else:
        schema["properties"]["children"] = {"type": "array", "maxItems": 0}  # models write "children": [] on leaves
    return schema


def any_node_schema(child_schema):
    """A node of any catalog component: `type` picks which node_schema applies.

    if/then per component instead of oneOf, so a failing spec gets a message
    that names the prop, not "not valid under any of the given schemas".
    """
    return {
        "type": "object",
        "properties": {"type": {"enum": list(CATALOG)}},
        "required": ["type", "props"],
        "allOf": [
            {"if": {"properties": {"type": {"const": name}}, "required": ["type"]}, "then": node_schema(name, child_schema)}
            for name in CATALOG
        ],
    }


def tree_schema():
    """A nested tree: every child is itself a node."""
    return {"$defs": {"node": any_node_schema({"$ref": "#/$defs/node"})}, "$ref": "#/$defs/node"}


def flat_schema():
    """A flat element map: every child is the id of another element."""
    return {
        "type": "object",
        "properties": {
            "root": STRING,
            "elements": {"type": "object", "additionalProperties": any_node_schema(STRING)},
        },
        "required": ["root", "elements"],
        "additionalProperties": False,
    }


SCHEMAS = {"tree": tree_schema, "flat": flat_schema}


def validate(spec, shape):
    """The list of problems, empty when the spec fits the catalog. Also checks flat ids resolve."""
    validator = jsonschema.Draft202012Validator(SCHEMAS[shape]())
    problems = [f"{'/'.join(str(p) for p in e.path) or '/'}: {e.message}" for e in validator.iter_errors(spec)]
    if shape == "flat" and not problems:
        elements = spec["elements"]
        if spec["root"] not in elements:
            problems.append(f"root {spec['root']!r} is not an element")
        for element_id, element in elements.items():
            for child in element.get("children", []):
                if child not in elements:
                    problems.append(f"{element_id}: child {child!r} is not an element")
    return problems


# ---------------------------------------------------------------- prompts


def catalog_lines():
    """One line per component, the way the model sees it."""
    lines = []
    for name, (props, has_children) in CATALOG.items():
        fields = ", ".join(f"{key}: {schema.get('type', 'string')}" for key, schema in props.items())
        lines.append(f"- {name}({fields}){' takes children' if has_children else ''}")
    return "\n".join(lines)


TREE_EXAMPLE = {
    "type": "Card", "props": {"title": "Example"},
    "children": [{"type": "Row", "props": {}, "children": [{"type": "Metric", "props": {"title": "Cups", "value": "12", "delta": "+2"}}]}],
}
FLAT_EXAMPLE = {
    "root": "card",
    "elements": {
        "card": {"type": "Card", "props": {"title": "Example"}, "children": ["row"]},
        "row": {"type": "Row", "props": {}, "children": ["m1"]},
        "m1": {"type": "Metric", "props": {"title": "Cups", "value": "12", "delta": "+2"}},
    },
}

SHAPE_RULES = {
    "tree": "Answer with one JSON object: the root node. A node is {\"type\", \"props\", \"children\"}; "
            "children is a list of nodes and is only allowed on components that take children.",
    "flat": "Answer with one JSON object {\"root\", \"elements\"}. Write \"root\" first. \"elements\" maps an id to a node "
            "{\"type\", \"props\", \"children\"}, where children is a list of ids. Write the root element first, "
            "then its children in order, then their children: top-down, so the layout is known before the details.",
}


def system_prompt(shape):
    """The catalog, the shape's rules and one example, in the shape the model must write."""
    example = TREE_EXAMPLE if shape == "tree" else FLAT_EXAMPLE
    return (
        "You design dashboards as JSON, using only these components:\n"
        f"{catalog_lines()}\n"
        "Chart values are numbers; every other prop is a string. Only components marked "
        "'takes children' may have children. Put the metrics in a Row, "
        "the table and the chart side by side in a second Row, all inside one Card. "
        "Invent plausible sample data when the user gives none.\n"
        "GeneratedView is the escape hatch: its html prop is a small self-contained HTML fragment "
        "(inline style, inline SVG, no external resources) for one thing the catalog cannot show, "
        "such as a gauge. Use it at most once and keep it short.\n"
        "Button.action is an event name. When the user clicks, the app sends you that event and "
        "you answer with the updated dashboard.\n"
        f"{SHAPE_RULES[shape]}\nExample:\n{json.dumps(example)}\n"
        "Output only the JSON."
    )
