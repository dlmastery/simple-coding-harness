"""Stage 8 - slash commands. Anything typed starting with / lands here."""

import session
from ui import ui

COMMANDS = {
    "/rewind": "jump back to before one of your messages",
    "/sessions": "open a past chat",
    "/exit": "leave (so do ctrl-d and ctrl-c)",
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
    """Offer your own messages and cut just before the one you pick. Cutting anywhere
    else could strand a tool call without its result, which the API refuses."""
    session.save(messages)  # so a fresh chat is on disk before its first marker
    turns = [i for i, m in enumerate(messages) if m["role"] == "user"]
    rows = [f"{i:<4} {preview(messages[i])}" for i in turns]
    choice = ui.pick("rewind to before", rows)
    if choice is None:
        return messages
    count = turns[choice]
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
    """One function: take the list, return the list to continue with."""
    if command == "/rewind":
        return rewind(messages)
    if command == "/sessions":
        return sessions(messages)
    ui.note("\n".join(f"{name}  -  {help}" for name, help in COMMANDS.items()))
    return messages
