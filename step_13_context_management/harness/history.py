"""Keeping the transcript small enough to send. Three mechanisms, cheapest first.

1. cap    a fresh tool result is trimmed and the full text parked in a temp
          file the model can page through. Decided once, when the result is
          born, so it never edits anything already sent.
2. strip  once a turn is over, its tool results shrink to a stub. The edit
          lands at the tail, right before the next user message, so the
          cached prefix in front of it survives.
3. fit    a single request is still too big: throw tool results away whole,
          oldest first, until it fits. The panic button.

The expensive fourth mechanism - compaction - is in compact.py.

Everything here refuses to touch the *locked prefix*: system prompt plus the
newest compaction summary. That block must stay byte-identical to stay
cached.
"""

import json
import tempfile
from pathlib import Path

from . import config

CAP = 10_000  # chars of a fresh tool result the model sees inline
STUB = 300    # chars kept once the turn that produced it is over

TRIMMED = "[output trimmed:"  # marker, so stripping twice is a no-op
SUMMARY = "<summary>"         # marks the handoff note compaction leaves behind
SPILLS = []                   # temp files belonging to the current turn


# --- 1. cap ------------------------------------------------------------------


def spill(text):
    """Park the full output on disk for the rest of this turn."""
    handle = tempfile.NamedTemporaryFile(
        mode="w", prefix="harness-", suffix=".txt", delete=False, encoding="utf-8"
    )
    handle.write(text)
    handle.close()
    SPILLS.append(Path(handle.name))
    return handle.name


def cap(text):
    """Trim a fresh tool result, leaving a pointer to the whole thing."""
    if len(text) <= CAP:
        return text
    try:
        path = spill(text)
    except OSError:
        return text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} chars cut and could not be saved.]"
    return (
        text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} of {len(text)} chars cut. "
        f"The whole output is at {path} - page through it with head, tail, "
        "sed -n or grep. It is deleted when this turn ends.]"
    )


def sweep():
    """Delete this turn's temp files. Their paths die with the tool results."""
    for path in SPILLS:
        path.unlink(missing_ok=True)
    SPILLS.clear()


# --- the locked prefix -------------------------------------------------------


def locked(messages):
    """Length of the frozen prefix: up to and including the newest summary.

    Derived rather than remembered, so it stays right across /compact,
    /rewind and switching sessions.
    """
    for index in range(len(messages) - 1, -1, -1):
        if SUMMARY in (messages[index].get("content") or ""):
            return index + 1
    return 0


# --- 2. strip ----------------------------------------------------------------


def strip(messages):
    """Shrink every tool result that is no longer part of the live turn.

    Called after a turn ends, so "everything unlocked" and "everything the
    model no longer needs in full" are the same set. Returns how many shrank.
    """
    shrunk = 0
    for message in messages[locked(messages):]:
        content = message.get("content") or ""
        if message["role"] != "tool" or TRIMMED in content or len(content) <= STUB:
            continue
        message["content"] = (
            content[:STUB] + f"\n\n{TRIMMED} {len(content) - STUB} more chars. "
            "Run the command again if you need them.]"
        )
        shrunk += 1
    return shrunk


# --- 3. fit ------------------------------------------------------------------


def estimate(messages):
    """Rough token count - good enough to decide whether to panic."""
    return sum(len(json.dumps(m)) for m in messages) // 4


def fit(messages):
    """Last resort: discard whole tool results, oldest first, until it fits."""
    budget = config.CONTEXT_WINDOW * config.COMPACT_AT
    dropped = 0
    for message in messages[locked(messages):]:
        if estimate(messages) <= budget:
            break
        if message["role"] == "tool" and TRIMMED not in (message.get("content") or ""):
            message["content"] = f"{TRIMMED} dropped to fit the context window.]"
            dropped += 1
    return dropped
