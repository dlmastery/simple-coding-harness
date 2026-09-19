"""Step 24 - keeping the transcript small enough to send, pictures included.

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

A fourth piece, images: a tool result that carries a `[[image:PATH]]` marker
asks the loop to show the model that PNG. image_message() builds the user
message that does it. strip() shrinks those messages to a line of text once
the turn is over, the same as any other tool output.
"""

import base64
import json
import re
import tempfile
from pathlib import Path

from . import config

CAP = 10_000  # chars of a fresh tool result the agent sees inline
STUB = 300    # chars kept once the turn that produced it is over

CAPPED = "[output capped:"    # marker cap() leaves: the whole text is on disk for this turn
TRIMMED = "[output trimmed:"  # marker strip() and fit() leave: the rest is gone for good; stripping twice is a no-op
IMAGE = re.compile(r"\[\[image:(.+?)\]\]")  # marker a tool result carries when it made a picture
IMAGE_TOKENS = 1_500          # what one picture costs, whatever its byte size
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
        return text[:CAP] + f"\n\n{CAPPED} {len(text) - CAP} chars cut and could not be saved.]"
    return (
        text[:CAP] + f"\n\n{CAPPED} {len(text) - CAP} of {len(text)} chars cut. "
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
        if isinstance(content, list):  # an image message: keep its caption, drop the picture
            message["content"] = f"[{caption_of(content)} - no longer shown]"
            shrunk += 1
            continue
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
    """Rough token count - good enough to decide whether to panic.

    A picture is counted flat, because the model bills it by size on screen,
    not by the length of its base64 text.
    """
    total = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            total += IMAGE_TOKENS * sum(1 for part in content if part.get("type") == "image_url")
            total += sum(len(part.get("text", "")) for part in content) // 4
        else:
            total += len(json.dumps(message)) // 4
    return total


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


# --- 4. images ---------------------------------------------------------------


def split_images(result):
    """Take the image markers out of a tool result. Returns (clean text, paths)."""
    paths = IMAGE.findall(result)
    if not paths:
        return result, []
    return IMAGE.sub("", result).strip(), paths


def image_message(path, caption):
    """A user message that shows the model one PNG next to a line of text.

    The chat completions API takes a picture as an image_url part; a data URL
    keeps the file out of any server. The caption says which tool made it.
    """
    try:
        data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    except OSError as failed:  # a marker whose file is gone: say so, keep the loop alive
        return {"role": "user", "content": f"[{caption}: the image at {path} could not be read: {failed}]"}
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": caption},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}},
        ],
    }


def caption_of(content):
    """The text parts of a list-shaped message content, joined."""
    return " ".join(part.get("text", "") for part in content if part.get("type") == "text").strip()
