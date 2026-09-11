"""Stage 15 - an OS sandbox for bash (video 33:02).

Permissions are "not real security because a file can still be removed
using Python". A sandbox "asks a completely different question: if a
specific operation is allowed or not", and the kernel answers it.

One policy - read anything, write only inside the project, no network - and
one mechanism per OS. The macOS profile is the shape used by the OpenAI
Codex CLI (Apache-2.0), which the video borrows; the Linux one is bubblewrap.
Windows has no equivalent here and the banner says so.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        profile = Path(tempfile.gettempdir()) / "simple-harness.sb"
        profile.write_text(PROFILE)
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

    return None  # Windows, or Linux without bubblewrap


def name():
    if sys.platform == "darwin":
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
