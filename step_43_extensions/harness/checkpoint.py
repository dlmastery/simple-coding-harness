"""Step 33 - workspace checkpoints: a copy of every file before the agent
changes it, so a turn can be undone.

Before `write_file` or `str_replace` runs, the file as it is now is copied
into `~/.simple-harness/checkpoints/<session>/<turn>/<hashed path>` and one
line goes into that turn's `manifest.jsonl`. A file that does not exist
yet is recorded as such, so undoing the turn deletes it. A file is
captured once per turn: the first copy is the state before the turn, which
is the one an undo must bring back.

The capture runs from `tools.run`, after the permission check and the
approval, so a declined call captures nothing; `before(tool, args)` is
the one call the tool code makes, and a capture that fails is a loud
note naming the file, never a silent gap in the manifest. `agent.turn`
calls `begin_turn` once per user message, which numbers the turn and
records where the transcript stood. `/undo` and `/rewind` use that
record to cut the transcript and to restore the files together.
"""

import hashlib
import json
import shutil
import threading
from datetime import datetime
from pathlib import Path

from . import session

ROOT = Path.home() / ".simple-harness" / "checkpoints"

EDIT_TOOLS = ("write_file", "str_replace")  # the tools whose target file is captured

MANIFEST = "manifest.jsonl"  # one JSON line per captured file, in capture order
TURN_FILE = "turn.json"      # where the transcript stood when the turn began

TURN = 0  # the number of the turn now running; 0 before the first begin_turn

LOCK = threading.Lock()  # parallel tools and subagents may capture at the same time


def hashed(path):
    """A short, file-system safe name for a path: the first 16 hex digits of its SHA-1."""
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:16]


def session_dir(session_id=None):
    return ROOT / (session_id or session.CURRENT)


def turn_dir(turn=None, session_id=None):
    return session_dir(session_id) / f"{TURN if turn is None else turn:04d}"


def turns(session_id=None):
    """The turn numbers that have a directory, oldest first."""
    folder = session_dir(session_id)
    if not folder.exists():
        return []
    return sorted(int(p.name) for p in folder.iterdir() if p.is_dir() and p.name.isdigit())


def begin_turn(message_count):
    """Number the next turn and record how long the transcript is before it.

    The number continues from what is on disk, so a resumed session does
    not reuse a turn number that still holds checkpoints.
    """
    global TURN
    TURN = max(turns(), default=0) + 1
    folder = turn_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / TURN_FILE).write_text(json.dumps({"turn": TURN, "messages": message_count}), encoding="utf-8")
    return TURN


def start_of(turn, session_id=None):
    """The transcript length recorded when the turn began, or None when unknown."""
    record = turn_dir(turn, session_id) / TURN_FILE
    if not record.exists():
        return None
    return json.loads(record.read_text(encoding="utf-8")).get("messages")


def manifest(turn, session_id=None):
    """Every captured file of one turn, in capture order."""
    path = turn_dir(turn, session_id) / MANIFEST
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def capture(path, tool=None):
    """Save the file as it is before the tool changes it. Returns the manifest entry, or None.

    Once per file per turn: a second write in the same turn keeps the first
    copy, which is the state the turn started from.
    """
    target = Path(path).resolve()
    blob = hashed(target)
    with LOCK:
        folder = turn_dir()
        if any(entry["blob"] == blob for entry in manifest(TURN)):
            return None
        folder.mkdir(parents=True, exist_ok=True)
        existed = target.is_file()
        if existed:
            shutil.copy2(target, folder / blob)
        entry = {"path": str(target), "blob": blob, "existed": existed, "tool": tool, "time": datetime.now().isoformat(timespec="seconds")}
        with (folder / MANIFEST).open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    return entry


def before(tool, args):
    """Capture the target of an edit tool before it runs. Any other tool: nothing. A failure is a note, not an exception."""
    if tool not in EDIT_TOOLS:
        return
    path = (args or {}).get("path")
    if not path:
        return
    try:
        capture(path, tool=tool)
    except OSError as failed:
        from .ui import ui  # here, not at the top: ui imports todos, tools imports this module

        ui.note(f"checkpoint: could not capture {path} before {tool}: {failed}; /undo will not restore it")


def pre_tool_use(event):
    """The same capture as a PreToolUse hook, for a hooks.json that wants it there: `"python": "harness.checkpoint:pre_tool_use"`."""
    before(event.get("tool_name"), event.get("tool_input"))
    return None


def restore(entry, turn, session_id=None):
    """Put one file back as it was: copy the blob over it, or delete it if it was new."""
    target = Path(entry["path"])
    if entry["existed"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(turn_dir(turn, session_id) / entry["blob"], target)
    elif target.exists():
        target.unlink()
    return str(target)


def undo_turn(turn=None, session_id=None):
    """Restore every file of one turn (the last, by default) in reverse order.

    Returns (turn number, transcript length at its start, restored paths),
    or None when there is no turn to undo. The turn's checkpoints are
    removed afterwards: an undone turn cannot be undone twice.
    """
    if turn is None:
        found = turns(session_id)
        if not found:
            return None
        turn = found[-1]
    with LOCK:
        restored = [restore(entry, turn, session_id) for entry in reversed(manifest(turn, session_id))]
        start = start_of(turn, session_id)
        shutil.rmtree(turn_dir(turn, session_id), ignore_errors=True)
    return turn, start, restored


def undo_since(message_count, session_id=None):
    """Undo every turn that began at or after a transcript length, newest first.

    This is what `/rewind` needs: keeping the first N messages means the
    files must go back to how they were when message N was about to be
    written.
    """
    undone = []
    for turn in reversed(turns(session_id)):
        start = start_of(turn, session_id)
        if start is None or start < message_count:
            continue
        undone.append(undo_turn(turn, session_id))
    return undone


def compacted(before, after):
    """Compaction cut the transcript; move every recorded start with it.

    The compacted list is one summary message plus the tail of the old
    list, so a start inside the tail shifts by a constant. A start inside
    the summarised part has no place in the new list any more and is
    recorded as unknown; its files can still be undone, its transcript
    position cannot.
    """
    cut = before - after + 1
    for turn in turns():
        record = turn_dir(turn) / TURN_FILE
        if not record.exists():
            continue
        data = json.loads(record.read_text(encoding="utf-8"))
        start = data.get("messages")
        if start is not None:
            data["messages"] = start - cut + 1 if start >= cut else None
            record.write_text(json.dumps(data), encoding="utf-8")


def summary(session_id=None):
    """One row per turn: number, transcript start and the files captured."""
    rows = []
    for turn in turns(session_id):
        start = start_of(turn, session_id)
        files = [Path(entry["path"]).name + ("" if entry["existed"] else " (new)") for entry in manifest(turn, session_id)]
        where = f"from message {start}" if start is not None else "position unknown"
        rows.append(f"turn {turn:<4} {where:<22} {len(files)} file(s)  {', '.join(files) or '-'}")
    return rows
