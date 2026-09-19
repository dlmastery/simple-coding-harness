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

PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""

# no pagers, no credential prompts: the command has no terminal to answer on
BASH_ENV = {**os.environ, "PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"}
# the command starts its own process group, so a timeout can kill all of it
NEW_GROUP = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        profile = Path(tempfile.gettempdir()) / "simple-harness.sb"
        profile.write_text(PROFILE, encoding="utf-8")
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


def kill_tree(pid):
    """Kill a process and everything it started."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        os.killpg(pid, signal.SIGKILL)


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us. Raises TimeoutExpired after killing the tree."""
    sandboxed = wrap(command)
    proc = subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,            # no stdin: an interactive command ends, it does not wait
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",  # never a UnicodeDecodeError on odd output
        env=BASH_ENV, **NEW_GROUP,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)   # the shell alone would die; its children would live on
        proc.communicate()
        raise
    return subprocess.CompletedProcess(command, proc.returncode, out, err)
