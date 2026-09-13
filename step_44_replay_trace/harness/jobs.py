"""Step 42 - a job's output comes through the same Reader thread as
a foreground command's. The reader appends each line to the log file,
and while job_wait blocks the lines also show live in the job's panel. The rest is step 29: background jobs: shell commands that keep running while the
conversation goes on.

bash blocks the turn until the command ends, and kills it after a timeout.
That is right for a grep and wrong for a dev server, a long test run or a
build. bash_background starts the command with subprocess.Popen, through
the same sandbox wrapper as bash, and returns at once with a job id. The
output goes to a log file. job_status reads the tail of that file and
reports whether the process is still running. job_wait blocks for a while;
job_kill ends the process and everything it started.

Every job stays in JOBS until the session ends. The late block lists the
running ones, so the model does not forget what it started. kill_all() runs
on the way out: a job never outlives the session.
"""

import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import sandbox, streaming

TAIL_LINES = 20     # lines of the log a status report shows
KILL_GRACE = 2      # seconds a job gets to end on its own before the next, harder step
DEFAULT_WAIT = 60   # seconds job_wait blocks when the model gives no timeout

JOBS = {}                 # job id -> Job, in start order
_lock = threading.Lock()  # guards the counter: tool calls can come from a thread pool
_counter = 0


@dataclass
class Job:
    id: str
    command: str
    process: subprocess.Popen
    log: Path
    started: float
    seen: bool = False    # True once a report showed the model that the job had ended
    killed: bool = False  # True when job_kill or kill_all ended it
    reader: object = None  # the streaming.Reader that fills the log
    on_line: object = None  # set while job_wait shows the job live: each new line goes here too

    def running(self):
        return self.process.poll() is None

    def record(self, line):
        """The reader's callback: one line to the log, and to the screen when someone is waiting."""
        with open(self.log, "a", encoding="utf-8") as out:
            out.write(line + "\n")
        if self.on_line is not None:
            self.on_line(line)

    def settle(self):
        """Wait for the reader's last lines once the process has ended, so the log is complete."""
        if self.reader is not None and not self.running():
            self.reader.join()

    def tail(self):
        """The last TAIL_LINES lines of the log, or a note that there are none."""
        try:
            text = self.log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        lines = text.splitlines()
        if not lines:
            return "(no output yet)" if self.running() else "(no output)"
        return "\n".join(lines[-TAIL_LINES:])

    def state(self):
        code = self.process.poll()
        if code is None:
            return f"running for {int(time.time() - self.started)}s"
        return f"killed (exit code {code})" if self.killed else f"exited with code {code}"


def next_id():
    global _counter
    with _lock:
        _counter += 1
        return f"job-{_counter}"


def start(command):
    """Start a command in the background and return its Job."""
    handle = tempfile.NamedTemporaryFile(prefix="harness-job-", suffix=".log", delete=False)
    handle.close()
    log = Path(handle.name)

    # the same start as a foreground command: the sandbox wrapper, one pipe, a
    # process group of its own so job_kill can signal the whole tree at once
    process = streaming.popen(command)
    job = Job(next_id(), command, process, log, time.time())
    job.reader = streaming.Reader(process, job.record, keep=False)  # the log is the record; a server prints forever
    JOBS[job.id] = job
    return job


def terminate(process):
    """End a process and the children it started.

    Windows: a CTRL_BREAK to the process group, then taskkill for the tree.
    Elsewhere: SIGTERM to the session. If the group is gone but the leader
    is not, terminate() and kill() finish the job the plain way.
    """
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)  # reaches the whole group
            process.wait(timeout=KILL_GRACE)
            return
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except (OSError, AttributeError):
            pass
    try:
        process.wait(timeout=KILL_GRACE)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=KILL_GRACE)
        except subprocess.TimeoutExpired:
            process.kill()


def find(job_id):
    """The Job, or an error string naming the ids that exist."""
    job = JOBS.get(job_id)
    if job is not None:
        return job
    known = ", ".join(JOBS) or "none"
    return f"Error: no job {job_id!r}. Known jobs: {known}."


def report(job):
    """One status report: id, state, command and the tail of the log."""
    job.seen = not job.running()  # an ended job leaves the late block once reported
    job.settle()                  # the last lines are in the log before the tail is read
    return (
        f"{job.id}: {job.state()}\n"
        f"command: {job.command}\n"
        f"log: {job.log}\n"
        f"--- last {TAIL_LINES} lines ---\n"
        f"{job.tail()}"
    )


# ----------------------------------------------------------------- the tools


def bash_background(command: str) -> str:
    """Start a shell command in the background. Returns its job id at once."""
    try:
        job = start(command)
    except OSError as failed:
        return f"Error: could not start the job: {failed}"
    return (
        f"Started {job.id}: {command}\n"
        f"Output goes to {job.log}. Call job_status to check on it, "
        "job_wait to block for it, job_kill to stop it."
    )


def job_status(job_id: str) -> str:
    """Is the job still running? Plus the last lines of its output."""
    job = find(job_id)
    if isinstance(job, str):
        return job
    return report(job)


def job_wait(job_id: str, timeout: int = DEFAULT_WAIT) -> str:
    """Block until the job ends or the timeout passes, then report."""
    job = find(job_id)
    if isinstance(job, str):
        return job
    from .ui import ui  # here, not at the top: ui is built on top of the tools

    with ui.streaming(job.id, {"command": job.command}) as show:  # the wait is the one time someone is watching
        job.on_line = show
        try:
            job.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return f"{job.id} is still running after {timeout}s.\n" + report(job)
        finally:
            job.on_line = None
    return report(job)


def job_kill(job_id: str) -> str:
    """Stop the job and every process it started."""
    job = find(job_id)
    if isinstance(job, str):
        return job
    if not job.running():
        return f"{job.id} had already ended.\n" + report(job)
    job.killed = True
    terminate(job.process)
    return f"Killed {job.id}.\n" + report(job)


# --------------------------------------------------------- session plumbing


def running():
    """The jobs whose process is still alive, in start order."""
    return [job for job in JOBS.values() if job.running()]


def jobs_prompt():
    """One line per job the model should know about. Empty when there is none.

    Running jobs are always listed. A job that ended is listed until a
    report has shown the model that it ended.
    """
    lines = []
    for job in JOBS.values():
        if job.running():
            lines.append(f"{job.id}: {job.state()} - {job.command}")
        elif not job.seen:
            lines.append(f"{job.id}: {job.state()} - {job.command} (job_status shows its output)")
    return "\n".join(lines)


def kill_all():
    """Session end: kill every running job and delete every log."""
    for job in JOBS.values():
        job.killed = job.killed or job.running()
        terminate(job.process)
        job.settle()  # the reader has let go of the log before it is deleted
    for job in JOBS.values():
        try:
            job.log.unlink(missing_ok=True)
        except OSError:
            pass
    JOBS.clear()


def schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


JOB_SCHEMAS = [
    schema(
        "bash_background",
        (
            "Start a shell command in the background and return a job id at once. "
            "For servers, long builds and test runs that would hit the bash timeout. "
            "Output goes to a log; read it with job_status."
        ),
        {"command": {"type": "string", "description": "The shell command to start"}},
        ["command"],
    ),
    schema(
        "job_status",
        "Report whether a background job is still running, its exit code if not, and the last 20 lines of its output.",
        {"job_id": {"type": "string", "description": "The id bash_background returned, e.g. job-1"}},
        ["job_id"],
    ),
    schema(
        "job_wait",
        "Block until a background job ends or the timeout passes, then report like job_status.",
        {
            "job_id": {"type": "string", "description": "The id bash_background returned"},
            "timeout": {"type": "integer", "description": f"Seconds to wait, default {DEFAULT_WAIT}"},
        },
        ["job_id"],
    ),
    schema(
        "job_kill",
        "Stop a background job and every process it started.",
        {"job_id": {"type": "string", "description": "The id bash_background returned"}},
        ["job_id"],
    ),
]

JOB_TOOLS = {
    "bash_background": bash_background,
    "job_status": job_status,
    "job_wait": job_wait,
    "job_kill": job_kill,
}
