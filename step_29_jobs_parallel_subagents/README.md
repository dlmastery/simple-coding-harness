# Step 29 - Background jobs and parallel subagents

**What this step adds:** two ways to do more than one thing at a time.
`bash_background` starts a shell command and returns a job id at once; the
command keeps running while the conversation goes on. `job_status`,
`job_wait` and `job_kill` look at it, block on it and stop it. The late
block lists the running jobs in a `<jobs>` tag, and the session end kills
whatever is left. The `task` tool takes a list of `descriptions` and runs
one subagent per item on a thread pool, each with its own message list,
and returns the reports joined under one header each. A `/jobs` command
lists the jobs.

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
│   ├── session.py                    append-only JSONL log, load(), /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash
│   ├── config.py                     settings: environment first, ~/.simple-harness/env fills gaps
│   ├── prompt.py                     the input line, through prompt_toolkit
│   ├── ui.py                         rich panels; nested panels carry the subagent's number
│   └── __init__.py                   package marker
├── .agents/
│   ├── hooks.json                    hook config: block .env writes, log every tool name
│   ├── block_env_writes.py           example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: appends every tool name to a log
│   ├── .gitignore                    ignores tool_log.txt, the log hook's output
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.29.0
└── README.md                         this file
```

## Why jobs, and why parallel subagents

`bash` waits for the command and kills it after a timeout. That is right
for a grep and wrong for a dev server, a watcher or a long test run. Up to
now the model had no way to start one of those and carry on. A background
job is the missing shape: start it, get an id, look at its output later,
stop it when done. The job runs through the same sandbox wrapper and the
same permission rules as `bash`, so the new tool opens no new door.

The `task` subagent from step 15 answers one question in its own context
window. Often the model has three questions that do not depend on each
other. Sending them one at a time costs three round trips. Sending them
together costs one: each question gets its own subagent, the subagents run
at the same time, and the reports come back in one result. The thread
pool from step 22 already made the tool registry safe for this.

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
...
def terminate(process):
    ...
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
```

Every tool result about a job has the same shape: the state on the first
line, the command, the log path, then the last twenty lines of output.
`job_status` returns it at once, `job_wait` after the process ends or the
timeout passes, `job_kill` after the kill. The kill goes to the group
first, so a shell and the program it started die together. If the group
signal fails, the plain `terminate()` and `kill()` on the leader are the
fallback.

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
...
def kill_all():
    """Session end: kill every running job and delete every log."""
    for job in JOBS.values():
        job.killed = job.killed or job.running()
        terminate(job.process)
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
browser and the MCP servers: a job started in the chat ends with the chat.

### 4. Same rules as bash

`harness/permissions.py`:

```python
    if name in ("bash", "bash_background"):
        action = decide(args["command"])
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {args['command']}"
        how = "run in background" if name == "bash_background" else "run"
        return action, f"{how}: {args['command']}"
```

A background command is rated by the same rules as a foreground one:
`ls` is allowed, `python serve.py` asks, `rm -rf build` is denied. The
prompt says `run in background:` so the user knows what they are
approving. The three tools that only look at, wait for or stop a job are
allowed without asking. In plan mode `bash_background` is not in the tool
set, so the check denies it before the rules are consulted.

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
    ...
    lines = []
    for job in JOBS.values():
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
        return f"Error: subagent {number} failed with {type(failure).__name__}: {failure}"


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
    ...
    if descriptions:
        return parallel([str(d) for d in descriptions])
    if description:
        return explore(description)
    return "Error: give a description, or a list of descriptions to run several subagents at once."
```

`loop()` is unchanged in what it does: a fresh message list, the same
`call_llm`, the same `execute_all`. `parallel` submits one `loop` per
description to a pool of at most four threads and collects the futures in
the order given, so the reports come back in that order whatever the
finishing order was. A subagent that raises becomes an error section; the
others still report. The tool result is one string with a `##` header per
subagent, so the main agent can tell which answer belongs to which
question.

### 7. Tagged panels

`harness/subagent.py`:

```python
        with ui.working(label) if tag is None else nullcontext():
            message, usage = call_llm(messages, tools=tools)  # rule 2
```

`harness/ui.py`:

```python
    def tool(self, name, args, result, nested=False, tag=None):
        """One tool call and its result. tag names the subagent, when several run at once."""
        if name == "write_todos" and args.get("todos"):
            return self.todos(args["todos"])
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
        title = Text(f"subagent {tag}", style=f"italic {MUTED}") if tag is not None else None
```

Parallel loops print at the same time, so their panels interleave on
screen. Each nested panel carries the number of the subagent that
produced it, and the header panel reads `subagent 2 · own context`. The
spinner is off in a parallel loop: the console allows one live display,
and four loops would fight over it.

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
            "anyOf": [{"required": ["description"]}, {"required": ["descriptions"]}],
```

`description` or `descriptions`, at least one. The `anyOf` says so in the
schema the model sees, and `task()` says so again in its error result if
neither arrives.

## Run it

```bash
pip install -e .
harness
> start the test suite in the background, then tell me how the todos module and the memory module are structured
```

The model calls `bash_background` with the test command and gets
`Started job-1: ...` back. The next late injection panel carries a
`<jobs>` block with `job-1: running for 2s`. Then it calls `task` with two
descriptions. Two `subagent 1 · own context` and `subagent 2 · own
context` panels appear, followed by nested tool panels titled `subagent
1` and `subagent 2`, interleaved. The `task` panel shows one result with
two `##` sections. When the model calls `job_status` or `job_wait`, the
result reads `job-1: exited with code 0` with the last twenty lines of
pytest output, and the `<jobs>` block is gone from the next panel.

Type `/jobs` to list every job of the session with its state. Exit with
ctrl-d while a job is running: the process is killed on the way out.

Run the offline tests from the repository root:

```bash
python run_tests.py 29
python check_snippets.py 29
```

## What to notice

- A job is `Popen` where `bash` is `run`. Same wrapper, same rules, same
  shell. The only new decision is where the output goes, and a file wins
  over a pipe because nobody has to drain it.
- Kill the group, not the process. The shell that started the command is
  the process the harness holds; the command is its child. A process
  group is what makes one signal reach both.
- The late block remembers what the model started. A job id in a tool
  result from ten turns ago is easy to lose; `<jobs>` puts the running
  ones in front of the model on every call.
- Parallel subagents share nothing but the registry. Each `loop` owns its
  message list, and the registry was made thread-safe for parallel tool
  calls in step 22. Nothing new had to be locked.
- Order by submission, not by completion. The futures are read in the
  order the descriptions came, so the model can match answers to
  questions by position as well as by header.
- A fake model for parallel loops must not count calls. The test picks
  the script by the text of the request and the step by the length of
  the message list, so three threads can call it in any order.

## Diff from step 28

```bash
diff -r ../step_28_plan_mode/harness harness
```

Added: `jobs.py` (`Job`, `start`, `terminate`, `report`,
`bash_background`, `job_status`, `job_wait`, `job_kill`, `running`,
`jobs_prompt`, `kill_all`, `JOB_SCHEMAS`, `JOB_TOOLS`). Changed:
`subagent.py` (`MAX_PARALLEL`, job tools in `WITHHELD`, `loop` takes
`tag`, `explore`, `title`, `guarded`, `parallel`, `task` with
`descriptions`, `TASK_SCHEMA` with `anyOf`), `tools.py` (job tools in
`TOOLS` and `TOOL_SCHEMAS`), `permissions.py` (`bash_background` rated
like `bash`), `context.py` (`jobs_note`, `<jobs>` after `<plan>`),
`agent.py` (`jobs.kill_all()` at session end), `llm.py` (prompt text on
jobs and parallel subagents), `commands.py` (`/jobs`), `ui.py` (`tool`
and `subagent` take `tag`). Everything else is unchanged from step 28.
