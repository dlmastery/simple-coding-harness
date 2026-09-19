"""Step 34 - load() no longer writes a stand-in result for a tool call the
log left hanging: agent.recover() runs the call instead, so a resumed chat
gets the real result. repair() stays for ctrl-c mid-turn. The rest is step 21.
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT = "".join(c if c.isalnum() else "-" for c in str(Path.cwd().resolve()))
SESSION_DIR = Path.home() / ".simple-harness" / "sessions" / PROJECT
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # how many messages are already on disk
PERSIST = True  # False in print mode: one-off runs leave no session behind


def path_for(session_id):
    return SESSION_DIR / f"{session_id}.jsonl"


def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN
    if not PERSIST:
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
    WRITTEN = len(messages)


def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    if not PERSIST:
        WRITTEN = count
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count


def compacted(messages):
    """Compaction rewrites history, so record the result and start from it."""
    global WRITTEN
    if not PERSIST:
        WRITTEN = len(messages)
        return
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"compacted": messages}) + "\n")
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
