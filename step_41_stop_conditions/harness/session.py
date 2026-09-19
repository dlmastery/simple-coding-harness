"""Step 40 - a handoff is an entry in the log: {"handoff": name}. handoff()
appends one when the active agent changes, and load() applies it in place
by rewriting the system message to that agent's prompt, so --resume comes
back with the agent that was answering when the session ended. Listing
the sessions applies nothing: all_sessions() reads titles from the raw
lines, and open_session() starts from the default agent before it
replays a log, so the agent of one chat never leaks into another.
The rest is step 39: the approval mode is an entry in the log too,
{"mode": name}, and stage 15 - session, unchanged since stage 14.

ENABLED turns the log off: a headless `-p` run writes no session file
unless it was asked to resume one.
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = Path.home() / ".simple-harness" / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many messages are already on disk
ENABLED = True  # False: nothing is written (a headless run that was not asked to resume)
NL = "\n"


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def append(entry):
    """One JSON line at the end of the current log."""
    if not ENABLED:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + NL)


def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN
    for message in messages[WRITTEN:]:
        append(message)
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    append({"rewind_to": count})
    WRITTEN = count


def mode(name):
    """Record that the approval mode is `name` from here on."""
    append({"mode": name})


def handoff(name):
    """Record that `name` answers from here on. The system message on disk stays; load() rewrites it."""
    append({"handoff": name})


def compacted(messages):
    """Compaction rewrites history, so record the result and start from it."""
    global WRITTEN
    append({"compacted": messages})
    WRITTEN = len(messages)


def load(session_id):
    """Replay the log: messages accumulate, rewinds cut them back, a compaction replaces them, a mode entry sets the mode, a handoff rewrites the prompt."""
    from . import handoff as handoffs  # here, not at the top: handoff imports llm, which imports modules that import session
    from . import modes

    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written last line from a kill mid-save
        if not isinstance(entry, dict):
            continue
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
        if message.get("role") == "user":
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
