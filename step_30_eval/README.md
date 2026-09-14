# Step 30 - Evaluation harness

**What this step adds:** a way to measure the agent instead of watching
it. `harness eval <suite>` runs every task in a suite directory through
the same `turn()` the chat uses, in a fresh copy of the task's workspace,
and scores each run with a checker: a `check.py` script, an `expect.txt`
substring, or a `judge.md` prompt for an LLM judge. The run records
pass or fail, wall time, tokens, cost and the final answer per task, prints
a table, and writes `eval_report.json` next to the tasks. `--repeat N`
runs every task N times and reports a pass rate. Three tasks ship in
`evals/`.

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
│   ├── session.py                    append-only JSONL log, load(), /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash
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
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.30.0
└── README.md                         this file
```

## Why an eval harness

Every change to a prompt, a tool description or a permission rule changes
how the agent behaves. Up to now the only way to know was to open the
chat and try things. That does not scale, and it does not repeat: a model
that passes a task once may fail it the next time.

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
    started = time.perf_counter()
    with isolated(workspace, root / "sessions", session_id, usage) as cwd:
        messages = [{"role": "system", "content": system_prompt_for(cwd)}]
        try:
            messages = agent.turn(messages, task.prompt)
            answer, error = agent.last_reply(messages), None
        except Exception as failed:  # noqa: BLE001 - one broken run must not end the suite
            answer, error = "", f"run failed: {type(failed).__name__}: {failed}"
        seconds = time.perf_counter() - started
        passed, detail = (False, error) if error else check(task, cwd, answer)
```

The workspace is copied into a new temp directory for every run, so the
task's own files are never touched and two runs of the same task never
see each other. The message list is new, with a system prompt built for
that directory. `agent.turn` is the same function the chat calls. One
prompt, every model call and tool call it leads to, and the last
assistant text is the answer. A crash inside the turn becomes a failed
result with the exception as its detail. The temp directory is removed
afterwards unless `--keep` is given.

### 3. The cost of module-level state

`harness/evaluate.py`:

```python
@contextmanager
def isolated(workspace, session_dir, session_id, usage):
    """Run one task as if the harness had started in `workspace`.
    ...
    """
    saved = {
        "cwd": os.getcwd(),
        "session": (session.SESSION_DIR, session.CURRENT, session.WRITTEN),
        "permissions": permissions.PROJECT,
        "sandbox": sandbox.PROJECT,
        "hooks": (hooks.CONFIG_PATHS, list(hooks.SESSION_CONTEXT)),
        "status": context.LAST_STATUS,
        "todos": list(todos.TODOS),
        "plan": (plan.MODE, plan.PLAN, list(plan.FEEDBACK)),
        "approve": ui.approve,
        "usage": ui.usage,
    }
    workspace = Path(workspace).resolve()
    os.chdir(workspace)
    session.SESSION_DIR, session.CURRENT, session.WRITTEN = Path(session_dir), session_id, 0
    permissions.PROJECT = workspace
    sandbox.PROJECT = workspace
    hooks.CONFIG_PATHS = [hooks.CONFIG_PATHS[0], workspace / ".agents" / "hooks.json"]
    hooks.SESSION_CONTEXT.clear()
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
`sandbox.PROJECT` is the only path the OS sandbox lets a command write,
`hooks.CONFIG_PATHS` names the project's hook file, `session.SESSION_DIR`
is where the transcript goes, and `context.LAST_STATUS` is the git
baseline that the change notes diff against. Other modules accumulate
state during a chat: the todo list, the plan and its mode, the session
context from hooks, the background jobs. None of that may leak from one
task to the next, or from the suite into the chat that comes after it.

So the runner saves every one of those values, sets each to what a fresh
start in the workspace would have produced, and restores them all in the
`finally`. Nothing is monkeypatched: the module attributes are assigned
directly, which is what a fresh import would have done. `ui.approve` is
replaced by a function that answers yes, so an `ask` verdict never waits
for a keyboard. The permission rules themselves stay in force: a `deny`
is still a deny, and the eval reports what the agent did about it.

`harness/evaluate.py`:

```python
    def record(stats):
        for key, value in (stats or {}).items():
            if isinstance(value, (int, float)):
                usage[key] = usage.get(key, 0) + value
        saved["usage"](stats)

    ui.usage = record
```

Token counts are collected the same way. The loop reports every usage
dict to `ui.usage`, including the subagents' calls. For the length of a
task that method sums every numeric field into the `usage` dict and then
hands the dict to the real method. Prompt, completion and cached tokens
come from there, and so does `cost` when the provider sends one. A run
whose usage never carried a cost reports `null`.

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

`check.py` lives in the task directory and runs with the workspace as its
working directory, so it can open the files the agent wrote and run
whatever it likes on them. Exit code zero is a pass; the last ten lines
of its output become the detail. `expect.txt` is the simplest checker:
the text must appear in the final answer. It suits tasks whose result is
a fact rather than a file.

`judge.md` hands the verdict to a model. The judge gets the grading
instructions, the task, the agent's answer and the list of files left in
the workspace, and must start its reply with `PASS` or `FAIL`. It is
called with no tools, so it can only read what it was given. A judge is
the right checker for open-ended tasks and the wrong one for anything a
script can test: it costs a model call per run and it can be wrong.

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

`run_suite` runs every task `repeat` times and folds the results twice
with this function: once per task and once for the suite. The report is
one dict: the suite name, the model, the start time, the repeat count, a
list of tasks each with its totals and its individual results, and the
suite totals. It goes to `eval_report.json` in the suite directory, and
`ui.eval_table` draws the same dict as a table.

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
otherwise, which makes it usable from a script or a CI job.

## Run it

```bash
pip install -e .
harness eval evals
```

Three lines of progress go to stderr, one per task, followed by the panels
of each run. Then stdout shows a table with one row per task and a totals
row: `pass` as `passed/runs`, the wall time, the prompt, completion and
cached token sums, the cost or `-`, and the first line of the last answer.
The last line names the report:

```text
report: evals/eval_report.json
```

Open it to see the full answer and the checker's detail for every run.
Then:

```bash
harness eval evals --repeat 3
```

Each task runs three times and the `pass` column reads `3/3`, `2/3` and
so on. The report's `pass_rate` is that fraction. Add `--keep` to leave
the temp workspaces in place; the report lists their paths.

The three shipped tasks: `write_hello` asks for a five-line file and
`check.py` counts the lines; `fix_test` starts from a workspace with a
failing pytest and `check.py` runs pytest again; `find_function` asks the
agent to use a subagent to locate a function and `expect.txt` holds the
file name. An LLM judge is not shipped, because the shipped tasks all
have a checkable answer, but a `judge.md` beside a `task.md` is all it
takes.

Run the offline tests from the repository root:

```bash
python run_tests.py 30
python check_snippets.py 30
```

## What to notice

- The eval runs the real loop. `agent.turn` is called with a message
  list and a prompt, exactly as the chat calls it. A second loop for
  testing would drift from the first, and then the eval would measure
  the wrong thing.
- Module-level state is the cost. Every global that was computed from the
  working directory, or that fills up during a chat, has to be set and
  restored per task. The list in `isolated` is the honest inventory of
  that state, and each new step that adds a global has to add a line.
- The prompt is a function now. A string built at import carries the
  import-time directory forever. `build_system_prompt(cwd)` makes the
  directory an argument, and the default keeps the chat unchanged.
- Permissions stay on. Only `ui.approve` is replaced, so an `ask` is a
  yes, but a `deny` is still a deny and a hook can still block. The eval
  measures the agent under the rules the user would run it with.
- A checker is a contract with the task, not with the harness. `check.py`
  gets a working directory and returns an exit code. It can be any
  program, and the harness never reads it.
- The fake model in the tests is stateless. It picks a script by the
  task prompt and a step by the number of assistant messages, so `--repeat`
  and subagent threads need no shared counter.

## Diff from step 29

```bash
diff -r ../step_29_jobs_parallel_subagents/harness harness
```

Added: `evaluate.py` (`Task`, `Result`, `find_checker`, `load_suite`,
`isolated`, `system_prompt_for`, `file_list`, `run_check_py`,
`run_expect`, `run_judge`, `check`, `run_task`, `summarise`, `run_suite`,
`main`) and `evals/` with three tasks. Changed: `agent.py` (`parser`
with the `eval` subcommand, `main(argv)` dispatches, `chat(cli)` takes
the parsed flags), `llm.py` (`build_system_prompt(cwd)`; `SYSTEM_PROMPT`
is its default), `subagent.py` (`build_system_prompt(cwd)`; `explore`
builds the prompt per call), `ui.py` (`eval_table`). Everything else is
unchanged from step 29.
