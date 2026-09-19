"""Step 44 - every entry on disk carries `ts`, the time it was written,
and an assistant message is followed by a usage entry:
{"usage": {...}, "index": N, "ts": ..., "seconds": ..., "cost": ...}.
The message itself is written as the model saw it, so the shape the
model reads never changes; load() drops `ts` from every message and
skips the usage entries, so a resumed transcript is the same list as
before. replay.py and trace.py read the stamps and the usage entries.
The rest is step 40: a handoff is an entry in the log: {"handoff": name}. handoff()
appends one when the active agent changes, and load() applies it in place
by rewriting the system message to that agent's prompt, so --resume comes
back with the agent that was answering when the session ended. The rest
is stage 15, unchanged since stage 14.
"""

import json
import time
from datetime import datetime
from pathlib import Path

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = Path.home() / ".simple-harness" / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many messages are already on disk
NL = "\n"

clock = time.time  # the stamp on every entry; a name the tests can replace


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def log(session_id=None):
    """The log file of a session, opened for appending; the directory is made on the way."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return path_for(CURRENT if session_id is None else session_id).open("a", encoding="utf-8")


def stamped(entry):
    """The entry with `ts` added, as one JSON line. The dict passed in is not touched."""
    return json.dumps({**entry, "ts": round(clock(), 3)}) + NL


def save(messages, usage=None, seconds=None, cost=None):
    """Append what is new. Never rewrite what is already on disk.

    With `usage`, one more entry follows the messages: the usage of the
    model call that produced the last one, keyed by its index, with the
    seconds the call took and what it cost. The message keeps the shape
    the model saw; the numbers live in the entry next to it.
    """
    global WRITTEN
    with log() as f:
        for message in messages[WRITTEN:]:
            f.write(stamped(message))
        if usage is not None:
            f.write(stamped({"usage": usage, "index": len(messages) - 1, "seconds": seconds, "cost": cost}))
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    with log() as f:
        f.write(stamped({"rewind_to": count}))
    WRITTEN = count


def handoff(name):
    """Record that `name` answers from here on. The system message on disk stays; load() rewrites it."""
    with log() as f:
        f.write(stamped({"handoff": name}))


def compacted(messages):
    """Compaction rewrites history, so record the result and start from it."""
    global WRITTEN
    with log() as f:
        f.write(stamped({"compacted": messages}))
    WRITTEN = len(messages)


def load(session_id, apply_handoffs=True):
    """Replay the log: messages accumulate, rewinds cut them back, a compaction replaces them, a handoff rewrites the prompt.

    The stamps and the usage entries are for replay and trace; the model
    never sees them. `ts` comes off every message and a usage entry is
    skipped, so the list is the same one the model read.

    A handoff marker rewrites the system prompt and makes that agent the
    active one - a global. With apply_handoffs=False the markers are
    skipped, for a reader that only wants the messages (a title, a
    replay) and must not change which agent answers the live chat.
    """
    from . import handoff as handoffs  # here, not at the top: handoff imports llm, which imports modules that import session

    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written last line from a kill mid-save
        entry.pop("ts", None)
        if "usage" in entry:
            continue  # the numbers of a model call: replay and trace read them, the model does not
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        elif "compacted" in entry:
            messages = list(entry["compacted"])
        elif "handoff" in entry:
            if not apply_handoffs:
                continue
            try:
                handoffs.apply(entry["handoff"], messages)
            except KeyError:
                pass  # the definition file is gone; the transcript loads with the agent it had before
        else:
            messages.append(entry)
    return messages


def open_session(session_id):
    """Switch to a past chat and become it: the default agent first, then whatever the log hands off to."""
    from . import handoff as handoffs  # here, not at the top: see load()

    global CURRENT, WRITTEN
    CURRENT = session_id
    handoffs.reset()
    messages = load(session_id)
    WRITTEN = len(messages)
    return messages


def title(messages):
    for message in messages:
        if message["role"] == "user":
            return " ".join(str(message.get("content") or "").split())[:60]
    return "(empty)"


def all_sessions():
    """Newest first."""
    if not SESSION_DIR.exists():
        return []
    files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"id": p.stem, "title": title(load(p.stem, apply_handoffs=False))} for p in files]  # a listing changes no agent
