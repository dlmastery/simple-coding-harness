"""Stage 6 - late injection (video 26:37).

"Sometimes we want to grab additional system level information right
before we invoke the LLM call": the date, the git branch, anything the
agent can use that is not in the user's message or the past context.

It goes at the END of the message list, and only on the request - never
into `messages` - so the stable prefix in front of it stays cached. "If you
put it at the top your prefix keeps breaking and you never hit the prefix
cache often enough to actually save money."
"""

import subprocess
from datetime import datetime


def git_branch():
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
    return result.stdout.strip() or "(detached)"


def reminder():
    """The block we append to the request on every call."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git_branch()}\n"
            "</env>"
        ),
    }
