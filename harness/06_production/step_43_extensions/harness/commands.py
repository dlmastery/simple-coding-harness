"""Step 43 - /extensions lists every extension: the built-in loaders and
the project's files, with what each one registered, and a failed one
with its reason. handle() looks in the registry's commands after its own
table, so a command an extension registered - /status from the shipped
git_tools.py, /hooks and /mcp from the built-in loaders - runs from the
same prompt line, and the help lists it with the rest.
The rest is step 40: /agent names the active agent and who it may hand off to;
/handoff <name> forces a handoff to any definition, or to main for the
default agent, from the prompt line.
The rest is step 39: /mode lists the approval modes or switches to one; the banner
and the late block show the mode from the next call on. /plan and /act
still work: plan is one of the modes, and leaving it brings back the
mode the user had before.
The rest is step 36: /pipeline <task> runs the plan, work, review pipeline: the
planner agent writes a numbered plan, the worker agent carries out each
step, the reviewer agent checks it and a failed step is worked once more
with the reviewer's notes. The steps of the whole run are captured as one
checkpoint turn, so one /undo takes every edit back. The rest is step 33:
/undo puts the files back as they were before the last turn
and cuts the transcript to the start of that turn. /rewind restores the
files as well as the messages: every turn that began at or after the
chosen point is undone. /checkpoints lists the turns and the files each
one captured. Compaction moves the recorded turn starts with the
transcript. The rest is step 32.
"""

from pathlib import Path

from . import agents as agents_
from . import budget
from . import checkpoint
from . import compact as compaction
from . import extensions
from . import handoff
from . import hooks
from . import instructions
from . import jobs
from . import llm
from . import plan
from . import memory
from . import history
from . import modes
from . import pipeline
from . import sandbox
from . import session
from . import stop
from . import subagent
from .todos import restore
from . import tools
from .ui import ui

COMMANDS = {
    "/agent": "show the active agent and who it may hand off to",
    "/handoff": "hand the conversation to an agent: /handoff <name>, or /handoff main for the default agent",
    "/mode": "show the approval modes, or switch: /mode default|accept-edits|read-only|auto|plan",
    "/pipeline": "plan a task, then work and review every step with the project's agents",
    "/rewind": "jump back to before one of your messages, files included",
    "/undo": "undo the last turn: its file changes and its messages",
    "/checkpoints": "list the turns of this chat and the files each one changed",
    "/sessions": "open a past chat",
    "/memory": "list what the agent remembers across sessions",
    "/compact": "summarise the history so far and free up the context window",
    "/extensions": "list the extensions, what each one registered, and the ones that failed",
    "/plan": "plan mode: read-only tools until you approve a plan",
    "/act": "act mode: every tool, the default",
    "/jobs": "list the background jobs and whether each is still running",
    "/context": "show what fills the context window, category by category",
    "/cost": "show what this session has cost and the budgets that stop a turn",
    "/init": "survey the project with a subagent and write AGENTS.md",
    "/instructions": "list the instruction files in the system prompt",
    "/exit": "leave (ctrl-d and ctrl-c do the same)",
}

INIT_QUESTION = """
Survey this repository and write AGENTS.md: a short guide for a coding agent
that is new to the project. Use these headings, in this order:

1. Overview - what the project is and does, in one paragraph.
2. Build system - the language and version, the package manager, the exact
   commands to install and build.
3. Test command - the exact command that runs the whole test suite, and the
   one that runs a single test file.
4. Layout - the main directories and files and what lives in each.
5. Conventions - formatting, naming, docstring and commit style, anything the
   existing code makes obvious.

Report only what the files show; quote commands and paths exactly. Say
plainly what you could not find. Markdown, no preamble: the report is
written to the file as it is. This guide is the one report that may run
past your usual length: up to 400 words.
"""


def preview(message):
    if message.get("tool_calls"):
        return "-> " + message["tool_calls"][0]["function"]["name"]
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, label):
    """The screen no longer matches the history, so wipe it and draw again."""
    ui.clear()
    ui.banner(sandbox.name(), modes.current())
    ui.resumed(messages, label)
    ui.replay(messages)
    restore(messages)  # the plan lives outside the transcript; rebuild it from this one
    tools.relearn(messages)  # and so do the deferred tools the model loaded
    return messages


def rewind(messages):
    """Cut the chat back to just before one of your messages and undo the turns from there on.

    Only user messages are offered: a cut anywhere else would leave a tool
    call without its result, or a turn's files changed while its messages
    are gone.
    """
    users = [i for i, m in enumerate(messages) if m["role"] == "user"]
    choice = ui.pick("rewind to before", [preview(messages[i]) for i in users])
    if choice is None:
        return messages
    cut = users[choice]
    undone = checkpoint.undo_since(cut)
    restored = [path for _, _, paths in undone for path in paths]
    if undone:
        ui.note(f"{len(undone)} turn(s) undone, {len(restored)} file(s) restored")
    session.save(messages)  # a fresh chat may not be on disk yet
    session.rewind_to(cut)
    return redraw(messages[:cut], "rewound")


def undo(messages):
    """Restore the files of the last turn and cut the transcript to where that turn began."""
    undone = checkpoint.undo_turn()
    if undone is None:
        ui.note("nothing to undo")
        return messages
    turn, start, restored = undone
    ui.note(f"turn {turn} undone: " + (", ".join(restored) if restored else "no files were changed"))
    if start is None or start > len(messages):
        ui.note("that turn's place in the transcript is not known; the messages stay")
        return messages
    session.rewind_to(start)
    return redraw(messages[:start], "undone")


def checkpoint_list(messages):
    """One row per turn: its number, where it began, and the files it captured."""
    rows = checkpoint.summary()
    ui.note("\n".join(rows) if rows else "no checkpoints in this chat yet")
    return messages


def sessions(messages):
    saved = session.all_sessions()
    if not saved:
        ui.note("no saved chats yet")
        return messages
    rows = [f"{s['id']}  {s['title']}" for s in saved]
    choice = ui.pick("open chat", rows)
    if choice is None:
        return messages
    from .agent import recover  # here, not at the top: agent imports this module

    opened = session.open_session(saved[choice]["id"])
    history.strip(opened)  # the same shrink --resume does
    redraw(opened, "opened")
    recover(opened)  # a crash mid-turn left tool calls without results: run them now, as --resume does
    return opened


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
    budget.WARNED.clear()  # the window is mostly free again: the 50% and 75% notes may fire once more
    checkpoint.compacted(before, len(compacted))  # the turn starts move with the messages
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


def extension_list(messages):
    """One row per extension: its name, whether it loaded, where it came from, and what it registered."""
    rows = extensions.summary()
    ui.note("\n".join(rows) if rows else "no extensions loaded (see .agents/extensions)")
    return messages


def registered(command, messages):
    """Run a command an extension registered, or return None when none matches.

    A command that raises is a note, not the end of the chat: the messages
    come back as they were.
    """
    for name, (_, fn) in extensions.COMMANDS.items():
        if command == name or command.startswith(name + " "):
            try:
                result = fn(messages, command[len(name):].strip())
            except Exception as failed:  # noqa: BLE001 - an extension's bug must not take the loop down
                ui.note(f"command {name} failed: {type(failed).__name__}: {failed}")
                return messages
            return messages if result is None else result
    return None


def job_list(messages):
    """One line per background job: id, state and command."""
    if not jobs.JOBS:
        ui.note("no background jobs in this session")
        return messages
    ui.note("\n".join(f"{job.id:<8} {job.state():<28} {job.command}" for job in jobs.JOBS.values()))
    return messages


def cost(messages):
    """What the session spent so far, the three budgets, and the Stop hook count of this turn."""
    ui.note(stop.status())
    return messages


def context_budget(messages):
    """The estimated tokens per category for the next request, as bars."""
    ui.context(budget.render(messages))
    return messages


def set_mode(messages, mode):
    """Switch between plan and act; the late block carries the mode from the next call on."""
    plan.set_mode(mode)
    if mode == "plan":
        ui.note("plan mode: the model reads and proposes; nothing is written until you approve a plan")
    else:
        ui.note(f"{modes.current()} mode: {modes.MODES[modes.current()]}")
    return messages


def agent_info(messages):
    """The active agent, its description and the names it may hand off to."""
    active = handoff.ACTIVE
    what = "the default coding agent" if active is None else active["description"]
    targets = ", ".join(handoff.targets()) or "nobody"
    ui.note(f"active agent: {handoff.active_name()} - {what}; may hand off to: {targets}")
    return messages


def force_handoff(messages, name):
    """Hand the conversation to `name` from the prompt line. The lists do not apply: the user is in charge."""
    if not name:
        ui.note("usage: /handoff <name>; the agents are " + ", ".join(agents_.AGENTS) + ", or main")
        return messages
    handoff.switch(messages, name, "/handoff")
    return messages


def mode(messages, name):
    """Without a name, list the modes with the current one marked. With one, switch to it."""
    if not name:
        ui.note(modes.describe())
        return messages
    try:
        modes.set_mode(name)
    except ValueError as unknown:
        ui.note(str(unknown))
        return messages
    ui.note(f"{name} mode: {modes.MODES[name]}")
    return messages


def init(messages):
    """Survey the project with a subagent; write the report to AGENTS.md on approval."""
    target = Path.cwd() / "AGENTS.md"
    report = subagent.task(INIT_QUESTION.strip())
    ui.agent(report)
    if report.startswith(subagent.STOPPED) or report.startswith("Error:"):
        ui.note("the subagent did not produce a guide; nothing written")
        return messages
    if target.exists():
        what = f"write {target.name} (it exists; this replaces it)"
    elif (target.parent / "CLAUDE.md").is_file():
        what = f"write {target.name} (CLAUDE.md is here too; it is read only when AGENTS.md is absent, so it stops being read)"
    else:
        what = f"write {target.name}"
    if not ui.confirm(what):
        ui.note("not written")
        return messages
    target.write_text(report.strip() + "\n", encoding="utf-8")
    handoff.refresh(messages)  # discovery runs again, so the new file is in the prefix; the active agent and the summary stay
    ui.note(f"wrote {target}; it is in the system prompt from the next call on")
    return messages


def instruction_list(messages):
    """The instruction files the system prompt carries, in the order they were read."""
    if not instructions.LOADED:
        ui.note("no instruction files loaded (AGENTS.md or CLAUDE.md in ~/.simple-harness, the git root, or below)")
        return messages
    rows = []
    for path in instructions.LOADED:  # the files the prompt was built from, not what is on disk now
        size = len(path.read_text(encoding="utf-8-sig", errors="replace"))
        cut = f"  (cut at {instructions.MAX_CHARS:,})" if size > instructions.MAX_CHARS else ""
        rows.append(f"{instructions.label(path):<40} {size:>7,} chars{cut}")
    ui.note("\n".join(rows))
    return messages


def run_pipeline(messages, task):
    """Plan, work and review a task with the shipped agents; print the summary table."""
    if not task:
        ui.note("usage: /pipeline <task>")
        return messages
    missing = pipeline.missing_agents()
    if missing:
        ui.note(f"the pipeline needs the {', '.join(missing)} definition(s) in .agents/agents; none ran")
        return messages
    checkpoint.begin_turn(len(messages))  # every edit of the run lands in one turn, so one /undo takes it all back
    plan_text, steps = pipeline.run(task)
    if not steps:
        ui.note(f"the planner returned no numbered steps:\n{plan_text.strip()}")
        return messages
    ui.pipeline(pipeline.summary(steps))
    passed = sum(1 for step in steps if step.verdict == "PASS")
    ui.note(f"pipeline: {len(steps)} step(s), {passed} passed, {len(steps) - passed} failed")
    return messages


def handle(command, messages):
    if command == "/agent":
        return agent_info(messages)
    if command == "/handoff" or command.startswith("/handoff "):
        return force_handoff(messages, command[len("/handoff"):].strip())
    if command == "/mode" or command.startswith("/mode "):
        return mode(messages, command[len("/mode"):].strip())
    if command == "/pipeline" or command.startswith("/pipeline "):
        return run_pipeline(messages, command[len("/pipeline"):].strip())
    if command == "/plan":
        return set_mode(messages, "plan")
    if command == "/act":
        return set_mode(messages, "act")
    if command == "/extensions":
        return extension_list(messages)
    if command == "/jobs":
        return job_list(messages)
    if command == "/context":
        return context_budget(messages)
    if command == "/cost":
        return cost(messages)
    if command == "/compact":
        return compact(messages)
    if command == "/rewind":
        return rewind(messages)
    if command == "/undo":
        return undo(messages)
    if command == "/checkpoints":
        return checkpoint_list(messages)
    if command == "/sessions":
        return sessions(messages)
    if command == "/memory":
        return memories(messages)
    if command == "/init":
        return init(messages)
    if command == "/instructions":
        return instruction_list(messages)
    handled = registered(command, messages)
    if handled is not None:
        return handled
    listed = {**COMMANDS, **{name: help for name, (help, _) in extensions.COMMANDS.items()}}
    ui.note("\n".join(f"{name}  -  {help}" for name, help in listed.items()))
    return messages
