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

import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

PROFILE = """(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{project}") (literal "/dev/null"))
(deny file-write* (subpath "{project}/.git"))
"""

# No pager may block waiting for a key, git must never prompt for a password,
# and a Python child prints UTF-8 whatever the console code page is.
ENV = {**os.environ, "PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "PYTHONIOENCODING": "utf-8"}


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        # one profile file per call: several tool calls may run at the same time
        with tempfile.NamedTemporaryFile("w", prefix="simple-harness-", suffix=".sb", delete=False) as profile:
            profile.write(PROFILE.format(project=PROJECT))
        return ["sandbox-exec", "-f", profile.name, "/bin/sh", "-c", command]

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


def kill_tree(process):
    """Kill the command and everything it started, not just the shell."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us. Raises TimeoutExpired with the partial output."""
    sandboxed = wrap(command)
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,  # a command that waits for input would hang the turn
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env=ENV,
        **group,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(process)
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
