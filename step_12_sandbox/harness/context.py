"""Stage 12 - the late block, now watching git instead of an in-memory dict.

Stage 7 remembered mtimes in SEEN. That dict dies with the process, and
this stage makes chats resumable across processes. `git status --porcelain`
is remembered by nothing but git, so the freshness check moves onto it: the
block reports every path whose status changed since the previous call.
"""

import subprocess
from datetime import datetime

from .todos import todos_prompt

LABELS = {"M": "modified", "D": "deleted", "A": "added", "??": "new"}


def git(command):
    result = subprocess.run(f"git {command}", shell=True, capture_output=True, text=True)
    return result.stdout


def git_status():
    """path -> status code, straight from git."""
    return {line[3:]: line[:2].strip() for line in git("status --porcelain").splitlines()}


LAST_STATUS = git_status()


def file_changes():
    """What git sees as different since the previous call."""
    global LAST_STATUS
    now = git_status()
    changed = {p: c for p, c in now.items() if LAST_STATUS.get(p) != c}
    LAST_STATUS = now
    return changed


def changes_note():
    changed = file_changes()
    if not changed:
        return ""
    lines = [f"{LABELS.get(code, code)}: {path}" for path, code in changed.items()]
    return (
        "\n<system-reminder>\n"
        "These files changed since your last turn. Read them again before "
        "editing:\n" + "\n".join(lines) + "\n</system-reminder>"
    )


def todos_note():
    plan = todos_prompt()
    return f"\n<todos>\n{plan}\n</todos>" if plan else ""


def reminder():
    """The block we append to the request on every call."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git('branch --show-current').strip() or '(detached)'}\n"
            "</env>" + todos_note() + changes_note()
        ),
    }
