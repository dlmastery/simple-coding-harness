"""Stage 14 - slash commands gain /compact.
"""

from . import compact as compaction
from . import history
from . import sandbox
from . import session
from .todos import restore
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to before one of your messages",
    "/sessions": "open a past chat",
    "/compact": "summarise the history so far and free up the context window",
    "/exit": "leave (ctrl-d and ctrl-c do the same)",
}


def preview(message):
    if message.get("tool_calls"):
        return "-> " + message["tool_calls"][0]["function"]["name"]
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, label):
    """The screen no longer matches the history, so wipe it and draw again."""
    ui.clear()
    ui.banner(sandbox.name())
    ui.resumed(messages, label)
    ui.replay(messages)
    restore(messages)  # the plan lives outside the transcript; rebuild it from this one
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
    messages = session.open_session(saved[choice]["id"])
    history.strip(messages)  # the same shrink --resume does
    return redraw(messages, "opened")


def compact(messages):
    before = len(messages)
    try:
        with ui.working("compacting"):
            compacted = compaction.compact(messages)
    except Exception as failure:  # noqa: BLE001
        # One more API call, fired when the window is nearly full - the worst
        # moment to lose the session over a rate limit. Keep going as we are.
        ui.note(f"compaction failed ({type(failure).__name__}); transcript kept as is")
        compaction.COMPACTED_AT = before  # do not try again until the transcript has grown
        return messages
    if len(compacted) == before:
        ui.note("nothing old enough to compact yet")
        compaction.COMPACTED_AT = before
        return messages
    session.compacted(compacted)
    ui.compacted(before, compacted)
    return compacted


def handle(command, messages):
    if command == "/compact":
        return compact(messages)
    if command == "/rewind":
        return rewind(messages)
    if command == "/sessions":
        return sessions(messages)
    ui.note("\n".join(f"{name}  -  {help}" for name, help in COMMANDS.items()))
    return messages
