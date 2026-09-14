"""Server tools. Each one returns a list of JSON Patch operations against the
shared state instead of drawing anything. The agent applies the patch, sends
it as STATE_DELTA, and the page renders whatever the state now says.

That is generative UI as state: the model chooses components and fills
their props, but what travels is a patch to one `dashboard` object.
"""


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


def execute(name, args):
    """Run one server tool. Returns (result text for the model, patch operations)."""
    if name not in TOOLS:
        return f"Error: no tool named {name}", []
    try:
        operations = TOOLS[name](**args)
    except TypeError as error:
        return f"Error: {error}", []
    return "ok", operations
