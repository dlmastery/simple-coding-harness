# Step 42 - Streaming tool output

**What this step adds:** a running command shows its output as it
happens. `harness/streaming.py` runs the command with `subprocess.Popen`
through the sandbox wrapper of step 12, and a `Reader` thread pulls
stdout line by line. Each line goes to `ui.tool_line` the moment it is
read, and a panel on screen shows the last eight lines while the command
runs. When the command exits the panel comes down and the finished panel
is printed as before. The model's result does not change: the whole
output is collected and capped by the step 14 logic, exactly as it was.
Background jobs from step 29 fill their log through the same `Reader`,
and `job_wait` shows the job live while it blocks. A subagent run gets a
panel of its own that lists each nested tool call as it completes.

## Why the screen and the model see different things

`subprocess.run` returns once, after the process has exited. A test
suite that runs for two minutes shows nothing for two minutes. The user
cannot tell a slow test from a hung one, and cannot see that the tenth
test is the one that failed until all of them are done. The bash tool
has worked this way since step 2.

The model does not have this problem. It reads the result once, when the
call is over, and it needs the whole text, capped and spilled to a file
when it is long. Nothing about the result should change.

So the two readers get two paths. A thread reads the pipe and forwards
each line to the screen as it arrives. The same thread keeps every line,
and when the process exits the caller joins them into the output it
would have had from `subprocess.run`. The cap, the spill file and the
timeout message are untouched. The transcript is byte for byte what
step 41 produced; only the screen is live.

One live display at a time is the constraint the UI works under. rich
draws a live region for the spinner and would draw another for the
panel. The panel opens while a tool runs, and the spinner turns while
the model thinks, so the two rarely meet. When they do - a subagent
thinking while a parallel `bash` call runs - the panel stops the
spinner and takes over, and a spinner started while a panel is open
shows nothing. The panel stands in for it either way.

## The code, piece by piece

### 1. The start

`harness/streaming.py`:

```python
def popen(command):
    ...
    sandboxed = sandbox.wrap(command)  # argv inside the OS sandbox, or None for a plain shell
    return subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        errors="replace",
        **group_options(),
    )
```

The same wrapper as `sandbox.run`: seatbelt on macOS, bubblewrap on
Linux, a plain shell on Windows. stderr is merged into stdout so the
lines keep their order. `text=True` with `bufsize=1` makes the pipe
line-buffered on this side, and `errors="replace"` keeps one stray byte
from ending the read. stdin is closed, so a command that waits for a
keyboard gets an end of file instead of hanging the turn. The process
gets a group of its own, on Windows and elsewhere, so a kill reaches
the children it started. This is the start step 29 used for jobs; both
paths now share it.

### 2. The reader

`harness/streaming.py`:

```python
class Reader:
    ...
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
                    self.on_line(raw.rstrip("\r\n"))
        finally:
            self.process.stdout.close()

    def text(self):
        """The whole output so far, exactly as the process wrote it."""
        return "".join(self.lines or [])
```

One thread per command. It blocks on the pipe, and every line it gets
goes two ways: the raw line, newline included, into the list, and the
stripped line into the callback. `text()` joins the raw lines, so the
output is what `subprocess.run` would have returned. `keep=False` is for
background jobs: their log file is the record, and a server that prints
for an hour must not fill a list in memory.

### 3. The wait and the kill

`harness/streaming.py`:

```python
def run(command, timeout=None, on_line=None):
    ...
    timeout = TIMEOUT if timeout is None else timeout
    process = popen(command)
    reader = Reader(process, on_line)
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill(process)
        reader.join()
        raise
    except BaseException:
        kill(process)
        raise
    reader.join()
    return reader.text()
```

The calling thread does not read; it waits, with the timeout. The
reader thread does the reading. This is why the timeout still works: a
`readline` blocks for as long as the process is silent, and a thread
that is stuck on it cannot count seconds. `process.wait` can. On expiry
`kill` ends the process tree, `taskkill /T` on Windows, and the same
`TimeoutExpired` that `subprocess.run` raised comes out, so `bash` keeps
its handling. A Ctrl-C kills the command too. After a normal exit the
reader is joined, so the last lines are in before `text()` is read.

### 4. The bash tool

`harness/tools.py`:

```python
def bash(command: str) -> str:
    ...
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    with ui.streaming("bash", {"command": command}) as show:
        try:
            output = streaming.run(command, on_line=show)
        except subprocess.TimeoutExpired as expired:
            # A slow command is the model's problem to work around, not a reason
            # to take the session down. Hand the failure back as a result.
            return f"Timed out after {expired.timeout}s and was killed. Narrow it down."
    return history.cap(output or "(no output)")
```

`ui.streaming` opens the panel and returns a callable; each call adds
one line. The `with` block closes the panel on the way out, on a normal
exit, a timeout or an exception. The last line is the step 14 cap,
unchanged: the model reads the same text it read in step 41, with the
same spill file when the output is long.

### 5. The panel

`harness/ui.py`:

```python
class ToolStream:
    ...
    def __init__(self, ui, name, args):
        self.ui = ui
        self.name = name
        self.args = args
        self.lines = deque(maxlen=STREAM_LINES)
        self.count = 0  # every line seen, including the ones that scrolled off

    def __call__(self, line):
        self.ui.tool_line(self.name, line, self)

    def __enter__(self):
        self.ui.stream_open(self)
        return self

    def __exit__(self, *exc):
        self.ui.stream_close(self)
        return False
```

A `ToolStream` is one running call: the tool's name, its arguments and
a `deque` of the last `STREAM_LINES` lines. `count` keeps growing after
the deque is full, so the panel can say how many lines scrolled off.
The object is a context manager and a callable at once, which is what
lets `bash` hand it to the reader as `on_line`.

`harness/ui.py`:

```python
    def tool_line(self, name, line, stream=None):
        ...
        with self._streams_lock:
            if stream is None:
                stream = next((s for s in reversed(self._streams) if s.name == name), None)
                if stream is None:
                    stream = self.stream_open(ToolStream(self, name, {}))
            stream.lines.append(line)
            stream.count += 1
            self._redraw()
```

Lines arrive on reader threads, several at once when a reply had
parallel `bash` calls, so the list of open streams is guarded by a lock.
`_redraw` starts a rich `Live` for the first open panel, updates it on
every line, and `stream_close` stops it when the last panel goes. The
`Live` is transient: it erases itself on stop, and `ui.tool` prints the
finished panel in its place. A caller with no stream in hand can still
call `tool_line(name, line)`; the line joins the newest panel of that
name, or opens one.

### 6. Background jobs

`harness/jobs.py`:

```python
    process = streaming.popen(command)
    job = Job(next_id(), command, process, log, time.time())
    job.reader = streaming.Reader(process, job.record, keep=False)  # the log is the record; a server prints forever
```

A job starts the way a foreground command does and reads the way it
does. `Job.record` is the callback: one line appended to the log file,
and forwarded to the screen when someone is waiting. `job_wait` opens a
panel named after the job for the length of its wait, so a `pytest` run
started in the background shows its lines while the model blocks on it,
and stays quiet in the log at every other time.

### 7. A subagent run

`harness/subagent.py`:

```python
    # step 42: one panel for the whole run; every nested tool call adds a line to it
    with ui.streaming(label, {"request": title(request)}) as progress:
        return turns(messages, tools, max_turns, label, tag, progress, report)
...
            ui.tool(tool_call.function.name, args, result, nested=True, tag=tag)
            progress(progress_line(tool_call.function.name, args, result))
```

A `task` or `browse` call can run for minutes. Its nested `bash` calls
stream through the same `bash` tool, so their lines show as they arrive.
The run itself has a panel too, named after its label, and every nested
call adds one line: the tool, its argument and how many lines came back.
The lead's screen shows what the subagent is doing before its report
comes back, and the finished panels below it are the record.

## Run it

```bash
pip install -e .
harness
```

Ask for something slow:

```text
> run the test suite
```

The `bash` panel appears with the command in its header and `running ·
0 lines` in its title. Lines fill in as pytest prints them; after eight,
the oldest scroll off and the title counts them. When pytest exits the
panel disappears and the usual finished panel takes its place, with the
same twelve-line preview as before. Then the model answers.

Start something long in the background and wait for it:

```text
> start the tests in the background, then wait for them
```

`bash_background` returns `Started job-1` at once. `job_wait` opens a
panel named `job-1` and the lines show while it blocks; the report the
model reads is the last twenty lines of the log, as in step 29.

Run the offline tests from the repository root:

```bash
python run_tests.py 42
python check_snippets.py 42
```

The tests run a small Python command that prints three lines with a
pause between them and check that three `tool_line` calls arrive, one
at a time, before the result does. They check that a long output is
still capped, that a timeout is still a result, that the panel keeps
the last lines and comes down, that a job's log is filled through the
reader, and that a subagent run streams its nested calls.

## What to notice

- Two readers, two paths. The screen gets lines; the model gets the
  whole text, capped as before. Neither path knows about the other.
- The thread reads, the caller waits. A blocking `readline` cannot keep
  a timeout; `process.wait(timeout)` can. That split is the whole
  reason for the thread.
- `text()` is exact. Raw lines with their newlines are joined, so the
  result matches what `subprocess.run` returned. Only the stripped copy
  goes to the screen.
- The panel is transient. It draws over itself while the command runs
  and erases itself when it ends. The finished panel from `ui.tool` is
  the only one that stays in the scrollback.
- One live display at a time. A panel that opens stops the spinner; a
  spinner that starts under a panel shows nothing. Neither raises.
- A job is a foreground command that nobody waits for. Same start,
  same reader; the log is the sink instead of a list, and the screen
  gets the lines only during a `job_wait`.
- The timeout message did not change. The lines that arrived before the
  kill were shown, and the model still reads `Timed out after 60s`.

## Diff from step 41

```bash
diff -r ../step_41_stop_conditions/harness harness
```

Added: `streaming.py` (`popen`, `group_options`, `Reader`, `kill`,
`run`, `TIMEOUT`, `JOIN_GRACE`). Changed: `tools.py` (`bash` runs
through `streaming.run` inside `ui.streaming`), `ui.py` (`ToolStream`,
`Spinner`, `STREAM_LINES`, `streaming`, `tool_line`, `stream_open`,
`stream_close`, `_render_streams`, `_redraw`; `working` returns a
`Spinner`), `jobs.py` (`start` uses `streaming.popen` and a `Reader`;
`Job.record`, `Job.settle`, `Job.reader`, `Job.on_line`; `job_wait`
shows the job live; `report` and `kill_all` settle the reader),
`subagent.py` (`loop` opens a panel and delegates to `turns`;
`progress_line`), `pyproject.toml` (version). `sandbox.run` stays for
callers that want a blocking run. Everything else is unchanged from
step 41.
