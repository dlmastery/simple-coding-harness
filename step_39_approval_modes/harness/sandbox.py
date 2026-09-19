"""Stage 15 - an OS sandbox for bash.

Permissions are not real security. A file can still be removed from a
Python one-liner, because the rules only see the command text. A sandbox
asks a different question: is this specific operation allowed at all? The
kernel answers it.

One policy - read anything, write only inside the project, no network - and
one mechanism per OS. The macOS profile is the shape used by the OpenAI
Codex CLI (Apache-2.0); the Linux one is bubblewrap.
Windows has no equivalent here and the banner says so.

run() is the one place a foreground command starts. The command gets a
process group of its own, so a timeout kills everything it started, not
just the shell; its output is decoded as UTF-8 with replacement, so a
stray byte never raises; stdin is closed, so a command that waits for a
keyboard ends instead of hanging; and the pagers and credential prompts
are turned off, because there is no terminal to answer them on. On a
timeout the TimeoutExpired carries what the command printed so far.
"""

import os
import shutil
import signal
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

# no pagers, no credential prompts: the command has no terminal to answer on
ENV = {"PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "PYTHONIOENCODING": "utf-8"}

# the command starts its own process group, so a timeout can kill all of it
NEW_GROUP = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}


def temp_dir():
    """The real path of the temp directory; on macOS /var/folders is a link into /private."""
    return Path(tempfile.gettempdir()).resolve()


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        # one profile file per command: parallel tool calls must not overwrite each other's
        with tempfile.NamedTemporaryFile("w", prefix="simple-harness-", suffix=".sb", delete=False) as profile:
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


def popen(command, **options):
    """Start a command through the sandbox wrapper, in a process group of its own."""
    sandboxed = wrap(command)
    return subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, **ENV},
        **NEW_GROUP,
        **options,
    )


def kill_tree(process):
    """End a process and everything it started; the group id is the pid."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    process.kill()


def run(command, timeout=60):
    """Run a command to the end, sandboxed when the OS lets us. Returns a CompletedProcess.

    On a timeout the whole process tree is killed and TimeoutExpired is
    raised with `output` set to what arrived before the kill, so the
    caller can hand the partial output to the model.
    """
    process = popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        kill_tree(process)
        stdout, stderr = process.communicate()  # what the pipes held when it died
        raise subprocess.TimeoutExpired(command, timeout, output=(stdout or "") + (stderr or "")) from expired
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
