"""Stage 20 - /models shows the route and the catalogue; /route swaps the route in place.
"""

from . import compact as compaction
from . import history
from . import llm
from . import openrouter
from . import sandbox
from . import session
from .todos import restore
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to before one of your messages",
    "/sessions": "open a past chat",
    "/compact": "summarise the history so far and free up the context window",
    "/models": "show the model route, and the cheapest models OpenRouter offers",
    "/route": "/route <model>[,<fallback>...]  -  change the route for the rest of this chat",
    "/exit": "leave (ctrl-d and ctrl-c do the same)",
}

CATALOGUE_ROWS = 20


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


def models(messages):
    """The route, then the top of the catalogue sorted by prompt price."""
    with ui.working("fetching models"):
        catalogue = openrouter.list_models(llm.client)
    if not catalogue:
        ui.note("could not fetch the model list (no key, or offline); showing the route only")
    priced = [m for m in catalogue if m[2] is not None]
    cheapest = sorted(priced, key=lambda m: (m[2], m[3] or 0))[:CATALOGUE_ROWS]
    ui.models(openrouter.MODELS, cheapest)
    return messages


def route(command, messages):
    """/route a/b,c/d -> a/b is the primary, c/d the fallback. No argument shows the route."""
    argument = command[len("/route"):].strip()
    if not argument:
        ui.models(openrouter.MODELS, [])
        return messages
    openrouter.MODELS = openrouter.parse_route(argument)
    ui.note("route: " + " -> ".join(openrouter.MODELS))
    return messages


def handle(command, messages):
    if command == "/compact":
        return compact(messages)
    if command == "/rewind":
        return rewind(messages)
    if command == "/sessions":
        return sessions(messages)
    if command == "/models":
        return models(messages)
    if command == "/route" or command.startswith("/route "):
        return route(command, messages)
    ui.note("\n".join(f"{name}  -  {help}" for name, help in COMMANDS.items()))
    return messages
