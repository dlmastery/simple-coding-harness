"""Stage 7 - file freshness reminders.

The harness alerts the agent when a file has changed since the agent last
read it, and prompts the agent to read the file again before editing it.

A global dict SEEN records the mtime whenever the agent reads or writes a
file. On the next call, any file whose mtime moved is listed in a
<system-reminder> inside the late block. The reminder rides in the same
injected message as the <env> block, so it never touches the prefix.
"""

import os
import subprocess
from datetime import datetime

SEEN = {}  # absolute path -> mtime when the agent last read or wrote it


def note_seen(path):
    """Called by the read and write tools: remember the file as the agent saw it."""
    path = os.path.abspath(path)  # "a.txt", "./a.txt" and the full path are one file
    if os.path.exists(path):
        SEEN[path] = os.path.getmtime(path)


def stale_files():
    """Files whose mtime on disk no longer matches what the agent saw. A deleted
    file is reported once and then forgotten: there is nothing left to re-read."""
    stale = []
    for path, mtime in list(SEEN.items()):
        if not os.path.exists(path):
            stale.append(f"{path} (deleted)")
            del SEEN[path]
        elif os.path.getmtime(path) != mtime:
            stale.append(path)
    return stale


def stale_note():
    """Warn about files that changed on disk since the agent read them."""
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed on disk since you read them. Read them again "
        "before editing:\n" + "\n".join(changed) + "\n</system-reminder>"
    )


def git_branch():
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:  # no git, or not a repository: say so instead of guessing
        return "(not a git repository)"
    return result.stdout.strip() or "(detached)"


def reminder():
    """The block we append to the request on every call."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git_branch()}\n"
            "</env>" + stale_note()
        ),
    }
