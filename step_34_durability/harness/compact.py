"""Step 34 - a summariser call that failed after every retry raises, so
the caller keeps the transcript as it is; an empty note is never folded
into the prompt. The rest is step 25: the compaction agent, and its note
is kept.

When the prompt reaches 85% of the context window, the harness cuts it back
to 35%. It does not drop the oldest messages, because that would break the
KV cache. Instead it compacts: a summary of everything that happened in the
session replaces the messages about to be deleted.

A second agent with one job and no tools writes that handoff note. The note
is folded into the system prompt. The transcript then has to fill from 35%
back to 85% before the next compaction, so the system prompt stays the same
in between and the cached prefix survives.

The same note is saved as one project memory, handoff-latest, so the next
session can recall where the last one left off. One memory, not one per
session: the index goes to the model on every call, and it must stay short.
"""

import re

from . import config, llm, memory, session
from .history import SUMMARY, caption_of, estimate, strip

SYSTEM_PROMPT = """
You are compacting the transcript of a coding session. The session is out of
context window. Write the handoff note that lets a fresh agent pick the work up
without re-reading anything.

Use these sections, in this order. Skip any that would be empty.

## Goal
What the user asked for. Quote them where the exact wording matters.

## What happened
Decisions taken and the reasoning behind them. Include approaches that were
tried and abandoned, and why - those are the expensive lessons, and an agent
without them will try the same dead end again.

## Files
Every file touched: path, and what changed in it.

## State
What works, what is broken, what was left half-finished.

## Next
The immediate next step.

Rules:
- Be specific. Real paths, function names, error text, exact commands.
- Keep anything the user explicitly asked for, corrected, or rejected.
- Never invent progress. If something was not finished, say it was not.
- No preamble and no sign-off. Start at the first heading.
"""

HANDOFF = SUMMARY + """
Everything before this point has been compacted out of the context window to
free up room. This is the record of it - treat it as your own memory of the
work so far, not as something the user told you.

{summary}
</summary>"""

SUMMARY_BLOCK = re.compile(r"\n*<summary>.*?</summary>", re.S)
ROLES = {"user": "USER", "assistant": "ASSISTANT", "tool": "TOOL RESULT"}


LAST_SIZE = 0  # how long the transcript was when compaction last ran (or found nothing to do)


def needed(usage, messages):
    """Has the last request grown past the point where we rebuild?

    Once compaction has run - or found nothing old enough - it does not fire
    again until the transcript has grown, so one big prompt does not trigger
    it on every turn.
    """
    full = (usage.get("prompt_tokens") or 0) > config.CONTEXT_WINDOW * config.COMPACT_AT
    return full and len(messages) > LAST_SIZE


def previous_summary(system_content):
    """The handoff note a previous compaction left in the system prompt, if any."""
    match = SUMMARY_BLOCK.search(system_content)
    return match.group(0).strip() if match else ""


def base_prompt(system_content):
    """The system prompt without any earlier handoff note."""
    return SUMMARY_BLOCK.sub("", system_content).rstrip()


def render(messages, previous=""):
    """Flatten the transcript into something the summariser can read."""
    lines = []
    if previous:
        lines.append(f"PREVIOUS HANDOFF NOTE (carry forward what still matters):\n{previous}")
    for message in messages:
        if message["role"] == "system":
            continue
        content = message.get("content") or ""
        if isinstance(content, list):  # an image message: the caption stands in for the picture
            content = f"[{caption_of(content)}]"
        for call in message.get("tool_calls") or []:
            function = call["function"]
            content += f"\n[called {function['name']}: {function['arguments']}]"
        lines.append(f"{ROLES.get(message['role'], message['role'])}: {content}")
    return "\n\n".join(lines)


def summarize(messages, previous=""):
    """One model call, no tools. Returns the handoff note."""
    message, _ = llm.call_llm(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": render(messages, previous)}],
        tools=[],
    )
    if getattr(message, "failed", None) or not message.content:
        # never fold an empty note into the prompt: the caller keeps the transcript as it is
        raise RuntimeError(getattr(message, "failed", None) or "the summariser returned nothing")
    return message.content


def safe_boundary(messages, start):
    """First index at or after `start` where cutting cannot orphan a tool call.

    A tool result has to keep the assistant message that asked for it, so the
    only safe cut points are user messages: they open a fresh exchange.
    """
    for index in range(max(start, 1), len(messages)):
        if messages[index]["role"] == "user":
            return index
    return len(messages)


def tail_start(messages, budget):
    """Walk back from the end, taking messages until the tail fills `budget`."""
    total = 0
    for index in range(len(messages) - 1, 0, -1):
        total += estimate([messages[index]])
        if total > budget:
            return safe_boundary(messages, index)
    return safe_boundary(messages, 1)


HANDOFF_MEMORY = "handoff-latest"  # one note, overwritten: the index must not grow by one per session


def remember_handoff(summary):
    """Save the handoff note as the project's handoff-latest memory."""
    goal = next((line.strip() for line in summary.splitlines() if line.strip() and not line.startswith("#")), "")
    return memory.remember(
        HANDOFF_MEMORY,
        f"where session {session.CURRENT} left off: {goal[:80]}" if goal else f"where session {session.CURRENT} left off",
        summary,
        type="project",
    )


def compact(messages):
    """[system + summary, ...recent tail]. Unchanged if nothing is old enough."""
    global LAST_SIZE
    cut = tail_start(messages, config.CONTEXT_WINDOW * config.COMPACT_TO)
    if cut <= 1:
        LAST_SIZE = len(messages)  # nothing to do yet: do not ask again until it grows
        return messages

    system = messages[0]["content"]
    summary = summarize(messages[1:cut], previous_summary(system))
    remember_handoff(summary)  # the next session can recall it
    kept = [
        {"role": "system", "content": base_prompt(system) + "\n\n" + HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now, while the prefix is already rebuilt
    LAST_SIZE = len(kept)
    return kept
