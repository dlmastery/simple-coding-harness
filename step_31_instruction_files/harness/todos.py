"""Stage 15 - the plan.

The harness keeps a list of every task the agent wants to save. Each task
carries a status: pending, in_progress or completed. Every write_todos call
replaces the whole list, so there is exactly one current plan.

The list lives here, not in the transcript. The late injection shows it to
the model on every call, so the plan is always in front of the model.
"""

import json

MARKS = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}

TODOS = []  # [{"content": ..., "activeForm": ..., "status": ...}]


def write_todos(todos):
    """Replace the whole list. At most one task may be in_progress.

    The list is checked before anything is assigned, so a bad call leaves
    the current plan as it was and the model reads why.
    """
    if not isinstance(todos, list):
        return "Error: todos must be a list"
    for i, todo in enumerate(todos):
        if not isinstance(todo, dict):
            return f"Error: item {i} is not an object"
        for key in ("content", "activeForm"):
            if not isinstance(todo.get(key), str) or not todo[key]:
                return f"Error: item {i} needs a non-empty {key!r}"
        if todo.get("status") not in MARKS:
            return f"Error: item {i} has status {todo.get('status')!r}; use one of {', '.join(MARKS)}"
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be."

    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt():
    return "\n".join(f"{MARKS.get(t.get('status'), '[?]')} {t.get('content', '')}" for t in TODOS)


def active_form():
    """What the agent is doing right now, for the spinner."""
    for todo in TODOS:
        if todo.get("status") == "in_progress":
            return todo.get("activeForm") or "working"
    return "thinking"


def from_transcript(messages):
    """Rebuild the list from the last write_todos call that succeeded, for a resumed chat."""
    results = {m.get("tool_call_id"): m.get("content") or "" for m in messages if m.get("role") == "tool"}
    found = []
    for message in messages:
        for call in message.get("tool_calls") or []:
            if call["function"]["name"] != "write_todos" or results.get(call["id"], "").startswith("Error"):
                continue
            try:
                todos = json.loads(call["function"]["arguments"]).get("todos")
            except (ValueError, AttributeError):
                continue
            if isinstance(todos, list):
                found = todos
    TODOS[:] = found
    return TODOS


TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_todos",
        "description": (
            "Record the plan for a multi-step task. Send the whole list every "
            "time. Keep at most one task in_progress and update it as you go."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The task, imperative: 'Fix the parser'"},
                            "activeForm": {"type": "string", "description": "Present continuous: 'Fixing the parser'"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                        },
                        "required": ["content", "activeForm", "status"],
                    },
                }
            },
            "required": ["todos"],
        },
    },
}
