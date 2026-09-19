"""Stage 15 - session. load() repairs a transcript that a crash left with
tool calls that have no results, so a resumed chat is always one the API
accepts.
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
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count


def compacted(messages):
    """Compaction rewrites history, so record the result and start from it."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"compacted": messages}) + NL)
    WRITTEN = len(messages)


def load(session_id):
    """Replay the log: messages accumulate, rewinds cut them back, a compaction replaces them."""
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
    return repaired(messages)


def repaired(messages):
    """A transcript that ends in tool calls without results gets a stand-in result for each.

    That is what a crash between a reply and its tool results leaves; the
    API refuses the transcript until every call has a result.
    """
    index = len(messages) - 1
    while index >= 0 and messages[index].get("role") == "tool":
        index -= 1
    if index < 0 or messages[index].get("role") != "assistant":
        return messages
    answered = {m.get("tool_call_id") for m in messages[index + 1:]}
    for call in messages[index].get("tool_calls") or []:
        if call["id"] not in answered:
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": "(the harness stopped before this tool ran; no result was recorded)"})
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
