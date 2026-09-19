"""Stage 20 - /models shows the route and the catalogue; /route swaps the route in place.
"""

from . import compact as compaction
from . import llm
from . import openrouter
from . import sandbox
from . import session
from . import todos
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to an earlier point in this chat",
    "/sessions": "open a past chat",
    "/compact": "summarise the history so far and free up the context window",
    "/models": "show the model route, and the cheapest models OpenRouter offers",
    "/route": "/route <model>[,<fallback>...]  -  change the route for the rest of this chat",
}

CATALOGUE_ROWS = 20


def preview(message):
    if message.get("tool_calls"):
        return "-> " + message["tool_calls"][0]["function"]["name"]
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, label):
    """The screen no longer matches the history, so wipe it and draw again."""
    todos.rebuild(messages)  # the plan lives outside the transcript; rebuild it from it
    ui.clear()
    ui.banner(sandbox.name())
    ui.resumed(messages, label)
    ui.replay(messages)
    return messages


def rewind(messages):
    """Cut before a user message. Only user rows are offered: cutting inside a
    tool exchange would leave a tool_call without its result."""
    session.save(messages)  # a fresh session may have nothing on disk yet
    turns = [i for i, m in enumerate(messages) if m["role"] == "user"]
    rows = [f"turn {n + 1:<4} {preview(messages[i])}" for n, i in enumerate(turns)]
    choice = ui.pick("rewind to before", rows)
    if choice is None:
        return messages
    cut = turns[choice]
    session.rewind_to(cut)
    return redraw(messages[:cut], "rewound")


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
    if command == "/models":
        return models(messages)
    if command == "/route" or command.startswith("/route "):
        return route(command, messages)
    if command == "/rewind":
        return rewind(messages)
    if command == "/sessions":
        return sessions(messages)
    ui.note("\n".join(f"{name}  -  {help}" for name, help in COMMANDS.items()))
    return messages
