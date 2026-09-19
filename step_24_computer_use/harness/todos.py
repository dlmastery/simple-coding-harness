"""Stage 15 - the plan.

The harness keeps a list of every task the agent wants to save. Each task
carries a status: pending, in_progress or completed. Every write_todos call
replaces the whole list, so there is exactly one current plan.

The list lives here, not in the transcript. The late injection shows it to
the model on every call, so the plan is always in front of the model.
"""

MARKS = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}

TODOS = []  # [{"content": ..., "activeForm": ..., "status": ...}]


def validate(todos):
    """The first problem with a list, or None. Checked before anything is stored."""
    if not isinstance(todos, list):
        return "Error: todos must be a list."
    for i, todo in enumerate(todos):
        if not isinstance(todo, dict):
            return f"Error: item {i} is not an object."
        for key in ("content", "activeForm", "status"):
            if not isinstance(todo.get(key), str) or not todo[key]:
                return f"Error: item {i} needs a non-empty {key!r}."
        if todo["status"] not in MARKS:
            return f"Error: item {i} has status {todo['status']!r}; use one of {', '.join(MARKS)}."
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. At most one may be."
    return None


def write_todos(todos):
    """Replace the whole list. At most one task may be in_progress."""
    problem = validate(todos)
    if problem:
        return problem  # the old list stays as it was

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


def restore(messages):
    """Rebuild the list from the last write_todos in a transcript (resume, rewind)."""
    import json

    TODOS.clear()
    for message in messages:
        for call in message.get("tool_calls") or []:
            if call["function"]["name"] != "write_todos":
                continue
            try:
                todos = json.loads(call["function"]["arguments"]).get("todos")
            except (ValueError, AttributeError):
                continue
            if validate(todos) is None:
                TODOS[:] = todos


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
