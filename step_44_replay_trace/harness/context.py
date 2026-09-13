"""Step 40 - the <env> block names the active agent: main, or the
definition the conversation was handed to, from handoff.active_name().
The rest is step 39: the <env> block names the approval mode: default, accept-edits,
read-only, auto or plan, from modes.current().
The rest is step 29: the late block carries a <jobs> tag after <plan>: one line per
background job that is running, and one for a job that ended since the
model last read its status. Nothing when there are no jobs.
"""

import subprocess
from datetime import datetime

from . import handoff, jobs, modes, plan
from .hooks import SESSION_CONTEXT
from .memory import memory_index
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


def memory_note():
    index = memory_index()
    return f"\n<memory>\n{index}\n</memory>" if index else ""


def jobs_note():
    """The background jobs the model should know about, or nothing."""
    listing = jobs.jobs_prompt()
    return f"\n<jobs>\n{listing}\n</jobs>" if listing else ""


def hooks_note(turn_context=""):
    """Text the hooks asked to add: the session's, then this turn's."""
    text = "\n".join(part for part in SESSION_CONTEXT + [turn_context] if part).strip()
    return f"\n<hooks>\n{text}\n</hooks>" if text else ""


def reminder(hook_context=""):
    """The block we append to the request on every call."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git('branch --show-current').strip() or '(detached)'}\n"
            f"mode: {modes.current()}\n"
            f"agent: {handoff.active_name()}\n"
            "</env>" + todos_note() + plan.plan_note() + jobs_note() + memory_note() + hooks_note(hook_context) + changes_note()
        ),
    }
