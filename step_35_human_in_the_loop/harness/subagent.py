"""Step 35 - ask_user is withheld from subagents: a subagent cannot see the
conversation, so a question to the user goes through the lead agent.
Withheld means denied: loop() hands execute_all the names it offered, and
a call to any other name comes back as Blocked by policy. The rest is
unchanged. Step 34: a subagent whose model call fails after every
retry returns the reason as its report, so the main agent reads what
happened. Step 32: the subagent tool set goes through active_schemas(), so
a deferred tool is a stub for a subagent too, and load_tool comes with it.
Step 30: the subagent prompt names the working directory of the call, not
of the import, so a subagent started by the eval runner searches the task
workspace, and the task tool can run several subagents at once.

A task tool hands a self-contained exploration question to a fresh agent
that has its own context window. The subagent reuses call_llm: it takes a
list of messages and a tool set and returns one response.

Four rules, and the code below is really just these:

  1. it starts from an empty history           - none of the chat context
     the user had with the main agent is shared with the subagent
  2. it holds every tool but a few             - task, browse, write_todos,
     str_replace, write_file, ask_user, the job, memory and computer tools
     are withheld; no recursion, one subagent deep, and no process that
     outlives the report. Withheld means denied, not just not offered.
  3. it runs the same loop as the main agent   - call_llm, append, execute_all,
     and a tool result that carries an image marker becomes an image message
  4. only its final message.content comes back - none of the subagent's
     tool calls ever return to the main agent

The loop itself is loop(): a system prompt, a request, a tool set and a turn
cap. task() is one way to call it; browse.py is another.

New in this step: task(descriptions=[...]) runs one loop per description on
a thread pool, MAX_PARALLEL at a time. Each loop owns its message list, so
nothing is shared but the tool registry, which was already built for
threads in step 22. The nested panels carry the subagent's number, and the
reports come back joined, one header per subagent, in the order given.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext

MAX_TURNS = 12     # a runaway explorer is worse than a missing answer
MAX_PARALLEL = 4   # subagents of one task call that run at the same time

WITHHELD = {
    "task", "browse", "write_todos", "str_replace", "write_file", "bash_background", "job_status", "job_wait", "job_kill",
    "ask_user", "computer_act", "computer_screenshot", "remember", "forget", "handoff_to", "finish",
}

def build_system_prompt(cwd=None):
    """The subagent prompt for one working directory. Default: the current one."""
    cwd = cwd or os.getcwd()
    return f"""
You are an exploration subagent. You were given one question by a lead agent
and you answer it. That is the whole job.

You cannot see the conversation that spawned you, and the lead agent cannot
see anything you do here. Only your final message crosses back, so it has to
stand on its own.

You are working in {cwd}. Search inside it. Never search from / or
from the home directory - that scans the whole machine and will time out.

How to work:
- Use bash, read_file and read_skill to find out what is actually true.
  Prefer rg, grep and find to guess at where things live.
- You are here to read and report, not to change anything.
- Search in batches. Several greps in one turn beats one grep per turn.
- Stop as soon as you can answer. Do not keep looking to be thorough.

Your final message is the entire report, and it is the only thing that costs
the lead agent anything - so keep it short. Aim for under 150 words. Findings
only: file paths with line numbers, names, values. Say plainly what you could
not find; a gap is useful, a guess is not.
"""


SYSTEM_PROMPT = build_system_prompt()


def toolset():
    """Every tool schema except the withheld ones, with the deferred ones as stubs."""
    from .tools import TOOL_SCHEMAS, active_schemas

    return active_schemas([s for s in TOOL_SCHEMAS if s["function"]["name"] not in WITHHELD])


def loop(system_prompt, request, tools, max_turns, label="subagent exploring", tag=None):
    """Run a fresh agent on one request and return only its final answer.

    tag is the subagent's number when several run at once. It goes on every
    panel, and it turns the spinner off: one live spinner per screen is the
    limit, and parallel loops would fight over it.
    """
    # Imported here, not at the top: tools imports us, and we need tools.
    from .history import fit, image_message, split_images
    from .llm import call_llm
    from .tools import execute_all
    from .ui import ui

    # rule 1: two messages, born here, dead at the return
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request},
    ]
    allowed = {schema["function"]["name"] for schema in tools} | {"load_tool"}  # rule 2, enforced: what was offered is what may run
    ui.subagent(request, tag=tag)
    report = None  # newest thing it has said, kept in case we run out of turns

    # rule 3: the loop from agent.py, pointed at a different list
    for _ in range(max_turns):
        fit(messages)  # its context can overflow too, and nobody compacts it

        with ui.working(label) if tag is None else nullcontext():
            message, usage = call_llm(messages, tools=tools)  # rule 2
        if getattr(message, "failed", None):
            return f"(the subagent stopped: {message.failed})"  # every retry failed; say so instead of "nothing"
        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)
        report = message.content or report

        # rule 4: no tool calls means it has stopped looking and started answering
        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"

        # the same executor as the main loop: same permissions, same sandbox, same pool;
        # a call to a tool that was not offered - task, write_file, an agent - is denied, not run
        outcomes = execute_all(message.tool_calls, allowed=allowed)
        pictures = []
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            result, paths = split_images(result)
            pictures += [(tool_call.function.name, path) for path in paths]
            ui.tool(tool_call.function.name, args, result, nested=True, tag=tag)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        for name, path in pictures:  # same expansion as agent.turn, after the last result
            messages.append(image_message(path, f"screenshot from tool {name}"))

    if report:
        return f"(stopped after {max_turns} turns, before finishing. Partial findings below.)\n\n{report}"
    return f"(stopped after {max_turns} turns with nothing to report.)"


def explore(description, tag=None):
    """One exploration subagent: every tool but the withheld ones, twelve turns."""
    return loop(build_system_prompt(), description, toolset(), MAX_TURNS, tag=tag)  # the cwd of this call, not of the import


def title(description):
    """The first line of a description, cut short, for a report header."""
    first = description.strip().splitlines()[0] if description.strip() else "(empty)"
    return first if len(first) <= 60 else first[:57] + "..."


def guarded(number, description):
    """explore(), but a crash becomes a report: one failure must not sink the others."""
    try:
        return explore(description, tag=number)
    except Exception as failure:  # noqa: BLE001
        return f"Error: subagent {number} failed with {type(failure).__name__}: {failure}"


def parallel(descriptions):
    """Run one subagent per description at the same time; join the reports in order."""
    pool = ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="subagent")
    futures = [pool.submit(guarded, number, description) for number, description in enumerate(descriptions, 1)]
    try:
        reports = [future.result() for future in futures]
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # a queued subagent never starts; a running one finishes alone
        raise
    pool.shutdown(wait=True)
    return "\n\n".join(
        f"## subagent {number}: {title(description)}\n\n{report}"
        for number, (description, report) in enumerate(zip(descriptions, reports), 1)
    )


def task(description: str = None, descriptions: list = None) -> str:
    """The exploration subagent, or several of them at once.

    One description runs one subagent and returns its report. A list of
    descriptions runs one subagent per item concurrently and returns the
    reports joined, one header per subagent, in the order of the list.
    """
    if descriptions:
        return parallel([str(d) for d in descriptions])
    if description:
        return explore(description)
    return "Error: give a description, or a list of descriptions to run several subagents at once."


TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Hand a self-contained exploration question to a fresh agent that "
            "has its own context window, and get back its findings. Use this "
            "to learn how the codebase works - tracing behaviour, locating "
            "where something is implemented, surveying files - so the search "
            "costs you one answer instead of dozens of tool results. It cannot "
            "see this conversation, so include every detail it needs. It reads "
            "and reports; it never edits. Do your own editing. Give one "
            "description for one question, or descriptions for several "
            "independent questions: each runs in its own subagent at the same "
            "time, and the reports come back together, one section each."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": (
                        "The question, written to stand alone: what to find "
                        "out, where to start looking, and what the answer "
                        "should contain."
                    ),
                },
                "descriptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Several stand-alone questions that do not depend on "
                        "each other. One subagent per item, run in parallel. "
                        "Use this instead of description, not with it."
                    ),
                },
            },
            # no top-level anyOf: the OpenAI API rejects one, and task() checks that one of the two came
        },
    },
}
