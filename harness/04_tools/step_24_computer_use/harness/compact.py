"""Step 24 - the compaction agent, which reads an image message by its caption.

When the prompt reaches 85% of the context window, the harness cuts it back
to 35%. It does not drop the oldest messages, because that would break the
KV cache. Instead it compacts: a summary of everything that happened in the
session replaces the messages about to be deleted.

A second agent with one job and no tools writes that handoff note. The note
is folded into the system prompt. The transcript then has to fill from 35%
back to 85% before the next compaction, so the system prompt stays the same
in between and the cached prefix survives.
"""

import re

from . import config, llm
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


COMPACTED_AT = 0  # how long the transcript was right after the last compaction


def needed(usage, messages):
    """Has the last request grown past the point where we rebuild?

    Never twice on the same transcript: if a compaction just happened and
    the prompt is still over the line, another one would only rewrite the
    system prompt again and throw the cache away for nothing.
    """
    over = (usage.get("prompt_tokens") or 0) > config.CONTEXT_WINDOW * config.COMPACT_AT
    return over and len(messages) > COMPACTED_AT


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
        raise RuntimeError("the summariser returned nothing")  # keep the transcript rather than replace it with nothing
    return message.content


def safe_boundary(messages, start):
    """First index at or after `start` where cutting cannot orphan a tool call.

    A tool result has to keep the assistant message that asked for it, and
    some providers refuse a transcript whose first message after the system
    prompt is not the user's, so the only safe cut points are user messages.
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


def compact(messages):
    """[system + summary, ...recent tail]. Unchanged if nothing is old enough."""
    global COMPACTED_AT
    # the system prompt, handoff note included, is part of every request: budget for it
    budget = config.CONTEXT_WINDOW * config.COMPACT_TO - estimate(messages[:1])
    cut = tail_start(messages, budget)
    if cut <= 1:
        return messages

    system = messages[0]["content"]
    summary = summarize(messages[1:cut], previous_summary(system))
    kept = [
        {"role": "system", "content": base_prompt(system) + "\n\n" + HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now, while the prefix is already rebuilt
    COMPACTED_AT = len(kept)
    return kept
