"""Subagents: exploration that happens somewhere else.

A subagent is a whole agent loop with its own message list. That list is
never shown to the main agent and never outlives the call. The only thing
that crosses back is the final report.

It is compact.py's idea from the other end. Exploring a repo burns tens of
thousands of tokens of tool output to produce a few hundred tokens of
answer. Compaction throws context away after it has been spent; a subagent
spends it somewhere that is thrown away by design, so the main transcript
never pays for it at all.

Four rules, and the code below is really just these:

  1. it starts from an empty history          (no memory of anything)
  2. it holds every tool but a few            (no recursion, no plan edits)
  3. it runs the same loop as the main agent  (nothing special happens here)
  4. only its last message comes back         (the rest is discarded)
"""

import os

MAX_TURNS = 12  # a runaway explorer is worse than a missing answer

# Rule 2. `task` would let a subagent spawn subagents forever. `write_todos`
# writes the main agent's plan, and this is a guest in someone else's session.
# The editing tools are withheld so "read-only" is a fact, not a request.
WITHHELD = {"task", "write_todos", "write_file", "str_replace"}

SUBAGENT_PROMPT = f"""You are an exploration subagent. A lead agent gave you one question and you
answer it. That is the whole job.

You cannot see the conversation that spawned you, and the lead agent cannot
see anything you do here. Only your final message crosses back, so it must
stand on its own.

You are working in {os.getcwd()}. Search inside it. Never search from / or
the home directory - that scans the whole machine and times out.

How to work:
- Use bash, read_file and read_skill to find out what is actually true.
  Prefer rg, grep and find to guessing where things live.
- You read and report. You cannot write or edit files.
- Search in batches: several greps in one turn beat one grep per turn.
- Stop as soon as you can answer. Do not keep looking to be thorough.

Your final message is the entire report and the only thing that costs the
lead agent anything, so keep it short - under 150 words. Findings only:
paths with line numbers, names, values. Say plainly what you could not
find; a gap is useful, a guess is not."""


def toolset():
    """Every tool schema except the withheld ones."""
    from .tools import TOOL_SCHEMAS

    return [s for s in TOOL_SCHEMAS if s["function"]["name"] not in WITHHELD]


def task(description: str) -> str:
    """Run a fresh agent on one question and return only its final answer."""
    # Imported here, not at the top: tools imports us, and we need tools.
    from . import llm
    from .agent import as_dict
    from .history import fit
    from .tools import execute
    from .ui import ui

    # Rule 1: two messages. Not a copy of the caller's transcript - a list
    # born here that dies at the return statement.
    messages = [
        {"role": "system", "content": SUBAGENT_PROMPT},
        {"role": "user", "content": description},
    ]
    ui.subagent(description)
    report = None  # newest thing it said, in case we run out of turns

    # Rule 3: compare with turn() in agent.py. Call, append, run tools,
    # append, repeat. A subagent is the loop you already have, pointed at a
    # different list.
    for _ in range(MAX_TURNS):
        fit(messages)  # its context can overflow too, and nobody compacts it

        with ui.working("subagent exploring"):
            message, usage = llm.complete(messages, tools=toolset())
        messages.append(as_dict(message))
        ui.usage(usage)
        report = message.content or report

        # Rule 4: no tool calls means it has stopped looking and started
        # answering. `messages` goes out of scope here - every tool result,
        # every path explored - and one string comes back.
        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"

        for call in message.tool_calls:
            # Same executor as the main loop: same permission rules, same
            # sandbox. A subagent is a second caller, not a privileged one.
            args, result = execute(call)
            ui.tool(call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    if report:
        return f"(stopped after {MAX_TURNS} turns before finishing. Partial findings:)\n\n{report}"
    return f"(stopped after {MAX_TURNS} turns with nothing to report.)"


TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Hand a self-contained exploration question to a fresh agent with "
            "its own context window and get back its findings. Use it to learn "
            "how the codebase works - where something is implemented, how data "
            "flows, what calls what - so the search costs you one answer instead "
            "of dozens of tool results. It cannot see this conversation, so "
            "include every detail it needs. It reads and reports; it cannot edit."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": (
                        "The question, written to stand alone: what to find out, "
                        "where to start looking, what the answer should contain."
                    ),
                }
            },
            "required": ["description"],
        },
    },
}
