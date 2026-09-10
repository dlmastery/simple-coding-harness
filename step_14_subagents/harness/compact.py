"""The compaction agent: a second model call with one job.

Read a transcript that has grown too big and write the handoff note a fresh
agent would need to carry on. The note replaces the messages it summarised.
This is the only place in the harness that throws information away for
good, so it runs rarely and cuts deep: trimming just enough to fit would put
us back over the line next turn, and every rebuild costs the prompt cache.

After compaction the list is:  [system, <summary>, ...recent tail...]
and history.locked() treats the first two as frozen.
"""

from . import config, llm
from .history import SUMMARY, estimate, strip

COMPACT_PROMPT = """You are compacting the transcript of a coding session that has run out of
context window. Write the handoff note that lets a fresh agent pick the work
up without re-reading anything.

Use these sections, in this order. Skip any that would be empty.

## Goal
What the user asked for. Quote them where the exact wording matters.

## What happened
Decisions taken and why. Include approaches that were tried and abandoned -
an agent without them will try the same dead end again.

## Files
Every file touched: path, and what changed in it.

## State
What works, what is broken, what is half-finished.

## Next
The immediate next step.

Rules: be specific (real paths, names, error text, commands). Keep anything
the user explicitly asked for, corrected or rejected. Never invent progress.
No preamble, no sign-off - start at the first heading."""

HANDOFF = SUMMARY + """
Everything before this point was compacted out of the context window. This
is the record of it - treat it as your own memory of the work so far, not
as something the user told you.

{summary}
</summary>"""

ROLES = {"user": "USER", "assistant": "ASSISTANT", "tool": "TOOL RESULT"}


def needed(usage):
    """Has the last request grown past the point where we rebuild?"""
    return (usage.get("prompt_tokens") or 0) > config.CONTEXT_WINDOW * config.COMPACT_AT


def render(messages):
    """Flatten the transcript into text the summariser can read."""
    lines = []
    for message in messages:
        if message["role"] == "system":
            continue
        content = message.get("content") or ""
        for call in message.get("tool_calls") or []:
            content += f"\n[called {call['function']['name']}: {call['function']['arguments']}]"
        lines.append(f"{ROLES.get(message['role'], message['role'])}: {content}")
    return "\n\n".join(lines)


def summarize(messages):
    """One model call, no tools. Returns the handoff note."""
    message, _ = llm.complete(
        [{"role": "system", "content": COMPACT_PROMPT}, {"role": "user", "content": render(messages)}],
        tools=[],
    )
    return message.content or "(the summariser returned nothing)"


def safe_boundary(messages, start):
    """First index at or after `start` where a cut cannot orphan a tool call.

    A tool result must keep the assistant message that asked for it, so the
    only safe cut points are messages that open a fresh exchange.
    """
    for index in range(max(start, 1), len(messages)):
        if messages[index]["role"] == "tool" or messages[index - 1].get("tool_calls"):
            continue
        return index
    return len(messages)


def tail_start(messages, budget):
    """Walk back from the end, keeping messages until the tail fills `budget`."""
    total = 0
    for index in range(len(messages) - 1, 0, -1):
        total += estimate([messages[index]])
        if total > budget:
            return safe_boundary(messages, index)
    return safe_boundary(messages, 1)


def compact(messages):
    """Return [system, summary, recent tail]. Unchanged if nothing is old enough."""
    cut = tail_start(messages, config.CONTEXT_WINDOW * config.COMPACT_TO)
    if cut <= 1:
        return messages

    summary = summarize(messages[1:cut])
    kept = [
        messages[0],
        {"role": "user", "content": HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now while the prefix is already rebuilt
    return kept
