"""Stage 15 - an OS sandbox for bash.

Permissions are not real security. A file can still be removed from a
Python one-liner, because the rules only see the command text. A sandbox
asks a different question: is this specific operation allowed at all? The
kernel answers it.

One policy - read anything, write only inside the project, no network - and
one mechanism per OS. The macOS profile is the shape used by the OpenAI
Codex CLI (Apache-2.0); the Linux one is bubblewrap.
Windows has no equivalent here and the banner says so.

run() also owns the plumbing every command needs: no stdin, no pager, utf-8
output, and a process group of its own so a timeout kills the whole tree,
not just the shell that started it.
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

# what every command inherits on top of the environment: no pager, no git prompt
ENV = {"PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"}


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        # one profile file per call: parallel tool calls must not share it
        handle = tempfile.NamedTemporaryFile(mode="w", prefix="simple-harness-", suffix=".sb", delete=False, encoding="utf-8")
        handle.write(PROFILE.format(project=Path(PROJECT).resolve()))
        handle.close()
        return ["sandbox-exec", "-f", handle.name, "/bin/sh", "-c", command]

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


def group_options():
    """Popen options that put the command in a process group of its own."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def kill_tree(process):
    """Kill a process started with group_options() and everything it spawned."""
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (OSError, AttributeError):
            pass
    try:
        process.kill()  # the leader itself, in case the group call missed it
    except OSError:
        pass


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us. Returns a CompletedProcess.

    On timeout the whole process tree is killed and TimeoutExpired carries
    the output collected so far in `.stdout`.
    """
    sandboxed = wrap(command)
    process = subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, **ENV},
        **group_options(),
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(process)  # closes every pipe, so the second communicate returns
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
