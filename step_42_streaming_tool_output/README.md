# Step 42 - Streaming tool output

**What this step adds:** a running command shows its output as it
happens. `harness/streaming.py` runs the command with `subprocess.Popen`
through the sandbox wrapper of step 12, and a `Reader` thread pulls
stdout line by line. Each line goes to `ui.tool_line` the moment it is
read, and a panel on screen shows the last eight lines while the command
runs, redrawn eight times a second whatever the line rate. When the
command exits the panel comes down and the finished panel is printed as
before. The model's result is collected and capped by the step 14 logic
as it was, with one change for the better: stderr is interleaved where
it happened instead of appended at the end, and a timed-out command
hands over what it printed before the kill. Background jobs from step
29 fill their log through the same `Reader`, and `job_wait` shows the
job live while it blocks. A subagent run gets a panel of its own that
lists each nested tool call as it completes.

## Files

```text
step_42_streaming_tool_output/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; four ways to end: reply, finish, a budget, a Stop hook
│   ├── agents.py         agent definitions; each carries a name and a handoffs list
│   ├── ask_user.py       the ask_user tool: a question to the user, answer as result
│   ├── browse.py         the browse tool set over the step 23 browser subagent
│   ├── browser.py        browser tools: one Chromium page driven through Playwright
│   ├── budget.py         the context budget: where the window goes, when to warn
│   ├── checkpoint.py     workspace checkpoints: file copies taken before each edit
│   ├── commands.py       slash commands: /agent and /handoff join /mode, /pipeline
│   ├── compact.py        the compaction agent; its note is kept
│   ├── computer.py       computer use: the screen as a tool
│   ├── config.py         settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py        the late injection block; <env> names the agent and the mode
│   ├── durability.py     the loop detector and the crash-recovery scan
│   ├── evaluate.py       the evaluation harness; run_suite(workspace=DIR) grades a copy
│   ├── handoff.py        handoffs: the conversation moves to another agent definition
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events; Stop joins them, and an exit 2 blocks the stop
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs; output comes through the same Reader thread
│   ├── llm.py            the model call with retries; USAGE_EXTRA asks OpenRouter for the cost
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── modes.py          named permission policies, one layer above the rules
│   ├── permissions.py    the rules, then modes.apply rewrites an allow or an ask
│   ├── pipeline.py       the plan, work, review pipeline behind /pipeline
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line
│   ├── sandbox.py        an OS sandbox for bash; popen() starts a process group, kill_tree() ends it
│   ├── session.py        JSONL session log; {"handoff": name} markers replayed by load(), not by all_sessions()
│   ├── skills.py         skills, unchanged since stage 9
│   ├── stop.py           stop conditions: finish, the three budgets, the Stop hook
│   ├── streaming.py      Popen plus a Reader thread: lines reach the screen as they arrive
│   ├── subagent.py       the subagent loop; a panel lists nested tool calls as it runs
│   ├── todos.py          the plan behind write_todos
│   ├── tools.py          the tool registry; bash runs through streaming.run
│   └── ui.py             rich panels; ToolStream shows the last eight lines of a running tool
├── .agents/
│   ├── .gitignore                     ignores tool_log.txt, the PostToolUse hook's log
│   ├── hooks.json                     hook config: PreToolUse, PostToolUse and the Stop entry
│   ├── block_env_writes.py            example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py                example PostToolUse hook: appends every tool name to a log
│   ├── require_tests.py               example Stop hook: a .py edit must be followed by pytest
│   ├── mcp.json                       MCP config: one stdio server, echo
│   ├── mcp_echo_server.py             a tiny MCP server: two tools, stdio transport
│   ├── skills/explain-code/SKILL.md   the stage 4 skill
│   ├── agents/planner.md              definition: reads the code, returns a numbered plan
│   ├── agents/worker.md               definition: carries out one plan step with the edit tools
│   ├── agents/reviewer.md             definition: judges a change; may hand off to coder
│   ├── agents/router.md               definition: reads the request, hands off to a specialist
│   └── agents/coder.md                definition: writes and tests code; may hand off to reviewer
├── evals/           three step 30 tasks: task.md, check.py or expect.txt, workspace/
├── capstone/        the end-to-end task, carried over from step 38
│   ├── task.md         the brief: a FastAPI todo API with SQLite, tests and a README
│   ├── run.py          the runner: one headless harness run, then the eval suite
│   ├── evals/          five checks, one folder each: task.md, check.py; _common.py helpers
│   ├── reference/      hand-written solution that proves the checks are passable
│   │   ├── app.py        the todo API: FastAPI on top of a SQLite file
│   │   ├── test_app.py   its tests; every test gets an empty database
│   │   └── README.md     its README, with the run section check 4 looks for
│   ├── report.json     the recorded run: calls, tokens, cost and the check results
│   ├── SCORECARD.md    the recorded run as a markdown scorecard, 4/5
│   └── transcript.md   the recorded run's messages, readable
├── AGENTS.md        project instructions the harness reads into its prompt
├── test_step.py     offline tests: a slow Python command plays the streaming tool; timeout, huge output, stderr order
├── pyproject.toml   package metadata; version 0.42.0
└── README.md        this file
```

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
would have had from `subprocess.run`. The cap and the spill file are
untouched. Two things about the text did change, both for the better:
step 41 returned all of stdout and then all of stderr, and this step
merges them on one pipe, so an error message sits next to the line
that caused it; and a command that times out hands the model the lines
that arrived before the kill instead of nothing.

### What breaks without it

`harness run the tests` on a suite that takes ninety seconds is ninety
seconds of a spinner. The user cannot tell a slow suite from a hung
one, and cannot press ctrl-c on the right test, because nothing is on
screen until `subprocess.run` returns - or until the sixty-second
timeout kills the suite and the output arrives all at once, too late to
act on. With this step the lines scroll past as pytest prints them, and
the user sees the test that hangs while it is hanging.

One live display at a time is the constraint the UI works under. rich
draws a live region for the spinner and would draw another for the
panel. The panel opens while a tool runs, and the spinner turns while
the model thinks, so the two rarely meet. When they do - a subagent
thinking while a parallel `bash` call runs - the panel stops the
spinner and takes over, and a spinner started while a panel is open
shows nothing. The panel stands in for it either way.

The other constraint is the reader thread. It sits between the child
and the pipe: every line it spends time on is a line the child waits
to write once the pipe buffer is full. A redraw per line would make a
command that prints two hundred thousand lines ten times slower than
it was, and a verbose test run could go from "works" to "timed out"
because of the screen. So the reader only appends to a deque; the
`Live` display pulls the panels itself, `REFRESH_PER_SECOND` times a
second, and the child never waits on the terminal.

## The code, piece by piece

### 1. The start

`harness/streaming.py`:

```python
def popen(command):
    ...
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
```

The same wrapper as `sandbox.run`: seatbelt on macOS, bubblewrap on
Linux, a plain shell - `cmd.exe` - on Windows. stderr is merged into
stdout so the lines keep their order. `bufsize=1` makes the pipe
line-buffered on this side; `encoding="utf-8"` with `errors="replace"`
decodes what a UTF-8 child prints and keeps one stray byte from ending
the read. stdin is closed, so a command that waits for a keyboard gets
an end of file instead of hanging the turn. `sandbox.ENV` turns the
pagers off and keeps git from prompting. The process gets a group of its
own (`CREATE_NEW_PROCESS_GROUP` on Windows, `start_new_session`
elsewhere), so a kill reaches the children it started. This is the
start `sandbox.run` uses for a foreground command and step 29 used for
jobs; both paths now share it.

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
        ...
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

    def text(self):
        """The whole output so far, exactly as the process wrote it."""
        return "".join(self.lines or [])
```

One thread per command. It blocks on the pipe, and every line it gets
goes two ways: the raw line, newline included, into the list, and the
stripped line into the callback. `text()` joins the raw lines, so the
output is what `subprocess.run` would have returned. `keep=False` is for
background jobs: their log file is the record, and a server that prints
for an hour must not fill a list in memory. A callback that raises - a
render error, a job log that was deleted under it - is dropped and the
reading goes on, so the model still gets the whole output when the
screen cannot show it; the alternative is a dead thread, a broken pipe
in the child and a truncated result with no error.

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
    except subprocess.TimeoutExpired as expired:
        kill(process)
        reader.join(JOIN_GRACE)
        raise subprocess.TimeoutExpired(command, timeout, output=reader.text()) from expired
    except BaseException:
        kill(process)
        raise
    reader.join()  # the process has ended: the pipe is closing, the last lines are moments away
    return reader.text()
```

The calling thread does not read; it waits, with the timeout. The
reader thread does the reading. This is why the timeout still works: a
`readline` blocks for as long as the process is silent, and a thread
that is stuck on it cannot count seconds. `process.wait` can. On expiry
`kill` ends the process tree, `taskkill /F /T` on Windows and
`killpg` elsewhere, the reader gets `JOIN_GRACE` seconds to drain what
is left (a grandchild may still hold the pipe), and a `TimeoutExpired`
with `output` set to the lines so far comes out, the way
`subprocess.run` raised it, so `bash` keeps its handling. A Ctrl-C
kills the command too. After a normal exit the reader is joined
without a limit: the child closed its end, so the join is a matter of
moments, and every line is in before `text()` is read.

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
            partial = (expired.stdout or "") + (expired.stderr or "")
            return history.cap(f"Timed out after {expired.timeout}s and was killed. Output so far:\n{partial}")
    return history.cap(output or "(no output)")
```

`ui.streaming` opens the panel and returns a callable; each call adds
one line. The `with` block closes the panel on the way out, on a normal
exit, a timeout or an exception. The last line is the step 14 cap,
unchanged, with the same spill file when the output is long. The
timeout result carries the partial output, capped the same way: the
model sees which test hung, not only that one did.

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
        self.ui.tool_line(self, line)

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
    def tool_line(self, stream, line):
        """One line of output from a running tool: it joins the stream's panel, which the live display redraws on its own clock."""
        with self._streams_lock:
            stream.lines.append(line)
            stream.count += 1
```

and the display that draws them:

```python
            live = Live(get_renderable=self._render_streams, console=self.console, transient=True, refresh_per_second=REFRESH_PER_SECOND)
```

Lines arrive on reader threads, several at once when a reply had
parallel `bash` calls, so the list of open streams is guarded by a
lock, and `tool_line` does nothing but append under it. `_redraw`
starts one rich `Live` for the first open panel, with
`get_renderable` so the display pulls `_render_streams` itself eight
times a second, and `stream_close` stops it when the last panel goes.
A million lines cost the screen eight redraws a second, not a million.
The `Live` is transient: it erases itself on stop, and `ui.tool` prints
the finished panel in its place. Headless (`-p`), `self.live` is False
and no panel is drawn; the lines still go to the deque and nothing
else.

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

Prerequisites: Python 3.10+, `API_KEY` (and optionally `BASE_URL`,
`MODEL`) in the environment or in `~/.simple-harness/env`.

```bash
pip install -e .
harness
```

```powershell
pip install -e .
harness
```

### Expected output

Ask for something slow:

```text
> run the test suite

  ╭─ running · 14 lines ─────────────────────────────────────────╮
  │ bash pytest -v                                               │
  │ ──────────────────────────────────────────────────────────── │
  │ … 6 earlier lines                                            │
  │ test_app.py::test_create PASSED                              │
  │ test_app.py::test_list PASSED                                │
  │ test_app.py::test_get_missing PASSED                         │
  │ test_app.py::test_update PASSED                              │
  │ test_app.py::test_delete PASSED                              │
  │ test_app.py::test_delete_missing PASSED                      │
  │ test_app.py::test_complete PASSED                            │
  │ test_app.py::test_readme PASSED                              │
  ╰──────────────────────────────────────────────────────────────╯
```

The `bash` panel appears with the command in its header and `running ·
0 lines` in its title. Lines fill in as pytest prints them; after eight,
the oldest scroll off and the title counts them. When pytest exits the
panel disappears and the usual finished panel takes its place, with the
same twelve-line preview as before:

```text
  ╭──────────────────────────────────────────────────────────────╮
  │ bash pytest -v                                               │
  │ ──────────────────────────────────────────────────────────── │
  │ ============================= test session starts ========== │
  │ ...                                                          │
  │ ============================== 12 passed in 1.84s ========== │
  ╰──────────────────────────────────────────────────────────────╯

  3,102 prompt (estimate 3,080) · 41 completion · $0.0035

All 12 tests pass.
```

A command that runs past the limit ends like this, and the model reads
the same text:

```text
  ╭──────────────────────────────────────────────────────────────╮
  │ bash python slow_suite.py                                    │
  │ ──────────────────────────────────────────────────────────── │
  │ Timed out after 60s and was killed. Output so far:           │
  │ test_one ... ok                                              │
  │ test_two ... ok                                              │
  │ test_three ...                                               │
  ╰──────────────────────────────────────────────────────────────╯
```

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

```powershell
python run_tests.py 42
python check_snippets.py 42
```

The tests run a small Python command that prints three lines with a
pause between them and check that three `tool_line` calls arrive, one
at a time, before the result does. They check that a long output is
still capped, that a timeout is a result that carries `line 0`, that a
line never redraws the panel itself, that a huge output is complete
under the live panel, that stderr lines land where they were printed
and UTF-8 survives, that a callback that raises does not lose the
output, that the panel keeps the last lines and comes down, that a
job's log is filled through the reader, and that a subagent run
streams its nested calls.

## Error handling

- **A bad tool call.** As in step 39: malformed arguments, an unknown
  tool, a missing argument and a tool that raises each become one
  `Error:` tool message, and the panel that opened for the call comes
  down with it (`with` closes it on any exit).
- **A failing command.** Its exit text is in the output like any other
  line, in the order it was printed; the model reads it at the
  position it happened.
- **A timeout.** `Timed out after 60s and was killed. Output so far:`
  with the lines that arrived, capped. The tree is killed with
  `taskkill /F /T` or `killpg`; the reader gets two seconds to drain.
- **Ctrl-C during a command.** `run` kills the process tree and
  re-raises; the steer prompt opens and the call is recorded as
  `INTERRUPTED`. On Windows `Popen.wait(timeout)` is one wait call, so
  the ctrl-c is seen when it returns: at the command's end or at the
  timeout, not in between.
- **A dead model call.** After the retries the turn ends with a note,
  as in step 41; no panel is involved.
- **A screen that cannot draw.** A `LiveError` (another live display
  owns the terminal) leaves the panel unopened and the next open or
  close tries again; a callback that raises is dropped and the output
  is kept.
- **Leaving.** `/exit`, `/quit`, ctrl-d, or ctrl-z then enter on
  Windows.

## Gotchas / What this is not

- The result is not byte for byte step 41's. stderr is interleaved
  with stdout in arrival order, and a stray non-UTF-8 byte becomes
  `U+FFFD` instead of an exception.
- The panel shows the last eight lines and a count; it is not a
  scrollback. The finished panel's twelve-line preview and the spill
  file are the record.
- Eight redraws a second is the ceiling, so a line can be on screen
  up to 125 ms after it was printed. The order is exact; the timing is
  not.
- Windows: no OS sandbox, the shell is `cmd.exe`, and the child is in
  its own process group, which means it ignores the console's ctrl-c;
  the harness kills it with `taskkill /T` once `wait` returns.
- A background job's lines show only during a `job_wait`. Between
  waits they go to the log, and `job_status` reads the tail.
- The subagent panel lists nested calls as they complete, one line
  each; the nested `bash` calls stream their own lines in their own
  panels below it.

## What to notice

- Two readers, two paths. The screen gets lines; the model gets the
  whole text, capped as before. Neither path knows about the other.
- The thread reads, the caller waits. A blocking `readline` cannot keep
  a timeout; `process.wait(timeout)` can. That split is the whole
  reason for the thread.
- `text()` is exact. Raw lines with their newlines are joined, so the
  result is what `subprocess.run` would have returned from the same
  merged pipe. Only the stripped copy goes to the screen.
- The panel is transient. It draws over itself while the command runs
  and erases itself when it ends. The finished panel from `ui.tool` is
  the only one that stays in the scrollback.
- One live display at a time. A panel that opens stops the spinner; a
  spinner that starts under a panel shows nothing. Neither raises.
- A job is a foreground command that nobody waits for. Same start,
  same reader; the log is the sink instead of a list, and the screen
  gets the lines only during a `job_wait`.
- The timeout hands over what arrived. The lines before the kill were
  shown, and the model reads them too under `Output so far:`, so it
  can tell which test hung.
- The screen never slows the child. The reader appends; the display
  pulls at its own rate. A command's speed is the same with the panel
  and without it.

## Diff from step 41

```bash
diff -r ../step_41_stop_conditions/harness harness
```

Added: `streaming.py` (`popen`, `Reader`, `kill`, `run`, `TIMEOUT`,
`JOIN_GRACE`). Changed: `tools.py` (`bash` runs through
`streaming.run` inside `ui.streaming`; the timeout result carries the
partial output, as since step 30), `ui.py` (`ToolStream`, `Spinner`, `STREAM_LINES`,
`REFRESH_PER_SECOND`, `streaming`, `tool_line`, `stream_open`,
`stream_close`, `_render_streams`, `_redraw`; `working` returns a
`Spinner`), `jobs.py` (`start` uses `streaming.popen` and a `Reader`;
`Job.record` keeps one open log handle, `Job.settle`, `Job.reader`,
`Job.on_line`, `Job.handle`; `job_wait` shows the job live; `report`
and `kill_all` settle the reader), `subagent.py` (`loop` opens a panel
and delegates to `turns`; `progress_line`), `pyproject.toml`
(version). `sandbox.run` stays for callers that want a blocking run.
Everything else is unchanged from step 41.

## What the next step adds

Step 43 adds extensions: every `.agents/extensions/*.py` exports
`apply(ctx)` and registers tools, commands, hooks, prompt sections and
agents through one context, with the same permission gate as the
built-in tools.
