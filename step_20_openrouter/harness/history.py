"""Stage 15 - keeping the transcript small enough to send.

Tool call output is the main reason a transcript explodes. Three
mechanisms, cheapest first. Only the first two live here; the expensive one
(the compaction agent) is compact.py.

1. cap    a fresh tool result is trimmed at 10,000 characters and the full
          text parked in a temp file the agent can page through with head,
          tail, sed or grep. The file lives only until the turn ends; then
          it is deleted.
2. strip  once a turn is over, its tool results shrink to a stub. Strip
          touches past turns only. The edit lands at the tail, so the
          cached prefix in front of it survives.
3. fit    a single request is still too big: throw tool results away whole,
          oldest first, until it fits. The panic button.
"""

import json
import tempfile
from pathlib import Path

from . import config

CAP = 10_000  # chars of a fresh tool result the agent sees inline
STUB = 300    # chars kept once the turn that produced it is over

TRIMMED = "[output trimmed:"  # marker, so stripping twice is a no-op
SUMMARY = "<summary>"         # marks the handoff note compaction leaves in the system prompt
SPILLS = []                   # temp files belonging to the current turn


# --- 1. cap ------------------------------------------------------------------


def spill(text):
    """Park the full output on disk for the rest of this turn."""
    handle = tempfile.NamedTemporaryFile(mode="w", prefix="harness-", suffix=".txt", delete=False, encoding="utf-8")
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


# --- 2. strip ----------------------------------------------------------------


def strip(messages):
    """Shrink every tool result from finished turns. Returns how many shrank.

    Called after a turn ends, so "everything in the list" and "everything the
    model no longer needs in full" are the same set.
    """
    shrunk = 0
    for message in messages:
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
    for message in messages:
        if estimate(messages) <= budget:
            break
        if message["role"] == "tool" and TRIMMED not in (message.get("content") or ""):
            message["content"] = f"{TRIMMED} dropped to fit the context window.]"
            dropped += 1
    return dropped
