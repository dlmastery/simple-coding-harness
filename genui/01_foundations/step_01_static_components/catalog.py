"""Step 01 - three prebuilt components, offered to the model as tools.

Static generation: the components exist before the model runs. The model
only picks one and fills its props. The JSON Schema of each tool is the
contract; the API enforces it (strict mode), so the server never sees a
call that does not fit.
"""

import json


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


TOOL_SCHEMAS = [
    tool("show_metric", "Show one headline number with a short title and its change.", {
        "title": {"type": "string", "description": "Two or three words, such as 'Cups sold'."},
        "value": {"type": "string", "description": "The number as text, with its unit, such as '$412'."},
        "delta": {"type": "string", "description": "Change versus the previous period, such as '+12%'."},
    }),
    tool("show_table", "Show rows of detail with column headers.", {
        "columns": {"type": "array", "items": {"type": "string"}},
        "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
    }),
    tool("show_chart", "Show a trend or a comparison as a bar or line chart.", {
        "kind": {"type": "string", "enum": ["bar", "line"]},
        "labels": {"type": "array", "items": {"type": "string"}},
        "values": {"type": "array", "items": {"type": "number"}},
    }),
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
