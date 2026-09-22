"""Stage 8 - transcripts on disk. One append-only JSONL file per chat.

A rewind does not delete lines: it appends a marker saying "the list is now
this long". Loading replays the log from the top and applies the markers, so
the file is the full history of what happened, including what you rewound
past. What the agent has read (context.SEEN) is saved the same way, as a
state entry between the messages.
"""

import json
from datetime import datetime
from pathlib import Path

import context

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = Path.home() / ".simple-harness" / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many messages are already on disk
SEEN_SAVED = {}  # the last SEEN written to disk

INTERRUPTED = "(the harness stopped before this tool ran; no result was recorded)"


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN, SEEN_SAVED
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
        if context.SEEN != SEEN_SAVED:  # what the agent has read: a state entry, not a message
            SEEN_SAVED = dict(context.SEEN)
            f.write(json.dumps({"seen": SEEN_SAVED}) + "\n")
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = min(WRITTEN, count)  # a fresh chat has fewer lines on disk than count


def replay(session_id, seen=None):
    """Replay the log: messages accumulate, rewinds cut them back, and the
    latest "seen" entry lands in `seen` when a dict is given."""
    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written last line from a kill mid-save
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        elif "seen" in entry:
            if seen is not None:
                seen.clear()
                seen.update(entry["seen"])
        else:
            messages.append(entry)
    return messages


def repair(messages, note=INTERRUPTED):
    """A transcript can end in an assistant message whose tool calls never got results
    (a crash, a kill, ctrl-c). Give each one a result, or the next request is refused."""
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    last = next((m for m in reversed(messages) if m["role"] != "tool"), None)
    if last and last["role"] == "assistant":
        for call in last.get("tool_calls") or []:
            if call["id"] not in answered:
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": note})
    return messages


def load(session_id, seen=None):
    """The messages of a past chat, valid to send: replayed, then repaired."""
    return repair(replay(session_id, seen))


def open_session(session_id):
    """Switch to a past chat and become it."""
    global CURRENT, WRITTEN, SEEN_SAVED
    CURRENT = session_id
    messages = replay(session_id, seen=context.SEEN)
    SEEN_SAVED = dict(context.SEEN)
    WRITTEN = len(messages)
    repair(messages)
    save(messages)  # the repairs go on disk too, so rewind counts stay right
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
    return [{"id": p.stem, "title": title(replay(p.stem))} for p in files]
