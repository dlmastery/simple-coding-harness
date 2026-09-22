# Step 30 - Evaluation harness

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 29 - Background jobs and parallel subagents](../step_29_jobs_parallel_subagents/README.md). Next: [Step 31 - Project instruction files](../../05_recovery/step_31_instruction_files/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** a way to measure the agent instead of watching
it. `harness eval <suite>` runs every task in a suite directory through
the same `turn()` the chat uses, in a fresh copy of the task's workspace,
and scores each run with a checker: a `check.py` script, an `expect.txt`
substring, or a `judge.md` prompt for an LLM judge. The run records
pass or fail, wall time, tokens, cost and the final answer per task, prints
a table, and writes `eval_report.json` next to the tasks. `--repeat N`
runs every task N times and reports a pass rate. Three tasks ship in
`evals/`.

## Why an eval harness, and what breaks without it

Every change to a prompt, a tool description or a permission rule changes
how the agent behaves. Up to now the only way to know was to open the
chat and try things. That does not scale, and it does not repeat: a model
that passes a task once may fail it the next time. Shorten the system
prompt by a paragraph in step 29 and you have no idea whether the agent
still uses `task` for a survey question, or has gone back to twenty
`read_file` calls; you find out a week later, from the token bill.

An eval is a task with a verdict. The task is a prompt and a workspace.
The verdict is a program, a string, or another model. Run every task,
count the passes, and a change to the harness becomes a number that went
up or down. Run every task several times, and the number carries its own
noise level.

The runner reuses the chat loop as it is. It does not build a second
agent for testing, because a second agent would drift from the first.
The cost of that choice is isolation: the harness keeps state at module
level, and some of it was computed from the working directory when the
module was imported. The runner has to put all of it right for each task
and back afterwards. Most of the code in this step is that bookkeeping.

## The code, piece by piece

### 1. A suite is a directory

`harness/evaluate.py`:

```python
CHECKERS = ("check.py", "expect.txt", "judge.md")
...
def load_suite(suite_dir):
    """Every task directory with a task.md and a checker, sorted by name."""
    suite_dir = Path(suite_dir)
    if not suite_dir.is_dir():
        raise FileNotFoundError(f"suite directory not found: {suite_dir}")
    tasks = []
    for task_dir in sorted(p for p in suite_dir.iterdir() if p.is_dir()):
        prompt_file = task_dir / "task.md"
        checker = find_checker(task_dir)
        if not prompt_file.exists() or checker is None:
            ui.note(f"skipped {task_dir.name}: needs task.md and one of {', '.join(CHECKERS)}")
            continue
        tasks.append(Task(task_dir.name, task_dir, prompt_file.read_text(encoding="utf-8").strip(), checker))
    return tasks
```

A suite is a directory of task directories. Each task holds `task.md`,
the prompt, and one checker file. An optional `workspace/` holds the files
the agent starts with. The first checker found in `CHECKERS` order is the
one used. A directory without a prompt or a checker is noted and skipped,
so one broken task does not stop the suite.

### 2. Every task runs in its own workspace

`harness/evaluate.py`:

```python
def run_task(task, run=1, suite_name="suite", keep=False):
    """One run of one task in a fresh temp workspace. Returns a Result."""
    root = Path(tempfile.mkdtemp(prefix=f"eval-{task.name}-"))
    workspace = root / "workspace"
    if (task.path / "workspace").is_dir():
        shutil.copytree(task.path / "workspace", workspace)
    else:
        workspace.mkdir()
    session_id = f"eval-{suite_name}-{task.name}-{run}-{datetime.now():%Y%m%d-%H%M%S-%f}"

    usage = {}
    notes = []
    answer = ""
    started = time.perf_counter()
    with isolated(workspace, root / "sessions", session_id, usage, notes) as cwd:
        messages = [{"role": "system", "content": system_prompt_for(cwd)}]
        try:
            messages = agent.turn(messages, task.prompt)
            answer = agent.last_reply(messages)
            trouble = [note for note in notes if note.startswith(TROUBLE)]
            if trouble:  # the loop kept the transcript valid, but the turn did not finish
                raise RuntimeError(trouble[0])
            passed, detail = check(task, cwd, answer)  # a judge that cannot be reached fails the run too
        except Exception as failed:  # noqa: BLE001 - one broken run must not end the suite
            passed, detail = False, f"run failed: {type(failed).__name__}: {failed}"
        seconds = time.perf_counter() - started
```

The workspace is copied into a new temp directory for every run, so the
task's own files are never touched and two runs of the same task never
see each other. The message list is new, with a system prompt built for
that directory. `agent.turn` is the same function the chat calls. One
prompt, every model call and tool call it leads to, and the last
assistant text is the answer. A crash inside the turn becomes a failed
result with the exception as its detail. The temp directory is removed
afterwards unless `--keep` is given.

The turn has a budget, the same one the chat has: `agent.MAX_CALLS` (40)
model calls, after which the loop stops with a note. The chat also turns
a dead model call into a note rather than an exception. Both notes are
caught here: `isolated` collects every note the loop prints, and a note
that starts with one of `TROUBLE` (`model call failed`, `stopped after`)
fails the run as `run failed: RuntimeError: ...`, even if the checker
would have passed whatever the agent left behind. A run that did not
finish is not a pass. A judge whose model call fails is caught by the
same `except` and fails the run, not the suite.

### 3. The cost of module-level state

`harness/evaluate.py`:

```python
@contextmanager
def isolated(workspace, session_dir, session_id, usage, notes=None):
    """Run one task as if the harness had started in `workspace`.
    ...
    """
    saved = {
        "cwd": os.getcwd(),
        "session": (session.SESSION_DIR, session.CURRENT, session.WRITTEN),
        "permissions": permissions.PROJECT,
        "sandbox": sandbox.PROJECT,
        "hooks": (hooks.CONFIG_PATHS, list(hooks.SESSION_CONTEXT)),
        "memory": memory.MEMORY_DIRS,
        "skills": (skills.SKILL_DIRS, skills.SKILLS),
        "status": context.LAST_STATUS,
        "todos": list(todos.TODOS),
        "plan": (plan.MODE, plan.PLAN, list(plan.FEEDBACK)),
        "approve": ui.approve,
        "usage": ui.usage,
        "note": ui.note,
    }
    workspace = Path(workspace).resolve()
    os.chdir(workspace)
    session.SESSION_DIR, session.CURRENT, session.WRITTEN = Path(session_dir), session_id, 0
    permissions.PROJECT = workspace
    sandbox.PROJECT = workspace
    hooks.CONFIG_PATHS = [hooks.CONFIG_PATHS[0], workspace / ".agents" / "hooks.json"]
    hooks.SESSION_CONTEXT.clear()
    memory.MEMORY_DIRS = [Path(session_dir).parent / "memory" / "project", Path(session_dir).parent / "memory" / "_user"]
    skills.SKILL_DIRS = [workspace / ".agents" / "skills"]
    skills.SKILLS = skills.find_skills()
    context.LAST_STATUS = context.git_status()
    todos.TODOS.clear()
    plan.set_mode("plan")  # forgets the old plan and its feedback...
    plan.set_mode("act")   # ...and the task runs with every tool
    jobs.kill_all()
    ui.approve = lambda reason: True
```

This is the price of running the real loop in-process. Several modules
computed a value from the working directory when they were imported:
`permissions.PROJECT` decides which writes are inside the project,
`sandbox.PROJECT` is the root the macOS profile is formatted with on each
call, `hooks.CONFIG_PATHS` names the project's hook file,
`session.SESSION_DIR` is where the transcript goes, `memory.MEMORY_DIRS`
is where `remember` writes and the `<memory>` index reads,
`skills.SKILL_DIRS` is where `SKILL.md` files are found, and
`context.LAST_STATUS` is the git baseline that the change notes diff
against. Other modules accumulate state during a chat: the todo list, the
plan and its mode, the session context from hooks, the background jobs.
None of that may leak from one task to the next, or from the suite into
the chat that comes after it, and none of the user's own state may leak
into a run: an eval that could read your real memories, or write into
them, would be neither hermetic nor safe.

So the runner saves every one of those values, sets each to what a fresh
start in the workspace would have produced, and restores them all in the
`finally`. Nothing is monkeypatched: the module attributes are assigned
directly, which is what a fresh import would have done. `ui.approve` is
replaced by a function that answers yes, so an `ask` verdict never waits
for a keyboard. The permission rules' `deny` verdicts stay in force, and
the eval reports what the agent did about them.

What a run isolates, and what it does not:

| state                          | per run                                            |
|--------------------------------|----------------------------------------------------|
| working directory              | the temp workspace                                 |
| session file                   | fresh, under the run's temp `sessions/`            |
| `permissions.PROJECT`, sandbox | the workspace                                      |
| project `hooks.json`           | the workspace's, if any                            |
| home `hooks.json`              | **still applies** (`CONFIG_PATHS[0]` is kept)      |
| git baseline                   | taken in the workspace                             |
| memory store                   | empty, under the run's temp dir                    |
| skills                         | the workspace's `.agents/skills`, if any           |
| todos, plan, mode              | cleared; act mode                                  |
| background jobs                | killed before and after                            |
| `ask` verdicts                 | auto-approved; `deny` still denies                 |
| MCP servers                    | **not started** (`connect_all` runs only in `chat`)|
| `SessionStart` hooks           | **not run**; `SessionEnd` runs once, at exit       |
| `MCP_ALLOW`, `BROWSER_ALLOW`   | as in the environment                              |

`harness/evaluate.py`:

```python
    def record(stats):
        with lock:
            for key, value in (stats or {}).items():
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
        saved["usage"](stats)
```

Token counts are collected the same way. The loop reports every usage
dict to `ui.usage`, including the subagents' calls, from their threads.
For the length of a task that method sums every numeric field into the
`usage` dict under a lock and then hands the dict to the real method.
Prompt, completion and cached tokens come from there, and so does `cost`
when the provider sends one: `llm.usage_from` reads `usage.cost` from the
response, and the request asks OpenRouter for it (`EXTRA_BODY`). Any
other provider leaves `cost` as `null`, and the table shows `-`.

### 4. The prompt names the workspace

`harness/llm.py`:

```python
def build_system_prompt(cwd=None):
    """The system prompt for one working directory. Default: where the harness started."""
    cwd = cwd or os.getcwd()
    return f"""
...
Your current working directory is: {cwd}
...
"""


SYSTEM_PROMPT = build_system_prompt()
```

The system prompt tells the model its working directory. Up to now the
string was built once, at import, with the directory the harness started
in. An eval task runs somewhere else, so the prompt is now a function of
the directory and `SYSTEM_PROMPT` is the value for the default one. The
subagent prompt got the same treatment in `subagent.py`, and `explore`
calls it per request, so a subagent started inside a task searches the
task's workspace and not the directory the eval was launched from.

### 5. Three kinds of verdict

`harness/evaluate.py`:

```python
def run_check_py(task, workspace):
    """Run the task's check.py with the workspace as cwd. Exit 0 is a pass."""
    try:
        completed = subprocess.run(
            [sys.executable, str(task.path / "check.py")],
            cwd=workspace, capture_output=True, text=True, timeout=CHECK_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, f"check.py took more than {CHECK_TIMEOUT}s"
    output = (completed.stdout + completed.stderr).strip()
    tail = "\n".join(output.splitlines()[-10:])
    return completed.returncode == 0, f"check.py exited {completed.returncode}" + (f"\n{tail}" if tail else "")


def run_expect(task, answer):
    """Pass when the expected text appears in the final answer."""
    expected = (task.path / "expect.txt").read_text(encoding="utf-8").strip()
    found = expected in answer
    return found, f"expected {expected!r} {'found' if found else 'missing'} in the answer"


def run_judge(task, workspace, answer):
    """Ask the model to grade the run. The first word of its reply decides."""
    instructions = (task.path / "judge.md").read_text(encoding="utf-8").strip()
    request = (
        f"<instructions>\n{instructions}\n</instructions>\n\n"
        f"<task>\n{task.prompt}\n</task>\n\n"
        f"<answer>\n{answer or '(no answer)'}\n</answer>\n\n"
        f"<workspace>\n{file_list(workspace)}\n</workspace>"
    )
    message, _ = llm.call_llm([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": request}], tools=[])
    verdict = (message.content or "").strip()
    first = verdict.split(None, 1)[0].strip(".:,").upper() if verdict else ""
    return first == "PASS", f"judge said: {verdict[:200] or '(nothing)'}"
```

The contracts, precisely:

- `check.py` is read from the *task* directory, not the workspace, so the
  agent cannot edit it. It runs under the harness's own interpreter with
  the workspace as its working directory, so it can open the files the
  agent wrote and run whatever it likes on them. Exit code zero is a
  pass; it has `CHECK_TIMEOUT` (300s); the last ten lines of its stdout
  and stderr become the detail.
- `expect.txt` is stripped and must appear, case-sensitively, in the
  *last assistant message that has text* (`agent.last_reply`). If the
  model's final message is empty, an earlier remark of the same turn is
  what gets graded. It suits tasks whose result is a fact rather than a
  file, and it is loose: `find_function` passes on any answer that names
  the right file, including one that gets the line wrong.
- `judge.md` hands the verdict to a model. The judge gets the grading
  instructions, the task, the agent's answer and the list of files left
  in the workspace (minus `__pycache__` and `.pytest_cache`, which the
  agent's own test runs leave behind), and must start its reply with
  `PASS` or `FAIL`. It is called with no tools, so it can only read what
  it was given. A judge is the right checker for open-ended tasks and the
  wrong one for anything a script can test: it costs a model call per
  run and it can be wrong.

### 6. The report

`harness/evaluate.py`:

```python
def summarise(name, results):
    """Totals over a list of results, for one task or the whole suite."""
    passed = sum(1 for r in results if r.passed)
    costs = [r.cost for r in results if r.cost is not None]
    return {
        "name": name,
        "runs": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 3) if results else 0.0,
        "seconds": round(sum(r.seconds for r in results), 3),
        "prompt_tokens": sum(r.prompt_tokens for r in results),
        "completion_tokens": sum(r.completion_tokens for r in results),
        "cached_tokens": sum(r.cached_tokens for r in results),
        "cost": round(sum(costs), 6) if costs else None,
    }
```

```python
def run_suite(suite_dir, repeat=1, keep=False):
    """Run every task `repeat` times. Returns the report dict and writes it to the suite dir.

    The report is written whatever ends the loop, so a ctrl-c halfway
    through a long --repeat leaves the runs that finished on disk.
    """
    suite_dir = Path(suite_dir)
    tasks = load_suite(suite_dir)
    started = datetime.now()
    results = []
    try:
        for task in tasks:
            for run in range(1, repeat + 1):
                ui.note(f"eval {task.name} run {run}/{repeat}")
                results.append(run_task(task, run, suite_dir.name, keep))
    finally:
        report = build_report(suite_dir, tasks, results, repeat, started)
        (suite_dir / REPORT_NAME).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
```

`run_suite` runs every task `repeat` times and folds the results twice
with `summarise`: once per task and once for the suite. The report is
one dict: the suite name, the model, the start time, the repeat count, a
list of tasks each with its totals and its individual results, and the
suite totals. It goes to `eval_report.json` in the suite directory
(`evals/.gitignore` keeps it out of the repository), and `ui.eval_table`
draws the same dict as a table. The write is in a `finally`: ctrl-c in
the middle of `--repeat 10` still leaves the finished runs on disk, and
then propagates.

### 7. A subcommand

`harness/agent.py`:

```python
def parser():
    """The command line: chat flags at the top level, `eval` as a subcommand."""
    top = argparse.ArgumentParser(prog="harness")
    top.add_argument("--resume", action="store_true", help="continue the last session")
    top.add_argument("--debug", action="store_true", help="show the raw model response")
    top.add_argument("-p", "--print", metavar="PROMPT", help="run one turn, print the answer, exit")
    commands_ = top.add_subparsers(dest="command", metavar="COMMAND")
    run = commands_.add_parser("eval", help="run an evaluation suite and report pass rates")
    run.add_argument("suite", help="directory of task directories")
    run.add_argument("--repeat", type=int, default=1, metavar="N", help="run every task N times")
    run.add_argument("--keep", action="store_true", help="keep the temp workspaces for inspection")
    return top


def main(argv=None):
    cli = parser().parse_args(argv)
    try:
        if cli.command == "eval":
            raise SystemExit(evaluate.main(cli))
        chat(cli)
```

The chat flags stay where they were, so `harness`, `harness --resume`
and `harness -p PROMPT` work as before. `harness eval SUITE` is a
subcommand with its own flags. `evaluate.main` puts the UI in headless
mode, so the panels of every run go to stderr and stdout carries only the
table and the report path. It returns zero when every run passed and one
otherwise, which makes it usable from a script or a CI job. The `finally`
of `main` still runs after the suite: the browser, the MCP servers (none
were started), the jobs and `SessionEnd`.

## Run it

Prerequisites are those of step 29: Python 3.11+, `API_KEY` (and
`BASE_URL`/`MODEL` if not OpenRouter) in the environment or in
`~/.simple-harness/env`. The shipped `fix_test` task runs `pytest` inside
its workspace, so `pytest` must be importable by the same interpreter.

bash:

```bash
cd harness/04_tools/step_30_eval
pip install -e .
harness eval evals
```

PowerShell:

```powershell
cd harness/04_tools/step_30_eval
pip install -e .
harness eval evals
```

### Expected output

Progress and every run's panels go to stderr; the table and the report
path go to stdout:

```text
  eval find_function run 1/1
  ...
  eval fix_test run 1/1
  ...
  eval write_hello run 1/1
  ...

                       eval evals · anthropic/claude-sonnet-4.5
  ┏━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃ task          ┃ pass ┃   time ┃ prompt ┃ compl ┃ cached ┃   cost ┃ answer                                    ┃
  ┡━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
  │ find_function │  1/1 │  14.2s │ 21,904 │   412 │ 18,432 │ $0.0231 │ `load_settings` is defined in settings.py │
  │ fix_test      │  1/1 │  31.8s │ 38,117 │   903 │ 30,720 │ $0.0412 │ Fixed the off-by-one in `total()`; pytest │
  │ write_hello   │  1/1 │   6.9s │  9,880 │   161 │  8,192 │ $0.0104 │ Wrote hello.txt with five lines.          │
  │ evals         │  3/3 │  52.9s │ 69,901 │ 1,476 │ 57,344 │ $0.0747 │                                           │
  └───────────────┴──────┴────────┴────────┴───────┴────────┴────────┴───────────────────────────────────────────┘

report: evals/eval_report.json
```

`pass` is `passed/runs`, `time` is wall time, then the prompt, completion
and cached token sums, the cost or `-`, and the first line of the last
answer. Open the report to see the full answer and the checker's detail
for every run. Then:

```bash
harness eval evals --repeat 3
```

Each task runs three times and the `pass` column reads `3/3`, `2/3` and
so on. The report's `pass_rate` is that fraction. Add `--keep` to leave
the temp workspaces in place; the report lists their paths. The exit code
is 0 only when every run passed.

The three shipped tasks: `write_hello` asks for a five-line file and
`check.py` counts the lines; `fix_test` starts from a workspace with a
failing pytest and `check.py` runs pytest again; `find_function` asks the
agent to use a subagent to locate a function and `expect.txt` holds the
file name. An LLM judge is not shipped, because the shipped tasks all
have a checkable answer, but a `judge.md` beside a `task.md` is all it
takes.

To add a task, make a directory under `evals/` with a `task.md` and one
checker:

```text
evals/rename_function/
├── task.md          "Rename `total` to `sum_items` everywhere it is used."
├── workspace/       cart.py, test_cart.py - what the agent starts with
└── check.py         import cart; assert hasattr(cart, "sum_items"); run pytest
```

`check.py` runs with `evals/rename_function/workspace`'s copy as its
working directory, so `import cart` finds the file the agent edited.

Run the offline tests from the repository root:

```bash
python run_tests.py 30
python check_snippets.py 30
```

## Error handling

- **A run whose model call fails**, or that hits the 40-call budget, is
  `run failed: RuntimeError: model call failed: ...` (or `... stopped
  after 40 model calls ...`) in the report, `0/1` in the table, and the
  suite goes on to the next run.
- **A run that crashes** for any other reason is `run failed: <Type>:
  <message>`; `isolated` restores every module attribute in its `finally`
  and kills any job the run left, so the next run starts clean.
- **A judge that cannot be reached** fails that run, not the suite.
- **A `check.py` that exits non-zero, or times out after 300s**: the
  detail is `check.py exited N` with its last ten lines, or `check.py
  took more than 300s`.
- **A task directory without `task.md` or a checker** is noted
  (`skipped <name>: needs task.md and one of ...`) and left out. A suite
  directory that does not exist is `FileNotFoundError: suite directory
  not found: ...` and exit 1.
- **ctrl-c during the suite**: the runs that finished are written to
  `eval_report.json`, then the interrupt propagates and the process
  exits without the table.
- **Inside a run** the loop behaves as in the chat: a tool call with
  broken arguments, an unknown tool, a raising tool and a timed-out
  command are all `Error: ...` tool results, and the run continues.
- **`ask` never blocks**: every `ask` is a yes, so a run cannot hang on a
  prompt. A `deny` is `Blocked by policy: ...` to the model.

## Gotchas / What this is not

- **Every `ask` is a yes.** `bash_background python serve.py`,
  `computer_act`, any MCP tool, a write outside the workspace: all run
  without a question. Only `deny`-rated calls are refused. Do not point
  the runner at a suite you have not read, and do not run it with
  `MCP_ALLOW` or `BROWSER_ALLOW` set wider than the suite needs.
- **Your home `hooks.json` still applies** to every run; the project one
  is the workspace's. A `SessionStart` hook does not run for a suite.
- **MCP servers are not started** by `eval`; a task that needs one will
  see `Error: no tool named 'mcp__...'.`.
- **Memory and skills are the workspace's.** A run starts with an empty
  memory store under its temp directory and only the skills in the
  workspace's `.agents/skills`. `remember` inside a run writes to the
  temp store, which is deleted with the workspace.
- **`expect.txt` is a loose grader.** Substring, case-sensitive, on the
  last non-empty assistant text. Anything stricter belongs in a
  `check.py`; the shipped `write_hello/task.md` says "do not create any
  other file" but its `check.py` does not check that.
- **Runs are sequential.** Tasks and repeats run one after another;
  parallel subagents inside a run are the only parallelism.
- **The report lands in the suite directory**, overwriting the last one.
  Copy it aside before a second run you want to compare against.
- **Cost is `null` off OpenRouter.** The `cost` column reads `-` unless
  the provider returns `usage.cost`.
- **macOS:** the seatbelt profile is formatted with `sandbox.PROJECT` on
  every call, so a run's `bash` may write inside its workspace; it may
  not write anywhere else.
- **Windows:** the tool called `bash` runs `cmd.exe`, there is no OS
  sandbox, and a task's shell commands are written for whatever shell
  the grader has; the shipped tasks use `python` and `pytest` only.

## What to notice

- The eval runs the real loop. `agent.turn` is called with a message
  list and a prompt, exactly as the chat calls it. A second loop for
  testing would drift from the first, and then the eval would measure
  the wrong thing.
- Module-level state is the cost. Every global that was computed from the
  working directory, or that fills up during a chat, has to be set and
  restored per task. The list in `isolated` is the honest inventory of
  that state, and each new step that adds a global has to add a line.
  The table above is the same inventory from the reader's side.
- The prompt is a function now. A string built at import carries the
  import-time directory forever. `build_system_prompt(cwd)` makes the
  directory an argument, and the default keeps the chat unchanged.
- A note is a verdict too. The chat loop turns a dead model call and a
  runaway turn into notes so the transcript stays valid; the runner reads
  those notes back and fails the run, because a turn that did not finish
  must not pass on whatever it left behind.
- Permissions stay on, halfway. `ask` is a yes, `deny` is a deny, a hook
  can still block. The eval measures the agent under the rules the user
  would run it with, minus the user.
- A checker is a contract with the task, not with the harness. `check.py`
  gets a working directory and returns an exit code. It can be any
  program, and the harness never reads it.
- The fake model in the tests is stateless. It picks a script by the
  task prompt and a step by the number of assistant messages, so `--repeat`
  and subagent threads need no shared counter.

## Files

```text
step_30_eval/
├── harness/
│   ├── llm.py                        the model call; build_system_prompt(cwd) for any workspace
│   ├── tools.py                      the registry; bash_background, job_status, job_wait, job_kill
│   ├── agent.py                      the loop; main() has subcommands, harness eval <suite>
│   ├── evaluate.py                   the eval harness: runs a suite through turn(), scores each run
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
│   ├── ui.py                         rich panels; eval_table() draws the result of an eval run
│   └── __init__.py                   package marker
├── .agents/
│   ├── hooks.json                    hook config: block .env writes, log every tool name
│   ├── block_env_writes.py           example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: appends every tool name to a log
│   ├── .gitignore                    ignores tool_log.txt, the log hook's output
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── evals/                            one folder per task: task.md, a checker, optional workspace/
│   ├── .gitignore                    ignores eval_report.json
│   ├── find_function/                task.md + expect.txt + workspace/
│   ├── fix_test/                     task.md + check.py + workspace/ with a failing test
│   └── write_hello/                  task.md + check.py
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.30.0
└── README.md                         this file
```

## What the next step adds

Step 31 adds project instruction files: `AGENTS.md` (or `CLAUDE.md`)
from the home directory, the git root and every directory down to the
working directory go into the system prompt, and `/init` writes one from
a subagent's survey of the project.

## Diff from step 29

```bash
diff -r ../step_29_jobs_parallel_subagents/harness harness
```

Added: `evaluate.py` (`Task`, `Result`, `find_checker`, `load_suite`,
`isolated`, `system_prompt_for`, `file_list`, `run_check_py`,
`run_expect`, `run_judge`, `check`, `run_task`, `summarise`,
`build_report`, `run_suite`, `main`) and `evals/` with three tasks.
Changed: `agent.py` (`parser` with the `eval` subcommand, `main(argv)`
dispatches, `chat(cli)` takes the parsed flags), `llm.py`
(`build_system_prompt(cwd)`; `SYSTEM_PROMPT` is its default),
`subagent.py` (`build_system_prompt(cwd)`; `explore` builds the prompt
per call), `ui.py` (`eval_table`). Everything else is unchanged from step
29.
