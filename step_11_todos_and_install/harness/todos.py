"""The plan. Lives here, not in the transcript, and is re-injected every call.

Why not just let the model write its plan in prose? Because prose scrolls
away. Twenty tool calls later the plan is buried under output and the model
drifts. Keeping the list in a variable and injecting it into the late block
on every call means the current state of the plan is always the last thing
the model reads before it acts.
"""

MARKS = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}

TODOS = []  # [{"content": ..., "active": ..., "status": ...}]


def write_todos(todos: list) -> str:
    """Replace the whole todo list. Exactly one item may be in_progress."""
    active = [t for t in todos if t.get("status") == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} items are in_progress. Keep exactly one."
    for todo in todos:
        if todo.get("status") not in MARKS:
            return f"Error: status must be one of {list(MARKS)}, got {todo.get('status')!r}."
    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt():
    """The list as the model sees it in the late block."""
    return "\n".join(f"{MARKS[t['status']]} {t['content']}" for t in TODOS)


def active_form():
    """What the agent is doing right now, for the spinner."""
    for todo in TODOS:
        if todo["status"] == "in_progress":
            return todo.get("active") or todo["content"]
    return "thinking"


TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_todos",
        "description": (
            "Record the plan for a task with several steps. Send the whole list "
            "every time - it replaces the previous one. Keep exactly one item "
            "in_progress and mark items done as soon as they are."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Imperative: 'Add the test'"},
                            "active": {"type": "string", "description": "Present continuous: 'Adding the test'"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "done"]},
                        },
                        "required": ["content", "active", "status"],
                    },
                }
            },
            "required": ["todos"],
        },
    },
}
