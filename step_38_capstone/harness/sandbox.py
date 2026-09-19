"""Stage 15 - an OS sandbox for bash.

Permissions are not real security. A file can still be removed from a
Python one-liner, because the rules only see the command text. A sandbox
asks a different question: is this specific operation allowed at all? The
kernel answers it.

One policy - read anything, write only inside the project, no network - and
one mechanism per OS. The macOS profile is the shape used by the OpenAI
Codex CLI (Apache-2.0); the Linux one is bubblewrap.
Windows has no equivalent here and the banner says so.

run() is the one place a foreground command starts: no stdin, no pager, no
credential prompt, UTF-8 output whatever the command prints, and a timeout
that kills the whole process tree, not just the shell.
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
ENV = {"PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"}

# the command starts its own process group, so a timeout can kill all of it
NEW_GROUP = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}


def temp_dir():
    """The real path of the temp directory; on macOS /var/folders is a link into /private."""
    return Path(tempfile.gettempdir()).resolve()


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        # one profile file per call: two threads writing one shared file would race
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


def kill_tree(pid):
    """Kill a process and everything it started."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def text(output):
    """Partial output as a string: communicate() hands back bytes or None after a timeout."""
    if output is None:
        return ""
    return output.decode("utf-8", errors="replace") if isinstance(output, bytes) else output


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us. Raises TimeoutExpired with the output so far."""
    sandboxed = wrap(command)
    process = subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,  # an interactive command ends instead of waiting for a terminal
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",  # never a UnicodeDecodeError on odd output
        env={**os.environ, **ENV},
        **NEW_GROUP,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        kill_tree(process.pid)
        partial_out, partial_err = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=text(expired.stdout) + text(partial_out), stderr=text(expired.stderr) + text(partial_err)) from None
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
