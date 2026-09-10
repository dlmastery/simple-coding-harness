"""Kernel-enforced limits on what bash can touch.

One policy - read anything, write only inside the project, no network - and
a different mechanism per OS:

  macOS   sandbox-exec (Seatbelt), built into the OS
  Linux   bubblewrap (`bwrap`), if installed
  other   nothing; the permission rules are the only line of defence

The policy is the part that ports; the mechanism never does. The Seatbelt
profile below is the same shape the OpenAI Codex CLI uses, simplified.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

SEATBELT_PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""


def name():
    if sys.platform == "darwin":
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def wrap(command):
    """The argv that runs `command` inside the sandbox, or None if there is none."""
    if sys.platform == "darwin":
        profile = Path(tempfile.gettempdir()) / "simple-harness.sb"
        profile.write_text(SEATBELT_PROFILE)
        return ["sandbox-exec", "-f", str(profile), "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
            "--dev", "/dev", "--proc", "/proc",
            "--unshare-net", "--die-with-parent",
            "/bin/sh", "-c", command,
        ]

    return None


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us, with a hard timeout."""
    argv = wrap(command)
    return subprocess.run(
        argv or command,
        shell=argv is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
