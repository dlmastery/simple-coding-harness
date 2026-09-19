"""Step 40 - handoffs: the whole conversation moves to another agent
definition. The transcript stays; the system prompt and the tool set
change; the new agent answers the user from then on.

ACTIVE is the definition the main loop runs as, or None for the default
coding agent. The model calls handoff_to(agent, reason); the tool checks
the target against the active definition's `handoffs:` list, records the
name in PENDING and returns a result the model reads. After the tool
results of that reply are in, agent.turn calls switch(): messages[0] is
rewritten to the new agent's prompt, the session log gets a
{"handoff": name} marker so --resume restores the agent, and the UI shows
"handoff -> name". The next model call goes out with the new prompt and
the new tool set.

The rewrite of messages[0] is the one deliberate change to the cached
prefix. It happens at a handoff boundary, where a new agent takes over
and a new prefix is the point, so the cache loss is the price of the
feature and nothing else. Compaction's <summary> block, if the prefix
carries one, is kept through the swap.

A definition takes part in handoffs when its front matter has a
`handoffs` list; the list names the definitions it may hand off to. The
default agent may hand off to every definition that has such a list.
/handoff <name> forces a handoff from the prompt line and is not limited
by the lists; /handoff main returns to the default agent.
"""

from . import agents, plan

MAIN = "main"     # the name of the default coding agent, which has no definition file
ACTIVE = None     # the active definition, or None for the default agent
PENDING = None    # the name a handoff_to call asked for, until switch() applies it
LAST_REASON = ""  # the reason the model gave for the pending handoff
MAX_HANDOFFS = 4  # handoffs one turn may make; two agents passing the conversation back and forth stop here
HANDOFFS = 0      # handoffs made this turn

ALWAYS = ("handoff_to", "finish", "submit_plan", "load_tool")  # offered to every agent, whatever its tools: list says

HANDOFF_SCHEMA = {
    "type": "function",
    "function": {
        "name": "handoff_to",
        "description": (
            "Hand the whole conversation to another agent. The transcript stays; "
            "that agent's instructions and tools replace yours from the next reply on, "
            "and it answers the user. Say why in one sentence."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "The name of the agent to hand off to"},
                "reason": {"type": "string", "description": "Why this agent should take over"},
            },
            "required": ["agent", "reason"],
        },
    },
}

HANDOFF_INTRO = """
You can hand the whole conversation to another agent with handoff_to. The
transcript stays; the other agent's instructions and tools replace yours,
and it answers the user from then on. Hand off when another agent's
description fits the request better than yours; otherwise do the work
yourself. You may hand off to:
"""


def active_name():
    """The name of the active agent: its definition's name, or `main`."""
    return MAIN if ACTIVE is None else ACTIVE["name"]


def definition(name):
    """The definition behind a name, or None. `main` has none."""
    return agents.AGENTS.get(name)


def offered(name):
    """Whether the active agent may run a tool: everything, or its `tools:` list plus ALWAYS."""
    wanted = None if ACTIVE is None else ACTIVE.get("tools")
    return wanted is None or name in wanted or name in ALWAYS


def begin_turn():
    """A new turn: the handoff count starts over."""
    global HANDOFFS
    HANDOFFS = 0


def targets(active=None):
    """The names the active definition may hand off to, in definition order.

    The default agent may hand off to every definition with a `handoffs`
    list. A definition may hand off to the names on its own list, and only
    to names that exist.
    """
    active = ACTIVE if active is None else active
    if active is None:
        return [name for name, a in agents.AGENTS.items() if a.get("handoffs") is not None]
    return [name for name in active.get("handoffs") or [] if name in agents.AGENTS]


def handoff_section(active=None):
    """The handoff_to guidance with the allowed targets, or empty when there are none."""
    names = targets(active)
    if not names:
        return ""
    return HANDOFF_INTRO + "\n".join(f"- {name}: {agents.AGENTS[name]['description']}" for name in names) + "\n"


def system_prompt(active, cwd=None):
    """The main system prompt with the definition's body in place of the default role.

    build_system_prompt supplies everything the default agent gets: the
    tool guidance, the agent index, the deferred tools, the instruction
    files and the skills. Only the opening role changes.
    """
    from .llm import build_system_prompt  # here, not at the top: llm imports tools, tools imports this module

    role = None if active is None else active["prompt"]
    return build_system_prompt(cwd, role=role, handoffs=handoff_section(active))


def toolset():
    """The schemas the active agent is offered: the mode's set, cut to the definition's list, plus handoff_to.

    The default agent gets the mode's whole set. A definition with a
    `tools` list gets the mode's set cut to that list; submit_plan stays
    in plan mode whatever the list says. handoff_to is added whenever the
    active agent has a target.
    """
    wanted = None if ACTIVE is None else ACTIVE.get("tools")
    chosen = [s for s in plan.toolset() if wanted is None or s["function"]["name"] in wanted or s["function"]["name"] == "submit_plan"]
    if targets():
        chosen.append(HANDOFF_SCHEMA)
    return chosen


def handoff_to(agent: str, reason: str) -> str:
    """Ask for a handoff. The switch happens after this reply's results are in."""
    global PENDING, LAST_REASON
    if agent == active_name():
        return f"Error: {agent} is already the active agent."
    if HANDOFFS >= MAX_HANDOFFS:
        return f"Error: {HANDOFFS} handoffs this turn already (MAX_HANDOFFS={MAX_HANDOFFS}); answer the user yourself."
    allowed = targets()
    if agent not in allowed:
        if definition(agent) is None and agent != MAIN:
            return f"Error: no agent named '{agent}'. You may hand off to: {', '.join(allowed) or 'nobody'}."
        return f"Error: {active_name()} may not hand off to '{agent}'. You may hand off to: {', '.join(allowed) or 'nobody'}."
    PENDING = agent
    LAST_REASON = reason
    return f"Handing off to {agent}: {reason}. The {agent} agent answers from the next reply on; do not answer the user yourself."


def apply(name, messages):
    """Make `name` the active agent and rewrite messages[0] to its prompt. Returns the definition.

    Nothing is logged here; switch() logs, and session.load calls this
    when it replays a marker. A compaction <summary> block in the old
    prompt is carried over, so the new agent reads what came before.
    """
    global ACTIVE
    from . import compact  # here, not at the top: compact imports llm

    ACTIVE = None if name == MAIN else definition(name)
    if name != MAIN and ACTIVE is None:
        raise KeyError(name)
    if messages and messages[0].get("role") == "system":
        summary = compact.previous_summary(messages[0]["content"])
        prompt = system_prompt(ACTIVE)
        messages[0]["content"] = prompt + ("\n\n" + summary if summary else "")
    return ACTIVE


def switch(messages, name=None, reason=None):
    """Apply a pending or forced handoff: prompt, log marker, UI line. Returns the new name or None.

    With no name, the pending one from handoff_to is used; nothing
    happens when there is none. A name that is not a definition, and is
    not `main`, is refused with a note.
    """
    global PENDING, LAST_REASON, HANDOFFS
    from . import session
    from .ui import ui

    name = PENDING if name is None else name
    reason = LAST_REASON if reason is None else reason
    PENDING = None
    LAST_REASON = ""
    if name is None:
        return None
    if name != MAIN and definition(name) is None:
        ui.note(f"no agent named '{name}'")
        return None
    previous = active_name()
    apply(name, messages)
    HANDOFFS += 1
    session.handoff(name)
    ui.handoff(previous, name, reason)
    return name


def reset():
    """Back to the default agent, with nothing pending. Used at session start and by tests."""
    global ACTIVE, PENDING, LAST_REASON, HANDOFFS
    ACTIVE = None
    PENDING = None
    LAST_REASON = ""
    HANDOFFS = 0
