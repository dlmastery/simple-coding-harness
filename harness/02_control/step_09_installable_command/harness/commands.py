"""Stage 9 - slash commands, unchanged from stage 8.
"""

from . import session
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to before one of your messages",
    "/sessions": "open a past chat",
    "/exit": "leave (ctrl-d and ctrl-c do the same)",
}


def preview(message):
    if message.get("tool_calls"):
        return "-> " + message["tool_calls"][0]["function"]["name"]
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, label):
    """The screen no longer matches the history, so wipe it and draw again."""
    ui.clear()
    ui.banner()
    ui.resumed(messages, label)
    ui.replay(messages)
    return messages


def rewind(messages):
    """Cut the chat back to just before one of your messages.

    Only user messages are offered: a cut there can never separate a tool
    call from its result, which the API would refuse on the next call.
    """
    users = [i for i, m in enumerate(messages) if m["role"] == "user"]
    choice = ui.pick("rewind to before", [preview(messages[i]) for i in users])
    if choice is None:
        return messages
    count = users[choice]
    session.save(messages)  # a fresh chat may not be on disk yet
    session.rewind_to(count)
    return redraw(messages[:count], "rewound")


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
    ui.note("\n".join(f"{name}  -  {help}" for name, help in COMMANDS.items()))
    return messages
