"""Late injection: a small block appended just before each model call.

Two facts about the prompt drive the design:

1. Some context changes every call (the time, the git branch, which files
   moved). It cannot go in the system prompt, which is written once.
2. Providers cache the *prefix* of a prompt. As long as the first N messages
   are byte-identical to last time, they are cheap. Anything that changes
   early in the list invalidates everything after it.

So the changing block goes at the END, is rebuilt fresh each call, and is
never stored in `messages`.

New in this step: file freshness. The model's memory of a file is whatever
it read last, and that goes stale the moment you (or a formatter, or a test
run) touch the file. We snapshot `git status` plus a content hash of every
changed file, diff the snapshots between calls, and tell the model which
files it must re-read before editing.
"""

import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

LABELS = {"M": "modified", "D": "deleted", "A": "added", "??": "new", "R": "renamed"}


def git(args):
    """Run a git command and return its stdout, or "" if git is unhappy."""
    result = subprocess.run(f"git {args}", shell=True, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def file_hash(path):
    file = Path(path)
    return hashlib.md5(file.read_bytes()).hexdigest() if file.is_file() else None


def git_state():
    """path -> (status code, content hash) for every file git sees as changed."""
    state = {}
    for line in git("status --porcelain").splitlines():
        code, path = line[:2].strip(), line[3:].strip()
        state[path] = (code, file_hash(path))
    return state


LAST = git_state()  # taken once at import, so the first call has a baseline


def file_changes():
    """Files whose status or contents moved since the previous call."""
    global LAST
    now = git_state()
    changed = {path: value[0] for path, value in now.items() if LAST.get(path) != value}
    LAST = now
    return changed


def changes_note():
    changed = file_changes()
    if not changed:
        return ""
    lines = "\n".join(f"{LABELS.get(code, code)}: {path}" for path, code in changed.items())
    return (
        "\n<system-reminder>\nThese files changed since your last turn. "
        f"Read them again before editing:\n{lines}\n</system-reminder>"
    )


def env_block():
    branch = git("branch --show-current").strip() or "(no git)"
    return f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>"


def reminder():
    """The message we append to the request - and only to the request."""
    return {"role": "user", "content": env_block() + changes_note()}
