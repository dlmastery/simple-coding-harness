"""Step 27 - compaction runs the PreCompact hooks first. A hook that blocks
keeps the transcript as it is; /hooks lists what is configured.
"""

from . import compact as compaction
from . import hooks
from . import mcp_client
from . import memory
from . import history
from . import sandbox
from . import session
from .todos import restore
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to before one of your messages",
    "/sessions": "open a past chat",
    "/memory": "list what the agent remembers across sessions",
    "/compact": "summarise the history so far and free up the context window",
    "/mcp": "list the MCP servers, whether each started, and the tools they added",
    "/hooks": "list the hooks configured for each event",
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
    outcome = hooks.run_hooks("PreCompact", {"prompt": f"{before} messages"})
    if outcome.blocked:
        ui.note(f"compaction blocked by hook: {outcome.reason}")
        return messages
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


def hook_list(messages):
    """Every configured hook, grouped by event: its matcher and what it runs."""
    config = hooks.load_config()
    rows = [f"{event:<18} {hook.get('matcher') or '*':<24} {hooks.describe(hook)}" for event, found in config.items() for hook in found]
    ui.note("\n".join(rows) if rows else "no hooks configured (see .agents/hooks.json)")
    return messages


def handle(command, messages):
    if command == "/hooks":
        return hook_list(messages)
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
