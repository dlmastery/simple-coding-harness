"""Late injection: a small block appended just before each model call.

Two facts about the prompt drive the design:

1. Some context changes every call (the time, the git branch). It cannot go
   in the system prompt, which is written once at startup.
2. Providers cache the *prefix* of a prompt. As long as the first N messages
   are byte-identical to last time, they are cheap. Anything that changes
   early in the list invalidates everything after it.

So the changing block goes at the END, is rebuilt fresh each call, and is
never stored in `messages`. The stable prefix stays cached; the volatile
part costs a few dozen tokens.
"""

import subprocess
from datetime import datetime


def git(args):
    """Run a git command and return its stdout, or "" if git is unhappy."""
    result = subprocess.run(f"git {args}", shell=True, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else ""


def env_block():
    branch = git("branch --show-current").strip() or "(no git)"
    return f"<env>\ntime: {datetime.now():%Y-%m-%d %H:%M}\ngit branch: {branch}\n</env>"


def reminder():
    """The message we append to the request - and only to the request."""
    return {"role": "user", "content": env_block()}
