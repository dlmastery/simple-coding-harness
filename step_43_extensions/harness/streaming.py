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
import subprocess
import threading

from . import sandbox

TIMEOUT = 60      # seconds a foreground command may run before it is killed
JOIN_GRACE = 2    # seconds to wait for the reader after the process has ended


def popen(command):
    """Start a command through the sandbox wrapper, its output on one text pipe.

    stderr is merged into stdout so the lines keep their order, which is
    the order the model reads them in. bufsize=1 makes the pipe
    line-buffered on this side. The rest is what sandbox.run does for a
    foreground command: no stdin, utf-8 with errors="replace" so a stray
    byte cannot end the read, the no-pager environment, and a process
    group of its own so a kill reaches the children too.
    """
    sandboxed = sandbox.wrap(command)  # argv inside the OS sandbox, or None for a plain shell
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    return subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
        env=sandbox.ENV,
        **group,
    )


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
        """The thread body: one readline at a time until the pipe closes.

        A callback that raises stops being called; the reading goes on, so
        the model still gets the whole output when the screen cannot show it.
        """
        try:
            for raw in self.process.stdout:
                self.count += 1
                if self.lines is not None:
                    self.lines.append(raw)
                if self.on_line is not None:
                    try:
                        self.on_line(raw.rstrip("\r\n"))
                    except Exception:  # noqa: BLE001 - the screen is not worth the output
                        self.on_line = None
        finally:
            self.process.stdout.close()

    def join(self, timeout=None):
        """Wait for the last lines: without a limit after a normal exit, for JOIN_GRACE seconds after a kill.

        A process that ended closed its end of the pipe, so the reader is
        about to finish; a killed one may have left a grandchild holding
        the pipe open, and that cannot hold the caller for long.
        """
        self.thread.join(timeout)

    def text(self):
        """The whole output so far, exactly as the process wrote it."""
        return "".join(self.lines or [])


def kill(process):
    """End a process that ran past its time, and the tree it started.

    process.kill() alone reaches only the shell. The command it started
    keeps the pipe open and keeps printing, and the reader keeps reading.
    sandbox.kill_tree signals the whole process group on POSIX and walks
    the tree with taskkill on Windows.
    """
    if process.poll() is not None:
        return
    sandbox.kill_tree(process)
    try:
        process.wait(timeout=JOIN_GRACE)
    except subprocess.TimeoutExpired:
        pass


def run(command, timeout=None, on_line=None):
    """Run a command to the end, streaming its lines to on_line. Returns the full output.

    The main thread waits on the process with the timeout (TIMEOUT unless
    given) while the Reader pumps the pipe. On expiry the process tree is
    killed and subprocess.TimeoutExpired is raised with `output` set to
    the lines that arrived before the kill, as sandbox.run did, so bash
    hands the model what it saw. A KeyboardInterrupt kills it too.
    """
    timeout = TIMEOUT if timeout is None else timeout
    process = popen(command)
    reader = Reader(process, on_line)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        kill(process)
        reader.join(JOIN_GRACE)
        raise subprocess.TimeoutExpired(command, timeout, output=reader.text()) from expired
    except BaseException:
        kill(process)
        raise
    reader.join()  # the process has ended: the pipe is closing, the last lines are moments away
    return reader.text()
