"""Transcripts on disk: one append-only JSONL file per chat.

Append-only is the design decision. A rewind does not delete lines; it
appends a marker saying "the list is now this long". Loading replays the
log from the top and applies the markers, so the file is the full history of
what happened, including the parts you rewound past.
"""

import json
from datetime import datetime
from pathlib import Path

from . import config

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = config.HOME / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many entries of `messages` are already in the file


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def save(messages):
    """Append whatever is new. Never rewrites what is already on disk."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry; the old messages stay in the file."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count


def compacted(messages):
    """Compaction rewrites history: record the result and continue from it."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"compacted": messages}) + "\n")
    WRITTEN = len(messages)


def load(session_id):
    """Replay the log: messages accumulate, rewind markers cut them back,
    compaction entries replace the whole list."""
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
        else:
            messages.append(entry)
    return messages


def open_session(session_id):
    """Switch to a past chat: from now on we append to its file."""
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
    """Newest first: [{id, title}, ...]."""
    if not SESSION_DIR.exists():
        return []
    files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"id": p.stem, "title": title(load(p.stem))} for p in files]
