"""Step 25 - the compaction agent, and its note is now kept.

When the prompt reaches 85% of the context window, the harness cuts it back
to 35%. It does not drop the oldest messages, because that would break the
KV cache. Instead it compacts: a summary of everything that happened in the
session replaces the messages about to be deleted.

A second agent with one job and no tools writes that handoff note. The note
is folded into the system prompt. The transcript then has to fill from 35%
back to 85% before the next compaction, so the system prompt stays the same
in between and the cached prefix survives.

The same note is saved as a memory named handoff-<session id>, so the next
session can recall where this one left off.
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


LAST_SIZE = 0  # how many messages the transcript had when compaction last ran


def needed(usage, messages=None):
    """Has the last request grown past the point where we rebuild?

    Not twice for the same transcript: when compaction found nothing old
    enough to fold, the next turn must add messages before it is tried again.
    """
    if (usage.get("prompt_tokens") or 0) <= config.CONTEXT_WINDOW * config.COMPACT_AT:
        return False
    return messages is None or len(messages) != LAST_SIZE


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
    if not message.content:
        raise RuntimeError("the summariser returned nothing")  # keep the transcript rather than replace it with a blank
    return message.content


def safe_boundary(messages, start):
    """First index at or after `start` where cutting cannot orphan a tool call.

    A tool result has to keep the assistant message that asked for it, and an
    assistant message its user message, so the only safe cut points are the
    user messages that open a fresh exchange. An image message is a user
    message too, but it belongs to the tool result before it, so it is not
    a cut point.
    """
    for index in range(max(start, 1), len(messages)):
        if messages[index]["role"] == "user" and not isinstance(messages[index].get("content"), list):
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


def remember_handoff(summary):
    """Save the handoff note as the project memory handoff-latest, replacing the last one."""
    return memory.remember(
        "handoff-latest",
        f"handoff note from session {session.CURRENT}",
        summary,
        type="project",
    )


def compact(messages):
    """[system + summary, ...recent tail]. Unchanged if nothing is old enough."""
    global LAST_SIZE
    LAST_SIZE = len(messages)
    cut = tail_start(messages, config.CONTEXT_WINDOW * config.COMPACT_TO)
    if cut <= 1:
        return messages

    system = messages[0]["content"]
    summary = summarize(messages[1:cut], previous_summary(system))
    remember_handoff(summary)  # the next session can recall it
    kept = [
        {"role": "system", "content": base_prompt(system) + "\n\n" + HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now, while the prefix is already rebuilt
    return kept
