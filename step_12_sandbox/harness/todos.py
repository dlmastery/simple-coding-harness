"""Stage 12 - the plan (video 29:26).

"I keep a list of every task the agent wants to save and each task carries a
status: in progress, completed, or pending. Whenever this tool is called,
the agent has to overwrite previous to-dos by writing a new list."

The list lives here, not in the transcript, and is shown to the agent through
the late-injected block on every call - "so the LLM will always have access
to it after each message".
"""

MARKS = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}

TODOS = []  # [{"content": ..., "activeForm": ..., "status": ...}]


def write_todos(todos):
    """Replace the whole list. Exactly one task may be in_progress."""
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be."

    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt():
    return "\n".join(f"{MARKS[t['status']]} {t['content']}" for t in TODOS)


def active_form():
    """What the agent is doing right now, for the spinner."""
    for todo in TODOS:
        if todo["status"] == "in_progress":
            return todo["activeForm"]
    return "thinking"


TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_todos",
        "description": (
            "Record the plan for a multi-step task. Send the whole list every "
            "time. Keep exactly one task in_progress and update it as you go."
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
