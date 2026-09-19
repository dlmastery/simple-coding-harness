"""Step 42 - streaming tool output: a command's lines reach the screen as
they arrive, not when the command ends.

subprocess.run hands the output over once, after the process has exited.
A test run that takes two minutes shows nothing for two minutes. This
module runs the command with subprocess.Popen instead, through the same
sandbox wrapper as before, and a Reader thread pulls stdout line by line.
Every line goes to a callback the moment it is read; the Reader also keeps
the whole output, so the caller still gets the full text at the end and
caps it the way it always did. The model sees the same result as before;
only the screen changes.

The Reader is shared: bash uses it for a foreground command, and the
background jobs of step 29 use it to fill their log files. run() is the
foreground path: start, pump, wait with a timeout, kill on expiry, and
raise subprocess.TimeoutExpired so bash can turn it into a result.
"""

import os
import signal
import subprocess
import sys
import threading

from . import sandbox

TIMEOUT = 60      # seconds a foreground command may run before it is killed
JOIN_GRACE = 2    # seconds to wait for the reader after a kill; a child that kept the pipe open cannot hold the caller

# no pagers and no credential prompts: the command has no terminal to answer on
ENV = {"PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "PYTHONIOENCODING": "utf-8"}


def popen(command):
    """Start a command through the sandbox wrapper, its output on one text pipe.

    stderr is merged into stdout so the lines keep their order. text=True
    and bufsize=1 make the pipe line-buffered on this side; errors="replace"
    keeps a stray byte from ending the read. stdin is /dev/null: a command
    that waits for a keyboard gets an end of file instead of a hang.
    """
    sandboxed = sandbox.wrap(command)  # argv inside the OS sandbox, or None for a plain shell
    return subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env={**os.environ, **ENV},
        **group_options(),
    )


def group_options():
    """Popen options that put the command in a process group of its own, so a kill reaches its children too."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


class Reader:
    """A thread that reads a process's stdout line by line as it arrives.

    Each line, without its newline, goes to on_line at once. With keep=True
    the raw lines are kept, and text() joins them into the output the
    caller would have had from subprocess.run. A background job passes
    keep=False: its log file is the record, and a server can print forever.
    """

    def __init__(self, process, on_line=None, keep=True):
        self.process = process
        self.on_line = on_line
        self.lines = [] if keep else None
        self.count = 0
        self.thread = threading.Thread(target=self.pump, name="tool-output", daemon=True)
        self.thread.start()

    def pump(self):
        """The thread body: one readline at a time until the pipe closes."""
        try:
            for raw in self.process.stdout:
                self.count += 1
                if self.lines is not None:
                    self.lines.append(raw)
                if self.on_line is not None:
                    try:
                        self.on_line(raw.rstrip("\r\n"))
                    except Exception:  # noqa: BLE001 - a screen that cannot draw must not stop the reading
                        pass
        finally:
            self.process.stdout.close()

    def join(self, timeout=None):
        """Wait for the last lines. After a kill, give a timeout: a child that kept the pipe open cannot hold the caller for long."""
        self.thread.join(timeout)

    def text(self):
        """The whole output so far, exactly as the process wrote it."""
        return "".join(self.lines or [])


def kill(process):
    """End a process that ran past its time, and the tree it started.

    process.kill() alone reaches only the shell. The command it started
    keeps the pipe open and keeps printing, and the reader keeps reading.
    group_options() gave the command a group of its own, so on POSIX the
    whole group gets the signal; on Windows taskkill walks the tree.
    """
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)  # start_new_session: the group id is the pid
        except (ProcessLookupError, PermissionError):
            pass
    process.kill()
    try:
        process.wait(timeout=JOIN_GRACE)
    except subprocess.TimeoutExpired:
        pass


def run(command, timeout=None, on_line=None):
    """Run a command to the end, streaming its lines to on_line. Returns the full output.

    The main thread waits on the process with the timeout (TIMEOUT unless
    given) while the Reader pumps the pipe. On expiry the process tree is
    killed and subprocess.TimeoutExpired is raised, as subprocess.run did,
    so the caller's handling stays the same. A KeyboardInterrupt kills it too.
    """
    timeout = TIMEOUT if timeout is None else timeout
    process = popen(command)
    reader = Reader(process, on_line)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill(process)
        reader.join(JOIN_GRACE)
        raise subprocess.TimeoutExpired(command, timeout, output=reader.text())  # what it printed before the kill rides along
    except BaseException:
        kill(process)
        raise
    reader.join()  # a normal exit closed the pipe; the last lines are moments away
    return reader.text()
