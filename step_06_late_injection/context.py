"""Stage 6 - late injection.

Some system-level facts are best gathered right before the model call: the
date, the git branch, anything the agent can use that is not in the user's
message or the past context.

The block goes at the END of the message list, and only on the request,
never into `messages`, so the stable prefix in front of it stays cached.
A block at the top would change on every call, break the prefix and lose
the cache discount.
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
