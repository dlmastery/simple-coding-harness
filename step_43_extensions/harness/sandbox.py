"""Stage 15 - an OS sandbox for bash.

Permissions are not real security. A file can still be removed from a
Python one-liner, because the rules only see the command text. A sandbox
asks a different question: is this specific operation allowed at all? The
kernel answers it.

One policy - read anything, write only inside the project, no network - and
one mechanism per OS. The macOS profile is the shape used by the OpenAI
Codex CLI (Apache-2.0); the Linux one is bubblewrap.
Windows has no equivalent here and the banner says so.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

# Filled in per command by wrap(): PROJECT can change (step 30 runs evaluations
# in a temp workspace), and tests need the temp directory to be writable.
PROFILE = """(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{project}") (subpath "{tmp}") (literal "/dev/null"))
(deny file-write* (subpath "{project}/.git"))
"""


def temp_dir():
    """The real path of the temp directory; on macOS /var/folders is a link into /private."""
    return Path(tempfile.gettempdir()).resolve()


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        # one profile file per command: parallel tool calls must not write the same file at the same time
        with tempfile.NamedTemporaryFile("w", prefix="simple-harness-", suffix=".sb", delete=False, encoding="utf-8") as profile:
            profile.write(PROFILE.format(project=Path(PROJECT).resolve(), tmp=temp_dir()))
        return ["sandbox-exec", "-f", profile.name, "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
            "--bind", str(temp_dir()), str(temp_dir()),
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
