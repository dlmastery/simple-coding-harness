"""Stage 8 - the late block, with a freshness check that survives a restart.

Stage 7 remembered mtimes in SEEN, and SEEN died with the process. This
stage makes chats resumable in a new process, so SEEN moves into the
session file (session.py writes it as a state entry, not a message) and
holds content hashes instead of mtimes, which mean nothing after a
restart. `git status --porcelain` supplies the label - modified, deleted,
new - for each file whose content is no longer what the agent saw.
"""

import hashlib
import os
import subprocess
from datetime import datetime

SEEN = {}  # absolute path -> sha1 of the content when the agent last read or wrote it

LABELS = {"M": "modified", "A": "added", "D": "deleted", "R": "renamed", "?": "new"}


def git(command):
    result = subprocess.run(f"git {command}", shell=True, capture_output=True,
                            encoding="utf-8", errors="replace")
    return result.stdout if result.returncode == 0 else None  # None: no git, or not a repository


def file_hash(path):
    """sha1 of the file's bytes; None when it is gone or unreadable."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()
    except OSError:
        return None


def note_seen(path):
    """Called by the read and write tools: remember the content as the agent saw it."""
    path = os.path.abspath(path)
    digest = file_hash(path)
    if digest:
        SEEN[path] = digest


def git_status():
    """absolute path -> one-letter status, straight from git."""
    root = (git("rev-parse --show-toplevel") or "").strip()
    status = {}
    for line in (git("status --porcelain") or "").splitlines():
        code, path = line[:2].replace(" ", "")[:1], line[3:].strip('"')
        if " -> " in path:  # a rename: "old -> new"
            path = path.split(" -> ")[-1]
        status[os.path.abspath(os.path.join(root, path))] = code
    return status


def file_changes():
    """Files the agent has seen whose content is no longer what it saw, labelled by git.
    The agent's own writes update SEEN, so they never show up here; an outside edit,
    a second outside edit, a revert or a delete all do."""
    status = git_status()
    changed = {}
    for path, digest in list(SEEN.items()):
        now = file_hash(path)
        if now == digest:
            continue
        code = status.get(path, "D" if now is None else "M")
        changed[path] = LABELS.get(code, code)
        if now is None:
            del SEEN[path]  # deleted: reported once, there is nothing left to re-read
    return changed


def changes_note():
    changed = file_changes()
    if not changed:
        return ""
    lines = [f"{label}: {path}" for path, label in changed.items()]
    return (
        "\n<system-reminder>\n"
        "These files changed since you read them. Read them again before "
        "editing:\n" + "\n".join(lines) + "\n</system-reminder>"
    )


def git_branch():
    branch = git("branch --show-current")
    if branch is None:
        return "(not a git repository)"
    return branch.strip() or "(detached)"


def reminder():
    """The block we append to the request on every call."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git_branch()}\n"
            "</env>" + changes_note()
        ),
    }
