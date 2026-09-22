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
is step 39: the approval mode is an entry in the log too, {"mode": name},
replayed the same way; and step 34: load() no longer writes a stand-in
result for a tool call the log left hanging: agent.recover() runs the call
instead, so a resumed chat gets the real result. repair() stays for ctrl-c
mid-turn.
"""

import json
import time
from datetime import datetime
from pathlib import Path

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = Path.home() / ".simple-harness" / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many messages are already on disk
PERSIST = True  # False in print mode: one-off runs leave no session behind

clock = time.time  # the stamp on every entry; a name the tests can replace


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def stamped(entry):
    """The entry with `ts` added, as one JSON line. The dict passed in is not touched."""
    return json.dumps({**entry, "ts": round(clock(), 3)}) + "\n"


def save(messages, usage=None, seconds=None, cost=None):
    """Append what is new. Never rewrite what is already on disk.

    With `usage`, one more entry follows the messages: the usage of the
    model call that produced the last one, keyed by its index, with the
    seconds the call took and what it cost. The message keeps the shape
    the model saw; the numbers live in the entry next to it.
    """
    global WRITTEN
    if not PERSIST:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(stamped(message))
        if usage is not None:
            f.write(stamped({"usage": usage, "index": len(messages) - 1, "seconds": seconds, "cost": cost}))
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    if not PERSIST:
        WRITTEN = count
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(stamped({"rewind_to": count}))
    WRITTEN = count


def mode(name):
    """Record that the approval mode is `name` from here on."""
    if not PERSIST:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(stamped({"mode": name}))


def handoff(name):
    """Record that `name` answers from here on. The system message on disk stays; load() rewrites it."""
    if not PERSIST:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(stamped({"handoff": name}))


def compacted(messages):
    """Compaction rewrites history, so record the result and start from it."""
    global WRITTEN
    if not PERSIST:
        WRITTEN = len(messages)
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(stamped({"compacted": messages}))
    WRITTEN = len(messages)


def repair(messages, note):
    """Answer every tool call in the last reply that has no result. Returns how many.

    A crash or ctrl-c between a reply and its tool results leaves a transcript
    the API refuses; a placeholder result per unanswered call makes it valid.
    The loop calls this on ctrl-c. load() does not: agent.recover() runs the
    hanging calls of a resumed chat instead, so the model gets real results.
    """
    last = next((m for m in reversed(messages) if m["role"] != "tool"), None)
    if not last or last["role"] != "assistant" or not last.get("tool_calls"):
        return 0
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    missing = [call["id"] for call in last["tool_calls"] if call["id"] not in answered]
    for call_id in missing:
        messages.append({"role": "tool", "tool_call_id": call_id, "content": note})
    return len(missing)


def load(session_id):
    """Replay the log: messages accumulate, rewinds cut them back, a compaction replaces them, a mode entry sets the mode, a handoff rewrites the prompt.

    The stamps and the usage entries are for replay and trace; the model
    never sees them. `ts` comes off every message and a usage entry is
    skipped, so the list is the same one the model read.
    """
    from . import modes  # here, not at the top: modes imports plan, which imports todos
    from . import handoff as handoffs  # here too: handoff imports llm, which imports modules that import session

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
        elif "mode" in entry:
            try:
                modes.set_mode(entry["mode"], log=False)
            except ValueError:
                pass  # a mode this version does not know: the session loads in the mode it has
        elif "handoff" in entry:
            try:
                handoffs.apply(entry["handoff"], messages)
            except KeyError:
                pass  # the definition file is gone; the transcript loads with the agent it had before
        else:
            messages.append(entry)
    return messages


def open_session(session_id):
    """Switch to a past chat and become it, starting from the default agent."""
    global CURRENT, WRITTEN
    from . import handoff as handoffs

    handoffs.reset()  # a chat without a handoff marker is the default agent's, whatever the last chat was
    CURRENT = session_id
    messages = load(session_id)
    WRITTEN = len(messages)
    return messages


def title(messages):
    for message in messages:
        if message["role"] == "user":
            return " ".join(str(message.get("content") or "").split())[:60]
    return "(empty)"


def all_sessions():
    """Newest first. The titles come from the raw lines: nothing in the log is applied here."""
    if not SESSION_DIR.exists():
        return []
    files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"id": p.stem, "title": title(raw_messages(p))} for p in files]


def raw_messages(path):
    """The message entries of a log as they are on disk, for a title: no rewind, mode, handoff or compaction applied."""
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and "role" in entry:
            found.append(entry)
    return found
