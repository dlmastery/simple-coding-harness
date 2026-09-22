# Step 29 - Background jobs and parallel subagents

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 28 - Plan mode and structured output](../step_28_plan_mode/README.md). Next: [Step 30 - Evaluation harness](../step_30_eval/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** two ways to do more than one thing at a time.
`bash_background` starts a shell command and returns a job id at once; the
command keeps running while the conversation goes on. `job_status`,
`job_wait` and `job_kill` look at it, block on it and stop it. The late
block lists the running jobs in a `<jobs>` tag, and the session end kills
whatever is left. The `task` tool takes a list of `descriptions` and runs
one subagent per item on a thread pool, each with its own message list,
and returns the reports joined under one header each. A `/jobs` command
lists the jobs.

## Why jobs, and why parallel subagents

`bash` waits for the command and kills it after a timeout. That is right
for a grep and wrong for a dev server, a watcher or a long test run. Up to
now the model had no way to start one of those and carry on: ask the step
28 harness to "start the dev server and then check the home page", and
`bash python serve.py` blocks for 60 seconds, is killed with its process
tree, and the model reports that the server "timed out". A background
job is the missing shape: start it, get an id, look at its output later,
stop it when done. The job runs through the same sandbox wrapper and the
same permission rules as `bash`, so the new tool opens no new door.

The `task` subagent from step 15 answers one question in its own context
window. Often the model has three questions that do not depend on each
other. Sending them one at a time costs three round trips. Sending them
together costs one: each question gets its own subagent, the subagents run
at the same time, and the reports come back in one result. The thread
pool from step 22 already made the tool registry safe for this; what the
step has to add is one lock around the approval prompt, because two
subagents can now ask you a question at the same moment.

## The code, piece by piece

### 1. Starting a job

`harness/jobs.py`:

```python
def start(command):
    """Start a command in the background and return its Job."""
    handle = tempfile.NamedTemporaryFile(prefix="harness-job-", suffix=".log", delete=False)
    handle.close()
    log = Path(handle.name)

    sandboxed = sandbox.wrap(command)  # argv inside the OS sandbox, or None for a plain shell
    options = {}
    if sys.platform == "win32":
        # its own process group, so job_kill can signal the whole tree at once
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True  # the same idea: a group of its own

    with open(log, "wb") as out:
        process = subprocess.Popen(
            sandboxed or command,
            shell=sandboxed is None,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            **options,
        )
    job = Job(next_id(), command, process, log, time.time())
    JOBS[job.id] = job
    return job
```

`sandbox.wrap` is the same call `bash` makes: it returns the argv that
runs the command inside the OS sandbox, or `None` when there is no
sandbox, in which case the command runs through the shell. The output
goes to a log file, not a pipe, so nothing has to read it while the job
runs. The process gets a group of its own. On Windows that is
`CREATE_NEW_PROCESS_GROUP`; elsewhere it is a new session. Both exist so
that a kill can reach the children too, not only the shell that started
them.

A job goes through four states, and `Job.state()` names each:

```text
started ──▶ running for Ns ──▶ exited with code N ──▶ (reported: seen)
                 │
                 └── job_kill / kill_all ──▶ killed (exit code N) ──▶ (reported: seen)
```

`<jobs>` lists a job while it is running, keeps listing it once it has
exited or been killed until a `job_status`, `job_wait` or `job_kill`
result has shown the model that, and drops it after.

### 2. Reporting and killing

`harness/jobs.py`:

```python
def report(job):
    """One status report: id, state, command and the tail of the log."""
    job.seen = not job.running()  # an ended job leaves the late block once reported
    return (
        f"{job.id}: {job.state()}\n"
        f"command: {job.command}\n"
        f"log: {job.log}\n"
        f"--- last {TAIL_LINES} lines ---\n"
        f"{job.tail()}"
    )
```

```python
def terminate(process):
    """End a process and the children it started.

    Windows: a CTRL_BREAK to the process group, then taskkill for the whole
    tree, always: the shell may have left on the signal while a grandchild
    ignored it. Elsewhere: SIGTERM to the session, then SIGKILL to the
    session, which no process can ignore.
    """
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)  # reaches the whole group
            process.wait(timeout=KILL_GRACE)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)  # a no-op once the tree is gone
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=KILL_GRACE)
        except (OSError, AttributeError, subprocess.TimeoutExpired):
            pass
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (OSError, AttributeError):
            pass
    try:
        process.wait(timeout=KILL_GRACE)
    except subprocess.TimeoutExpired:
        process.kill()
```

Every tool result about a job has the same shape: the state on the first
line, the command, the log path, then the last twenty lines of output.
`job_status` returns it at once, `job_wait` after the process ends or the
timeout passes, `job_kill` after the kill.

The kill is an escalation, and the last rung always runs. On Windows the
group gets a `CTRL_BREAK`, which a well-behaved server takes as its cue
to shut down; then `taskkill /T` walks the whole tree whether or not the
shell already left, because `cmd.exe` exiting on the signal says nothing
about the `python` it started. Elsewhere `SIGTERM` goes to the session,
then `SIGKILL` to the session: a grandchild that ignores `SIGTERM` (a
server with its own handler, a stuck child) does not get to keep the
port and the log file. `process.kill()` on the leader is the fallback
for a process that has left its group.

### 3. The tools and the session end

`harness/jobs.py`:

```python
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
```

```python
def job_wait(job_id: str, timeout: int = DEFAULT_WAIT) -> str:
    """Block until the job ends or the timeout passes, then report.

    The wait is capped at MAX_WAIT: the whole turn, and the prompt, block
    for as long as this runs, and a model that asks for an hour gets five
    minutes and a report it can act on.
    """
    job = find(job_id)
    if isinstance(job, str):
        return job
    try:
        timeout = min(int(timeout or DEFAULT_WAIT), MAX_WAIT)
    except (TypeError, ValueError):
        return f"Error: timeout must be a number of seconds, got {timeout!r}"
    try:
        job.process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"{job.id} is still running after {timeout}s.\n" + report(job)
    return report(job)
```

`job_wait` is the one tool here that blocks the turn, so it is bounded:
`DEFAULT_WAIT` is 60 seconds, `MAX_WAIT` is 300, and the schema tells the
model to poll with `job_status` for anything longer. A timeout that is
not a number (`"60"` from a model that quotes everything is fine, `"a
minute"` is not) is an `Error:` result, not a crash.

```python
def kill_all():
    """Session end: kill every running job and delete every log."""
    for job in list(JOBS.values()):
        job.killed = job.killed or job.running()
        terminate(job.process)
    for job in list(JOBS.values()):
        try:
            job.log.unlink(missing_ok=True)
        except OSError:
            pass
    JOBS.clear()
```

`harness/agent.py`:

```python
        browser.browser_close()  # a no-op unless a browse call opened one
        mcp_client.close_all()   # stops every MCP server that was started
        jobs.kill_all()          # a background job never outlives the session
        hooks.run_hooks("SessionEnd")
```

The four job tools join `TOOLS` and `TOOL_SCHEMAS` in `tools.py` like any
other. `kill_all` runs in the `finally` block of `main`, next to the
browser and the MCP servers: a job started in the chat ends with the
chat, and its log goes with it. `JOBS` is iterated over a copy
everywhere, because a pool thread may be adding a job while the main
thread lists them.

### 4. Same rules as bash

`harness/permissions.py`:

```python
    if name in ("bash", "bash_background"):
        command = args.get("command", "")
        if not command:
            return "deny", "bash: missing argument 'command'"
        action = decide(command)
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {command}"
        how = "run in background" if name == "bash_background" else "run"
        return action, f"{how}: {command}"
```

A background command is rated by the same rules as a foreground one:
`ls` is allowed, `python serve.py` asks, `rm -rf build` is denied. The
prompt says `run in background:` so the user knows what they are
approving. The three tools that only look at, wait for or stop a job are
allowed without asking. In plan mode `bash_background` is not in the tool
set, so the check denies it before the rules are consulted.

One consequence to know: the rule table allows `pytest*` and `python -m
pytest*`, so `bash_background pytest` starts an unattended test run
without a prompt. That is the intended use, and it is also why the job
tools are withheld from subagents: a subagent that started a job would
hand back a report and leave the process running until the session ends.

### 5. The late block

`harness/context.py`:

```python
def jobs_note():
    """The background jobs the model should know about, or nothing."""
    listing = jobs.jobs_prompt()
    return f"\n<jobs>\n{listing}\n</jobs>" if listing else ""
```

`harness/jobs.py`:

```python
def jobs_prompt():
    """One line per job the model should know about. Empty when there is none.

    Running jobs are always listed. A job that ended is listed until a
    report has shown the model that it ended.
    """
    lines = []
    for job in list(JOBS.values()):
        if job.running():
            lines.append(f"{job.id}: {job.state()} - {job.command}")
        elif not job.seen:
            lines.append(f"{job.id}: {job.state()} - {job.command} (job_status shows its output)")
    return "\n".join(lines)
```

The `<jobs>` block comes after `<plan>` and before `<memory>`. A running
job is listed on every call, with how long it has been running. A job
that ended stays listed until a report has shown the model that it ended,
then it leaves the block. When there are no jobs there is no block.

### 6. Several subagents at once

`harness/subagent.py`:

```python
def guarded(number, description):
    """explore(), but a crash becomes a report: one failure must not sink the others."""
    try:
        return explore(description, tag=number)
    except Exception as failure:  # noqa: BLE001
        who = f"subagent {number}" if number is not None else "the subagent"
        return f"Error: {who} failed with {type(failure).__name__}: {failure}"


def parallel(descriptions):
    """Run one subagent per description at the same time; join the reports in order."""
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="subagent") as pool:
        futures = [pool.submit(guarded, number, description) for number, description in enumerate(descriptions, 1)]
        reports = [future.result() for future in futures]
    return "\n\n".join(
        f"## subagent {number}: {title(description)}\n\n{report}"
        for number, (description, report) in enumerate(zip(descriptions, reports), 1)
    )


def task(description: str = None, descriptions: list = None) -> str:
    """The exploration subagent, or several of them at once.

    One description runs one subagent and returns its report. A list of
    descriptions runs one subagent per item concurrently and returns the
    reports joined, one header per subagent, in the order of the list.
    """
    if descriptions:
        return parallel([str(d) for d in descriptions])
    if description:
        return guarded(None, str(description))  # a crash is a report here too
    return "Error: give a description, or a list of descriptions to run several subagents at once."
```

`loop()` is unchanged in what it does: a fresh message list, the same
`call_llm`, the same `execute_all`. `parallel` submits one `loop` per
description to a pool of at most four threads and collects the futures in
the order given, so the reports come back in that order whatever the
finishing order was. A subagent that raises becomes an error section; the
others still report. The single-description path goes through `guarded`
too, so a subagent that raises is `Error: the subagent failed with ...`
as a tool result, not a crash of the main turn. The tool result
is one string with a `##` header per subagent, so the main agent can tell
which answer belongs to which question.

### 7. Tagged panels, and one prompt at a time

`harness/subagent.py`:

```python
        with ui.working(label) if tag is None else nullcontext():
            message, usage = call_llm(messages, tools=tools)  # rule 2
```

`harness/ui.py`:

```python
    def tool(self, name, args, result, nested=False, tag=None):
        """One tool call and its result. tag names the subagent, when several run at once."""
        if name == "write_todos" and args.get("todos") and not result.startswith("Error"):
            return self.todos(args["todos"])
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
        title = Text(f"subagent {tag}", style=f"italic {MUTED}") if tag is not None else None
```

Parallel loops print at the same time, so their panels interleave on
screen. Each nested panel carries the number of the subagent that
produced it, and the header panel reads `subagent 2 · own context`. The
spinner is off in a parallel loop: the console allows one live display,
and four loops would fight over it.

The terminal holds one question at a time. Two subagents whose calls
both rate `ask` (a `python -c` each, or an MCP tool without `MCP_ALLOW`)
would each open a prompt from their own thread, and `prompt_toolkit`
refuses a second prompt while one is open. `ui.approve` takes
`APPROVE_LOCK` around the whole question, so the second subagent waits
for the first answer; its panels may still print above the open prompt,
which is why the prompt repeats the reason. `ui.usage` takes `USAGE_LOCK`
around the totals for the same reason: `+=` from two threads loses one
of the two.

### 8. The schema

`harness/subagent.py`:

```python
                "descriptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Several stand-alone questions that do not depend on "
                        "each other. One subagent per item, run in parallel. "
                        "Use this instead of description, not with it."
                    ),
                },
            },
        },
```

`description` or `descriptions`, at least one. Both are optional in the
schema - a root-level `anyOf` is rejected by strict-schema providers, and
the prose says which to use - and `task()` says so again in its error
result if neither arrives.

## Run it

Prerequisites are those of step 28: Python 3.11+, `API_KEY` (and
`BASE_URL`/`MODEL` if not OpenRouter) in the environment or in
`~/.simple-harness/env`. Start from this directory so `.agents/` is
found.

bash:

```bash
cd harness/04_tools/step_29_jobs_parallel_subagents
pip install -e .
harness
```

PowerShell:

```powershell
cd harness/04_tools/step_29_jobs_parallel_subagents
pip install -e .
harness
```

Then:

```text
> start the test suite in the background, then tell me how the todos module and the memory module are structured
```

### Expected output

```text
  ╭──────────────────────────────────────────────────────────────────╮
  │ bash_background {"command": "python -m pytest -q"}               │
  │ ──────────────────────────────────────────────────────────────── │
  │ Started job-1: python -m pytest -q                               │
  │ Output goes to C:\Users\you\AppData\Local\Temp\harness-job-…log. │
  │ Call job_status to check on it, job_wait to block for it,        │
  │ job_kill to stop it.                                             │
  ╰──────────────────────────────────────────────────────────────────╯

  ╭─ subagent 1 · own context ───────────────────────────────────────╮
  │ Describe the structure of harness/todos.py: ...                  │
  ╰──────────────────────────────────────────────────────────────────╯
  ╭─ subagent 2 · own context ───────────────────────────────────────╮
  │ Describe the structure of harness/memory.py: ...                 │
  ╰──────────────────────────────────────────────────────────────────╯
      ╭─ subagent 2 ─────────────────────────────────────────────────╮
      │ read_file {"path": "harness/memory.py"}                      │
      ╰──────────────────────────────────────────────────────────────╯
      ╭─ subagent 1 ─────────────────────────────────────────────────╮
      │ read_file {"path": "harness/todos.py"}                       │
      ╰──────────────────────────────────────────────────────────────╯

  ╭──────────────────────────────────────────────────────────────────╮
  │ task {"descriptions": ["Describe the structure of ...", ...]}    │
  │ ──────────────────────────────────────────────────────────────── │
  │ ## subagent 1: Describe the structure of harness/todos.py: ...   │
  │                                                                  │
  │ todos.py holds one module-level list, TODOS, ...                 │
  │                                                                  │
  │ ## subagent 2: Describe the structure of harness/memory.py: ...  │
  │                                                                  │
  │ memory.py stores one markdown file per memory ...                │
  ╰──────────────────────────────────────────────────────────────────╯

  ╭──────────────────────────────────────────────────────────────────╮
  │ job_status {"job_id": "job-1"}                                   │
  │ ──────────────────────────────────────────────────────────────── │
  │ job-1: exited with code 0                                        │
  │ command: python -m pytest -q                                     │
  │ log: C:\Users\you\AppData\Local\Temp\harness-job-k3n1.log        │
  │ --- last 20 lines ---                                            │
  │ ........................                                         │
  │ 24 passed in 26.77s                                              │
  ╰──────────────────────────────────────────────────────────────────╯

  The tests pass (24 in 27s). todos.py keeps ... memory.py stores ...
```

The late injection panel after the first call carries `<jobs>` with
`job-1: running for 2s - python -m pytest -q`; after the `job_status`
result it is gone. Type `/jobs` to list every job of the session with its
state. Exit with ctrl-d while a job is running: the process is killed on
the way out.

Run the offline tests from the repository root:

```bash
python run_tests.py 29
python check_snippets.py 29
```

The job tests start real processes (`python -c` sleeps, a grandchild that
ignores its first signal) and kill them; they take about 20 seconds.

## Error handling

- **A job id that does not exist**: `Error: no job 'job-9'. Known jobs:
  job-1.`
- **A command that cannot start** (the OS refuses): `Error: could not
  start the job: ...`. A command that starts and fails at once is a job
  that `exited with code 1`; `job_status` shows its output.
- **`job_wait` past the cap**: `job-1 is still running after 300s.`
  followed by the report; a non-numeric timeout is `Error: timeout must
  be a number of seconds, got ...`.
- **`job_kill` on a job that already ended** reports `job-1 had already
  ended.` and the state; killing twice is harmless.
- **A subagent that crashes** (something raises past the guards; a
  failed model call is already the loop's own `(the subagent's model
  call failed: ...)` report) is the section `Error: subagent 2 failed
  with ValueError: ...`; the other sections are their reports. A single
  subagent gives `Error: the subagent failed with ...`.
- **A subagent that names a withheld tool** (`bash_background`,
  `write_file`) gets `Blocked by policy: bash_background is not
  available to this agent`.
- **A tool call with broken arguments** is `Error: the arguments of
  <tool> are not a JSON object: ...`; an unknown tool `Error: no tool
  named '...'.`; a tool that raises `Error: <Type>: <message>`.
- **A failing foreground command** returns its output and exit code; past
  60s it is killed with its tree: `Timed out after 60s and was killed.
  Output so far: ...`. A background job has no timeout.
- **A dead model call** ends the turn with `model call failed: ...`; the
  jobs keep running and `<jobs>` still lists them on the next turn.
- **ctrl-c mid-turn**, including during a `job_wait`, answers the
  unfinished tool calls with `(interrupted before this tool ran)` and
  returns to the prompt; the job itself is not killed.
- **More than 40 model calls in one turn** stops the turn with a note.

To leave: `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or
ctrl-c at the prompt. Every job is killed and every log deleted on the
way out, after the browser and the MCP servers.

## Gotchas / What this is not

- **`job_wait` blocks the whole turn**, and the prompt with it. Nothing
  prints while it waits, and ctrl-c is the only way out. Keep the timeout
  short and poll with `job_status`; the cap is five minutes.
- **The log lives in the temp directory** and is deleted at session end.
  It is the job's whole output; `job_status` shows the last twenty lines.
  Do not `bash tail -f` it: that is a foreground command with a 60s
  timeout.
- **Kill semantics differ by OS.** Windows: `CTRL_BREAK` to the group,
  then `taskkill /F /T`. POSIX: `SIGTERM` to the session, then
  `SIGKILL`. A process that has called `setsid` itself is outside the
  group and survives; nothing short of a process tree walk would catch
  it, and the harness does not do one.
- **Ports are not released instantly.** A killed server's port can stay
  in `TIME_WAIT` for a minute; a job started to replace it may fail to
  bind.
- **Parallel subagents and prompts.** Each `ask`-rated call from a
  subagent is a question on your terminal, serialised by `APPROVE_LOCK`
  but printed among other subagents' panels. For subagent work through
  an MCP server, set `MCP_ALLOW` for its read tools first; for shell
  work, stick to allow-listed commands.
- **Token totals under parallel runs** are exact (locked) but the per-call
  usage lines interleave on screen in finishing order.
- **`bash_background pytest` needs no approval.** Same as `bash pytest`;
  the difference is that it returns at once.
- **Jobs are process state.** `--resume` and `/sessions` know nothing
  about jobs from an earlier process; they were killed when it exited.
- **Subagents cannot start jobs by schema, and by rule.** The job tools
  are withheld from `toolset()`, and `execute_all(..., allowed=...)`
  refuses a call to a tool the subagent was not offered, so a
  hallucinated `bash_background` is `Blocked by policy`.
- **Windows:** the tool called `bash` and the jobs run through
  `cmd.exe`, there is no OS sandbox, and `CTRL_BREAK_EVENT` only reaches
  processes that share the console; the `taskkill` that follows is what
  actually ends a detached one.

## What to notice

- A job is `Popen` where `bash` is `run`. Same wrapper, same rules, same
  shell. The only new decision is where the output goes, and a file wins
  over a pipe because nobody has to drain it.
- Kill the group, not the process, and always take the last rung. The
  shell that started the command is the process the harness holds; the
  command is its child. A process group is what makes one signal reach
  both, and `SIGKILL`/`taskkill /T` is what makes it stick.
- The late block remembers what the model started. A job id in a tool
  result from ten turns ago is easy to lose; `<jobs>` puts the running
  ones in front of the model on every call.
- Parallel subagents share almost nothing. Each `loop` owns its message
  list, and the registry was made thread-safe for parallel tool calls in
  step 22. Two things did have to be locked: the approval prompt and the
  usage totals. Both are a `threading.Lock` in `ui.py`.
- Order by submission, not by completion. The futures are read in the
  order the descriptions came, so the model can match answers to
  questions by position as well as by header.
- A fake model for parallel loops must not count calls. The test picks
  the script by the text of the request and the step by the length of
  the message list, so three threads can call it in any order.

## Files

```text
step_29_jobs_parallel_subagents/
├── harness/
│   ├── llm.py                        the model call; the prompt explains jobs and parallel subagents
│   ├── tools.py                      the registry; bash_background, job_status, job_wait, job_kill
│   ├── agent.py                      the loop; the session end kills the background jobs
│   ├── jobs.py                       background jobs: Popen through the sandbox, a job table, kill_all
│   ├── subagent.py                   the subagent loop; task runs one subagent per description
│   ├── permissions.py                allow / ask / deny; a job is rated by the bash rules
│   ├── context.py                    the late injection block, with a <jobs> tag
│   ├── commands.py                   slash commands; /jobs lists jobs, running or ended
│   ├── plan.py                       plan mode: MODE, toolset(), PLAN_SCHEMA, submit_plan, approval
│   ├── hooks.py                      hooks: reads hooks.json, runs commands and functions per event
│   ├── mcp_client.py                 MCP client: starts each server over stdio, registers its tools
│   ├── memory.py                     persistent memory: markdown files with front matter
│   ├── compact.py                    the compaction agent; its handoff note is kept
│   ├── history.py                    transcript trimming: cap, strip, fit, image messages
│   ├── browse.py                     the browser subagent
│   ├── browser.py                    browser tools: one Chromium page through Playwright
│   ├── computer.py                   computer use: screen size, screenshot, act
│   ├── todos.py                      the plan: write_todos and the todo list
│   ├── skills.py                     skills: SKILL.md discovery and index
│   ├── session.py                    append-only JSONL log, load() with repair, /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash, and the process-group plumbing
│   ├── config.py                     settings: environment first, ~/.simple-harness/env fills gaps
│   ├── prompt.py                     the input line, through prompt_toolkit
│   ├── ui.py                         rich panels; nested panels carry the subagent's number; prompt and usage locks
│   └── __init__.py                   package marker
├── .agents/
│   ├── hooks.json                    hook config: block .env writes, log every tool name
│   ├── block_env_writes.py           example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: appends every tool name to a log
│   ├── .gitignore                    ignores tool_log.txt, the log hook's output
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── test_step.py                      offline tests against a fake model; real processes for the jobs
├── pyproject.toml                    package metadata; version 0.29.0
└── README.md                         this file
```

## What the next step adds

Step 30 adds `harness eval <suite>`: a runner that gives each task of a
suite a fresh workspace and session, runs one turn, grades the outcome
with a checker script, an expected string or a model judge, and prints
pass rates, time, tokens and cost.

## Diff from step 28

```bash
diff -r ../step_28_plan_mode/harness harness
```

Added: `jobs.py` (`Job`, `start`, `terminate`, `report`,
`bash_background`, `job_status`, `job_wait` with `MAX_WAIT`, `job_kill`,
`running`, `jobs_prompt`, `kill_all`, `JOB_SCHEMAS`, `JOB_TOOLS`).
Changed: `subagent.py` (`MAX_PARALLEL`, job tools in `WITHHELD`, `loop`
takes `tag`, `explore`, `title`, `guarded` on both paths, `parallel`,
`task` with `descriptions`, `TASK_SCHEMA` with `descriptions`), `tools.py`
(job tools in `TOOLS` and `TOOL_SCHEMAS`), `permissions.py`
(`bash_background` rated like `bash`), `context.py` (`jobs_note`, `<jobs>`
after `<plan>`), `agent.py` (`jobs.kill_all()` at session end), `llm.py`
(prompt text on jobs and parallel subagents), `commands.py` (`/jobs`),
`ui.py` (`tool` and `subagent` take `tag`, `USAGE_LOCK`). Everything else
is unchanged from step 28.
