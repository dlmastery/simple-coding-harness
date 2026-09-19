"""Server tools. Each one returns a list of JSON Patch operations against the
shared state instead of drawing anything. The agent applies the patch, sends
it as STATE_DELTA, and the page renders whatever the state now says.

That is generative UI as state: the model chooses components and fills
their props, but what travels is a patch to one `dashboard` object.
"""

import inspect
import json


def initial_state():
    return {"dashboard": {"metrics": [], "table": None, "chart": None, "purchases": []}}


def show_metric(title: str, value: str, delta: str = "") -> list:
    """Add one metric card to the dashboard."""
    return [{"op": "add", "path": "/dashboard/metrics/-", "value": {"title": title, "value": value, "delta": delta}}]


def show_table(columns: list, rows: list) -> list:
    """Set the dashboard table (one table, replaced each time)."""
    return [{"op": "replace", "path": "/dashboard/table", "value": {"columns": columns, "rows": rows}}]


def show_chart(kind: str, labels: list, values: list) -> list:
    """Set the dashboard chart. kind is 'bar' or 'line'."""
    return [{"op": "replace", "path": "/dashboard/chart", "value": {"kind": kind, "labels": labels, "values": values}}]


def record_purchase(item: str, cost: float) -> list:
    """Record a purchase the user has confirmed."""
    return [{"op": "add", "path": "/dashboard/purchases/-", "value": {"item": item, "cost": cost}}]


TOOLS = {
    "show_metric": show_metric,
    "show_table": show_table,
    "show_chart": show_chart,
    "record_purchase": record_purchase,
}


def schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOL_SCHEMAS = [
    schema("show_metric", "Add one metric card. Call once per metric.",
           {"title": {"type": "string"}, "value": {"type": "string"}, "delta": {"type": "string", "description": "change versus last period, e.g. +12%"}},
           ["title", "value"]),
    schema("show_table", "Show one table of rows.",
           {"columns": {"type": "array", "items": {"type": "string"}},
            "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}},
           ["columns", "rows"]),
    schema("show_chart", "Show one chart.",
           {"kind": {"type": "string", "enum": ["bar", "line"]},
            "labels": {"type": "array", "items": {"type": "string"}},
            "values": {"type": "array", "items": {"type": "number"}}},
           ["kind", "labels", "values"]),
    schema("record_purchase", "Record a purchase after the user confirmed it.",
           {"item": {"type": "string"}, "cost": {"type": "number"}},
           ["item", "cost"]),
]


def execute(name, arguments):
    """Run one server tool on the JSON arguments the model wrote.

    Returns (result text for the model, patch operations) and never raises:
    a bad name, arguments that are not a JSON object, a missing argument or
    a tool that fails all come back as an "Error: ..." result, so the model
    can try again and the run goes on.
    """
    if name not in TOOLS:
        return f"Error: no tool named {name!r}.", []
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError as error:
        return f"Error: the arguments of {name} are not a JSON object: {error}", []
    if not isinstance(args, dict):
        return f"Error: the arguments of {name} are not a JSON object: got {type(args).__name__}", []
    try:
        inspect.signature(TOOLS[name]).bind(**args)  # a missing or unknown argument, before the tool runs
    except TypeError as error:
        return f"Error: {error}", []
    try:
        return "ok", TOOLS[name](**args)
    except Exception as error:  # noqa: BLE001 - the error is the result
        return f"Error: {type(error).__name__}: {error}", []
