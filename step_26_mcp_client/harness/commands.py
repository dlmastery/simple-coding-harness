"""Step 26 - /mcp lists the MCP servers, their status and their tools.
"""

from . import compact as compaction
from . import mcp_client
from . import memory
from . import sandbox
from . import session
from . import todos
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to an earlier point in this chat",
    "/sessions": "open a past chat",
    "/compact": "summarise the history so far and free up the context window",
    "/memory": "list what the agent remembers across sessions",
    "/mcp": "list the MCP servers, whether each started, and the tools they added",
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
    return messages


def rewind(messages):
    """Cut the chat back to just before one of the user's messages.

    Only user messages are offered: a cut anywhere else could leave a tool
    call without its result, and the model refuses such a transcript.
    """
    users = [i for i, m in enumerate(messages) if m["role"] == "user"]
    rows = [f"{i:<4} {preview(messages[i])}" for i in users]
    choice = ui.pick("rewind to before", rows)
    if choice is None:
        return messages
    session.save(messages)  # a fresh chat has no file yet; the marker needs one
    cut = users[choice]
    session.rewind_to(cut)
    kept = messages[:cut]
    todos.restore(kept)  # the plan is whatever the kept transcript last wrote
    return redraw(kept, "rewound")


def sessions(messages):
    saved = session.all_sessions()
    if not saved:
        ui.note("no saved chats yet")
        return messages
    rows = [f"{s['id']}  {s['title']}" for s in saved]
    choice = ui.pick("open chat", rows)
    if choice is None:
        return messages
    opened = session.open_session(saved[choice]["id"])
    todos.restore(opened)  # the other chat's plan, not this one's
    return redraw(opened, "opened")


def compact(messages):
    before = len(messages)
    try:
        with ui.working("compacting"):
            compacted = compaction.compact(messages)
    except Exception as failure:  # noqa: BLE001
        # One more API call, fired when the window is nearly full - the worst
        # moment to lose the session over a rate limit. Keep going as we are.
        ui.note(f"compaction failed ({type(failure).__name__}); transcript kept as is")
        return messages
    if len(compacted) == before:
        ui.note("nothing old enough to compact yet")
        return messages
    session.compacted(compacted)
    ui.compacted(before, compacted)
    return compacted


def memories(messages):
    """Every memory, with its scope and type."""
    found = memory.find_memories()
    if not found:
        ui.note("no memories yet")
        return messages
    rows = [f"{name:<28} {m['scope']:<8} {m['type']:<10} {m['description']}" for name, m in found.items()]
    ui.note("\n".join(rows))
    return messages


def mcp(messages):
    """One line per configured server: name, status, and its tool names."""
    if not mcp_client.SERVERS:
        ui.note("no MCP servers configured (see .agents/mcp.json)")
        return messages
    rows = []
    for name, info in mcp_client.SERVERS.items():
        tools = ", ".join(info["tools"]) or "-"
        rows.append(f"{name:<12} {info['status']:<12} {tools}")
    ui.note("\n".join(rows))
    return messages


def handle(command, messages):
    if command == "/mcp":
        return mcp(messages)
    if command == "/compact":
        return compact(messages)
    if command == "/rewind":
        return rewind(messages)
    if command == "/sessions":
        return sessions(messages)
    if command == "/memory":
        return memories(messages)
    ui.note("\n".join(f"{name}  -  {help}" for name, help in COMMANDS.items()))
    return messages
