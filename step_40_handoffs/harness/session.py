"""Step 40 - a handoff is an entry in the log: {"handoff": name}. handoff()
appends one when the active agent changes, and load() applies it in place
by rewriting the system message to that agent's prompt, so --resume comes
back with the agent that was answering when the session ended. The rest
is stage 15, unchanged since stage 14.
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = Path.home() / ".simple-harness" / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many messages are already on disk
NL = "\n"


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count


def handoff(name):
    """Record that `name` answers from here on. The system message on disk stays; load() rewrites it."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"handoff": name}) + NL)


def compacted(messages):
    """Compaction rewrites history, so record the result and start from it."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"compacted": messages}) + NL)
    WRITTEN = len(messages)


def load(session_id):
    """Replay the log: messages accumulate, rewinds cut them back, a compaction replaces them, a handoff rewrites the prompt."""
    from . import handoff as handoffs  # here, not at the top: handoff imports llm, which imports modules that import session

    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written last line from a kill mid-save
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        elif "compacted" in entry:
            messages = list(entry["compacted"])
        elif "handoff" in entry:
            try:
                handoffs.apply(entry["handoff"], messages)
            except KeyError:
                pass  # the definition file is gone; the transcript loads with the agent it had before
        else:
            messages.append(entry)
    return messages


def open_session(session_id):
    """Switch to a past chat and become it."""
    global CURRENT, WRITTEN
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
    """Newest first."""
    if not SESSION_DIR.exists():
        return []
    files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"id": p.stem, "title": title(load(p.stem))} for p in files]
