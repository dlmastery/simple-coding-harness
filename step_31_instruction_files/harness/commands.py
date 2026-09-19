"""Step 31 - /init writes an AGENTS.md for the working directory and
/instructions lists the instruction files the system prompt carries.
/init sends an explorer subagent with a fixed question, shows the report,
asks `approve? (y/n)` and writes the file on yes. The rest is step 29.
"""

from pathlib import Path

from . import compact as compaction
from . import history
from . import hooks
from . import instructions
from . import jobs
from . import llm
from . import plan
from . import mcp_client
from . import memory
from . import sandbox
from . import session
from . import subagent
from . import todos
from .ui import ui

COMMANDS = {
    "/rewind": "jump back to an earlier point in this chat",
    "/sessions": "open a past chat",
    "/compact": "summarise the history so far and free up the context window",
    "/memory": "list what the agent remembers across sessions",
    "/mcp": "list the MCP servers, whether each started, and the tools they added",
    "/hooks": "list the hooks configured for each event",
    "/plan": "plan mode: read-only tools until you approve a plan",
    "/act": "act mode: every tool, the default",
    "/jobs": "list the background jobs and whether each is still running",
    "/init": "survey the project with a subagent and write AGENTS.md",
    "/instructions": "list the instruction files in the system prompt",
    "/exit": "leave (so do /quit, ctrl-d, ctrl-z then enter on Windows, and ctrl-c at the prompt)",
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
plainly what you could not find. Markdown, under 400 words, no preamble:
the report is written to the file as it is.
"""


def preview(message):
    if message.get("tool_calls"):
        return "-> " + message["tool_calls"][0]["function"]["name"]
    return " ".join(str(message.get("content") or "").split())[:70]


def redraw(messages, label):
    """The screen no longer matches the history, so wipe it and draw again.

    The todo list lives outside the transcript; it is rebuilt from the
    last write_todos call that the transcript still holds.
    """
    todos.from_transcript(messages)
    ui.clear()
    ui.banner(sandbox.name(), plan.MODE)
    ui.resumed(messages, label)
    ui.replay(messages)
    return messages


def turn_starts(messages):
    """The indexes of the user messages: the only places a transcript can be cut without orphaning a tool call."""
    return [i for i, m in enumerate(messages) if m.get("role") == "user" and isinstance(m.get("content"), str)]


def rewind(messages):
    """Cut the transcript before a user message the user picks: the turn it opened is forgotten."""
    starts = turn_starts(messages)
    rows = [f"turn {n + 1:<4} {preview(messages[i])}" for n, i in enumerate(starts)]
    choice = ui.pick("rewind to before", rows)
    if choice is None:
        return messages
    keep = starts[choice]
    session.rewind_to(keep)
    return redraw(messages[:keep], "rewound")


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
    history.strip(opened)  # its old tool output shrinks, the way --resume shrinks it
    return redraw(opened, "opened")


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


def hook_list(messages):
    """Every configured hook, grouped by event: its matcher and what it runs."""
    config = hooks.load_config()
    rows = [f"{event:<18} {hook.get('matcher') or '*':<24} {hooks.describe(hook)}" for event, found in config.items() for hook in found]
    ui.note("\n".join(rows) if rows else "no hooks configured (see .agents/hooks.json)")
    return messages


def job_list(messages):
    """One line per background job: id, state and command."""
    if not jobs.JOBS:
        ui.note("no background jobs in this session")
        return messages
    ui.note("\n".join(f"{job.id:<8} {job.state():<28} {job.command}" for job in jobs.JOBS.values()))
    return messages


def set_mode(messages, mode):
    """Switch between plan and act; the late block carries the mode from the next call on."""
    plan.set_mode(mode)
    if mode == "plan":
        ui.note("plan mode: the model reads and proposes; nothing is written until you approve a plan")
    else:
        ui.note("act mode: every tool is available")
    return messages


def init(messages):
    """Survey the project with a subagent; write the report to AGENTS.md on approval."""
    target = Path.cwd() / "AGENTS.md"
    report = subagent.task(INIT_QUESTION.strip())
    ui.agent(report)
    if report.startswith(subagent.STOPPED) or report.startswith("Error:"):
        ui.note("the subagent did not produce a guide; nothing written")
        return messages
    if not ui.confirm(f"write {target.name}" + (" (it exists; this replaces it)" if target.exists() else "")):
        ui.note("not written")
        return messages
    target.write_text(report.strip() + "\n", encoding="utf-8")
    if messages and messages[0].get("role") == "system":
        # discovery runs again, so the new file is in the prefix; a handoff note from a compaction stays at its end
        summary = compaction.previous_summary(messages[0]["content"])
        messages[0]["content"] = llm.build_system_prompt() + (f"\n\n{summary}" if summary else "")
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


def handle(command, messages):
    if command == "/init":
        return init(messages)
    if command == "/instructions":
        return instruction_list(messages)
    if command == "/plan":
        return set_mode(messages, "plan")
    if command == "/act":
        return set_mode(messages, "act")
    if command == "/hooks":
        return hook_list(messages)
    if command == "/jobs":
        return job_list(messages)
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
