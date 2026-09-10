"""Slash commands. Anything typed starting with / lands here, not in the model.

A command receives the message list and returns the (possibly different)
list the loop should carry on with. That is the whole contract.
"""

from . import sandbox, session
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to an earlier point in this chat",
    "/sessions": "open a past chat",
    "/help": "list commands",
}


def preview(message):
    if message.get("tool_calls"):
        return "-> " + message["tool_calls"][0]["function"]["name"]
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, label):
    """The screen no longer matches the history: wipe it and draw it again."""
    ui.clear()
    ui.banner(sandbox.name())
    ui.resumed(messages, label)
    ui.replay(messages)
    return messages


def rewind(messages):
    rows = [f"{m['role']:<9} {preview(m)}" for m in messages]
    choice = ui.pick("rewind to (keep everything up to and including)", rows)
    if choice is None:
        return messages
    session.rewind_to(choice + 1)
    return redraw(messages[: choice + 1], "rewound")


def sessions(messages):
    saved = session.all_sessions()
    if not saved:
        ui.note("no saved chats yet")
        return messages
    rows = [f"{s['id']}  {s['title']}" for s in saved]
    choice = ui.pick("open chat", rows)
    if choice is None:
        return messages
    return redraw(session.open_session(saved[choice]["id"]), "opened")


def handle(command, messages):
    if command == "/rewind":
        return rewind(messages)
    if command == "/sessions":
        return sessions(messages)
    ui.note("\n".join(f"{name:<10} {help}" for name, help in COMMANDS.items()))
    return messages
