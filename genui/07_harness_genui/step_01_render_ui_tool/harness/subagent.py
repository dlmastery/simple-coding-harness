"""Stage 15 - exploration subagents.

A task tool hands a self-contained exploration question to a fresh agent
that has its own context window. The subagent reuses call_llm: it takes a
list of messages and a tool set and returns one response.

Four rules, and the code below is really just these:

  1. it starts from an empty history           - none of the chat context
     the user had with the main agent is shared with the subagent
  2. it holds every tool but five              - task, write_todos,
     str_replace, write_file and render_ui are withheld; it reports, it does not draw
  3. it runs the same loop as the main agent   - call_llm, append, tools
  4. only its final message.content comes back - none of the subagent's
     tool calls ever return to the main agent
"""

import os

MAX_TURNS = 12  # a runaway explorer is worse than a missing answer

WITHHELD = {"task", "write_todos", "str_replace", "write_file", "render_ui"}

SYSTEM_PROMPT = f"""
You are an exploration subagent. You were given one question by a lead agent
and you answer it. That is the whole job.

You cannot see the conversation that spawned you, and the lead agent cannot
see anything you do here. Only your final message crosses back, so it has to
stand on its own.

You are working in {os.getcwd()}. Search inside it. Never search from / or
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


def toolset():
    """Every tool schema except the withheld ones."""
    from .tools import TOOL_SCHEMAS

    return [s for s in TOOL_SCHEMAS if s["function"]["name"] not in WITHHELD]


def task(description: str) -> str:
    """Run a fresh agent on one question and return only its final answer."""
    # Imported here, not at the top: tools imports us, and we need tools.
    from .history import fit
    from .llm import call_llm
    from .tools import execute
    from .ui import ui

    # rule 1: two messages, born here, dead at the return
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
    ui.subagent(description)
    report = None  # newest thing it has said, kept in case we run out of turns

    # rule 3: the loop from agent.py, pointed at a different list
    for _ in range(MAX_TURNS):
        fit(messages)  # its context can overflow too, and nobody compacts it

        with ui.working("subagent exploring"):
            message, usage = call_llm(messages, tools=toolset())  # rule 2
        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)
        report = message.content or report

        # rule 4: no tool calls means it has stopped looking and started answering
        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"

        for tool_call in message.tool_calls:
            # the same executor as the main loop: same permissions, same sandbox
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

    if report:
        return f"(stopped after {MAX_TURNS} turns, before finishing. Partial findings below.)\n\n{report}"
    return f"(stopped after {MAX_TURNS} turns with nothing to report.)"


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
            "and reports; it never edits. Do your own editing."
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
                }
            },
            "required": ["description"],
        },
    },
}
