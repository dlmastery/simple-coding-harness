# Step 38 - Capstone

**What this step adds:** one end-to-end task for the whole harness. The
brief in `capstone/task.md` asks for a FastAPI todo API with a SQLite
store, tests and a README, built in an empty directory. `capstone/run.py`
runs the harness on it headless, in-process, in a fresh temp workspace,
then grades the result with a step 30 suite of five checks in
`capstone/evals/`: the server starts, the CRUD endpoints work, the
project's own tests pass, a README with a run section exists, and no
file outside the workspace changed. The runner writes `report.json`, a
markdown scorecard and a readable transcript. A hand-written reference
solution in `capstone/reference/` proves the checks are passable. Two
harness changes came out of running it for real: `harness eval` can grade
one workspace instead of running the agent per task, and a tool that
raises now returns an `Error:` result instead of ending the loop.

## Files

```text
step_38_capstone/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; `harness eval --workspace DIR` grades one workspace
│   ├── agents.py         agent definitions: subagents described in Markdown files; a bad file is a note
│   ├── ask_user.py       the ask_user tool: a question to the user, answer as result
│   ├── browse.py         the browse tool set over the step 23 browser subagent
│   ├── browser.py        browser tools: one Chromium page driven through Playwright
│   ├── budget.py         the context budget: where the window goes, when to warn
│   ├── checkpoint.py     workspace checkpoints: file copies taken before each approved edit
│   ├── commands.py       slash commands: /pipeline joins /undo, /rewind, /checkpoints
│   ├── compact.py        the compaction agent; its note is kept
│   ├── computer.py       computer use: the screen as a tool
│   ├── config.py         settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py        the late injection block: <env>, <plan>, <jobs>
│   ├── durability.py     the loop detector, parse_args and the crash-recovery scan
│   ├── evaluate.py       the evaluation harness; run_suite(workspace=DIR) grades a copy
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events from hooks.json; PostToolUse carries `ok`
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs: commands that run while the chat goes on
│   ├── llm.py            the model call with retries; the prompt lists the agent definitions
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── permissions.py    which calls need a human; session rules from `a` and `never`
│   ├── pipeline.py       the plan, work, review pipeline behind /pipeline; verdict_of, missing_agents
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line; prompts go to stderr without a terminal
│   ├── sandbox.py        an OS sandbox for bash; the profile is written per call, the temp dir is writable
│   ├── session.py        append-only JSONL session log, load() and --resume
│   ├── skills.py         skills, unchanged since stage 9
│   ├── subagent.py       the subagent loop; TASK_SCHEMA has no top-level anyOf
│   ├── todos.py          the plan behind write_todos, validated before it replaces the list
│   ├── tools.py          the tool registry; run() turns a raised exception or an unknown name into Error:
│   └── ui.py             rich panels; pipeline() draws the summary table
├── .agents/
│   ├── .gitignore                     ignores tool_log.txt, the PostToolUse hook's log
│   ├── hooks.json                     hook config: one PreToolUse and one PostToolUse hook
│   ├── block_env_writes.py            example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py                example PostToolUse hook: appends every tool name to a log
│   ├── mcp.json                       MCP config: one stdio server, echo
│   ├── mcp_echo_server.py             a tiny MCP server: two tools, stdio transport
│   ├── skills/explain-code/SKILL.md   the stage 4 skill
│   ├── agents/planner.md              definition: reads the code, returns a numbered plan
│   ├── agents/worker.md               definition: carries out one plan step with the edit tools
│   └── agents/reviewer.md             definition: checks one step, answers PASS or FAIL
├── evals/           three step 30 tasks: task.md, check.py or expect.txt, workspace/
├── capstone/        the end-to-end task
│   ├── task.md         the brief: a FastAPI todo API with SQLite, tests and a README
│   ├── run.py          the runner: one headless harness run, then the eval suite
│   ├── evals/          five checks, one folder each: task.md, check.py; _common.py helpers (load_app, client)
│   ├── reference/      hand-written solution that proves the checks are passable
│   │   ├── app.py        the todo API: FastAPI on top of a SQLite file
│   │   ├── test_app.py   its tests; every test gets an empty database
│   │   └── README.md     its README, with the run section check 4 looks for
│   ├── report.json     the recorded run: calls, tokens, cost and the check results
│   ├── SCORECARD.md    the recorded run as a markdown scorecard, 4/5
│   └── transcript.md   the recorded run's messages, readable
├── AGENTS.md        project instructions the harness reads into its prompt
├── test_step.py     offline tests: a scripted fake writes the reference solution; the checks on their own
├── pyproject.toml   package metadata; version 0.38.0
└── README.md        this file
```

## Why a capstone

Every step so far tested one mechanism in isolation, with a fake model.
The loop, the tools, the permissions, the context management, the
subagents, the hooks and the evaluation harness have each been shown to
work. None of them has been shown to work together, on a task of the size
the harness was built for, with a real model on the other end.

A capstone is that test. It is deliberately small - one module, one test
file, one README - so a run costs cents and finishes in a minute, but it
is a real program with a database, a web framework and a test suite, and
the model has to get every one of them right. The grading is strict and
mechanical: five programs, each with an exit code, none of them a judge.

The second reason is measurement. The scorecard puts a number on the
whole harness, not one part: how many model calls, how many tool calls,
how many tokens, how much money, how many checks. Change the system
prompt, the tool set or the model and the number moves. Step 30 built the
instrument; this step points it at the harness itself.

The third reason is the surprises. Two live runs ended on harness bugs
that no offline test had caught. The section on the recorded run below
tells what happened and what changed because of it.

## The code, piece by piece

### 1. Grading a workspace

A step 30 task runs the agent, then its checker. The capstone needs the
five checkers to look at one workspace that a single run produced, so
`run_task` and `run_suite` take a `workspace` argument.

`harness/evaluate.py`:

```python
def run_task(task, run=1, suite_name="suite", keep=False, workspace=None):
    ...
    root = Path(tempfile.mkdtemp(prefix=f"eval-{task.name}-"))
    start = Path(workspace) if workspace else task.path / "workspace"
    if start.is_dir():
        shutil.copytree(start, root / "workspace")
    else:
        (root / "workspace").mkdir()
    workspace, grading = root / "workspace", workspace is not None
    ...
    with isolated(workspace, root / "sessions", session_id, usage, notes) as cwd:
        messages = [{"role": "system", "content": system_prompt_for(cwd)}]
        try:
            if not grading:
                messages = agent.turn(messages, task.prompt)
            answer = agent.last_reply(messages)
```

Every task still gets its own fresh copy, so a check that leaves files
behind, such as pytest with its caches, cannot affect the next one. The
model turn is skipped, and the `task.md` of each task describes what the
check looks for rather than prompting an agent. The `harness eval`
subcommand exposes the same thing as `--workspace DIR`. A `DIR` that does
not exist is a `FileNotFoundError` before anything runs, not an empty
copy graded 0 of 5 with no hint why. `harness/evaluate.py`:

```python
    if workspace is not None and not Path(workspace).is_dir():
        raise FileNotFoundError(f"workspace directory not found: {workspace}")  # grading an empty copy would fail every check for the wrong reason
```

Grading suits `check.py` tasks only. A task graded by `expect.txt`
compares an answer that is empty in this mode, so it always fails, and a
`judge.md` task spends a model call judging that empty answer. The
capstone's five tasks are all `check.py`.

### 2. The checks

Each check is a `check.py` with the workspace as cwd, as in step 30. The
first two import the app rather than starting a server, so no port is
bound and nothing is left running.

`capstone/evals/_common.py`:

```python
def load_app():
    """Import `app` from the workspace's app.py. Raises when it is missing or broken."""
    workspace = Path.cwd()
    if not (workspace / "app.py").exists():
        raise FileNotFoundError("app.py is missing")
    os.environ["TODO_DB"] = str(Path(tempfile.mkdtemp(prefix="capstone-db-")) / "check.db")
    sys.path.insert(0, str(workspace))
    module = importlib.import_module("app")
    if not hasattr(module, "app"):
        raise AttributeError("app.py has no module-level variable named app")
    return module.app
```

The brief pins two things the checks rely on: the module is `app.py`
with a variable named `app`, and the database path is read from
`TODO_DB` when a connection opens. The CRUD check then walks the whole
interface through a `TestClient`, whose `with` block runs the app's
startup code.

`capstone/evals/2_crud/check.py`:

```python
with client(app) as http:
    expect(http.get("/todos").json() == [], "GET /todos on an empty database must return []")

    created = http.post("/todos", json={"title": "write the checks"})
    expect(created.status_code == 201, f"POST /todos returned {created.status_code}, expected 201")
    ...
    deleted = http.delete(f"/todos/{first_id}")
    expect(deleted.status_code == 204, f"DELETE /todos/id returned {deleted.status_code}, expected 204")
    expect(deleted.content == b"", "DELETE must return an empty body")
```

Every `expect` names the rule it checks, so a failure reads as a sentence
in the scorecard. What makes each check fail:

1. `1_server_starts`: no `app.py`, an `app.py` that does not import, no
   module-level `app`, an app whose startup raises, or `GET /health` that
   is not `200` with the body `{"status": "ok"}` exactly.
2. `2_crud`: any step of the walk: `GET /todos` on an empty database must
   be `[]`; `POST` returns `201` and a body with exactly the keys `id`,
   `title`, `done`; a `POST` without a title is `422`; `GET /todos` lists
   in creation order; `PUT` updates the fields given and keeps the rest;
   `DELETE` is `204` with an empty body; a missing id is `404` on `GET`,
   `PUT` and `DELETE`.
3. `3_tests_pass`: no `test_*.py` or `*_test.py` in the workspace, or
   `python -m pytest -q -p no:cacheprovider` in a copy of the workspace
   exits non-zero - exit code 5 included, because a suite that collects
   nothing is not a passing suite - or runs over 240 s. It passes on
   `1 passed`: the brief asks for a test per endpoint, and this check
   does not count them.
4. `4_readme`: no `README.md`, one under 80 characters, no heading whose
   text contains "run", or no such section that names `uvicorn`. Any run
   section will do, so `## Run the tests` before `## Run the server` is
   fine. `capstone/evals/4_readme/check.py`:

```python
for start, title in run_headings:  # any run section will do: "Run the tests" may come before "Run the server"
    following = [pos for pos, _ in headings if pos > start]
    section = text[start:following[0] if following else len(text)]
    if "uvicorn" in section:
        ok(f"README.md has a {title!r} section with the uvicorn command")
fail(f"no run section names the uvicorn command; run headings are {[title for _, title in run_headings]}")
```

5. `5_no_outside_changes`: a file added, removed or changed in the parent
   of the workspace, or no `CAPSTONE_MANIFEST` in the environment.

The first three checks run under `sys.executable`, the interpreter that
runs `run.py` or `harness eval`. A check that cannot import `fastapi` or
`httpx` says so in one line instead of a traceback. `capstone/evals/_common.py`:

```python
    try:
        from fastapi.testclient import TestClient
    except ImportError as missing:  # the check's own interpreter lacks the [capstone] extra: say so, not a traceback
        fail(f"the check needs fastapi and httpx in {sys.executable}: {missing}")
```

### 3. Nothing changed outside

The last check cannot see the original workspace: it runs in a copy. So
the runner takes a manifest of the workspace's parent directory before
and after the run, and the check compares the two.

`capstone/run.py`:

```python
def manifest(root, skip):
    """Relative path -> sha256 of every file under root, except those under skip."""
    root, skip = Path(root), Path(skip)
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != skip and skip not in path.parents:
            found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found
```

The parent holds two planted files next to the workspace, so the
manifest has something to guard. The runner writes both manifests to one
JSON file and passes its path in the `CAPSTONE_MANIFEST` environment
variable, which the check's subprocess inherits.

`capstone/evals/5_no_outside_changes/check.py`:

```python
added = sorted(set(after) - set(before))
removed = sorted(set(before) - set(after))
changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
if added or removed or changed:
    for label, paths in (("added", added), ("removed", removed), ("changed", changed)):
        for p in paths:
            print(f"  {label}: {p}")
    fail(f"{len(added)} added, {len(removed)} removed, {len(changed)} changed outside the workspace")
```

Without the variable the check fails. A check that cannot compare must
not pass by default; silence is not evidence.

The check's reach is the parent directory and its two planted files, no
more. A write to the home directory - the `remember` tool's
`~/.simple-harness/memory/`, the checkpoints - or to the system temp
directory is invisible to it. And the harness's own guard is off during
the run: `evaluate.isolated` answers every approve prompt with `y`, a
write outside the workspace included, so check 5 grades the model's
obedience to the brief, not the permission layer. The test
`test_a_write_outside_the_workspace_fails_the_last_check` shows exactly
that: the outside write is approved, and the check catches it.

### 4. The headless run

The runner reuses the step 30 isolation instead of a subprocess, so the
run has the same permissions, hooks and session handling as `harness
eval`, and the usage of every model call is summed into one dict.

`capstone/run.py`:

```python
def why_continue(messages):
    ...
    last = messages[-1]
    if last["role"] == "tool":
        return "the turn stopped at MAX_CALLS"
    if last["role"] == "user":
        return "the model call failed"
    if last["role"] == "assistant" and (last.get("content") or "").rstrip().endswith("?"):
        return "the answer ended with a question"
    return None
```

```python
        with evaluate.isolated(workspace, state / "sessions", session_id, usage) as cwd:
            messages = [{"role": "system", "content": evaluate.system_prompt_for(cwd)}]
            user_input = prompt
            try:
                for turn in range(1, max_turns + 1):
                    messages = agent.turn(messages, user_input)
                    reason = why_continue(messages)
                    if reason is None or turn == max_turns:
                        break
                    user_input = NOBODY if "question" in reason else CONTINUE
                    continuations.append({"turn": turn + 1, "reason": reason, "message": user_input})
            except Exception as failed:  # noqa: BLE001 - a crashed run still gets a report
                notes.append(f"run failed: {type(failed).__name__}: {failed}")
```

A turn can end three ways short of an answer. It stops at `MAX_CALLS`
and the transcript ends in a tool result - or the model call failed for
good right after the tool results, which leaves the same shape and the
same label. The model call fails for good before any tool call and the
transcript ends in the user message. Or the model answers with a
question, which in a chat would wait for the user and here waits for
nobody; any answer whose last character is `?` counts, "Anything else?"
included. The runner sends a follow-up for each, at most twice, and
records why. The second live run below is the reason the question case
exists.

`run()` takes the two temp directories away in a `finally`, so a Ctrl-C
at the steer prompt or a crash in the suite leaves nothing behind unless
`--keep` asked for it.

### 5. The report

`capstone/run.py`:

```python
    manifest_file = state / "manifest.json"
    manifest_file.write_text(json.dumps({"before": before, "after": after}, indent=2), encoding="utf-8")
    previous = os.environ.get("CAPSTONE_MANIFEST")
    os.environ["CAPSTONE_MANIFEST"] = str(manifest_file)
    try:
        evals_report = evaluate.run_suite(evals, workspace=workspace, keep=keep)
    finally:
        if previous is None:
            os.environ.pop("CAPSTONE_MANIFEST", None)
        else:
            os.environ["CAPSTONE_MANIFEST"] = previous
```

The report holds the run's numbers, the summed usage, a cost, the notes
the loop printed, the follow-ups sent, a step list built from the
transcript with one line per tool call, the eval report from step 30,
and the score. The cost comes from the usage dict when the provider
reports one - `llm.usage_from` reads a `cost` field, and OpenRouter sends
one when the request asks with `usage.include` - else from `PRICES`, a
table of three OpenAI models, else it is `unknown`; `cost_note` says
which. The recorded run went through the OpenAI API, so its cost is an
estimate. The scorecard is the same data as markdown. The transcript
file keeps every message with tool results cut to forty lines.

The step list's `error` flag is true for a result that starts with an
`ERROR_MARKS` prefix (`Error`, `Timed out`, `Blocked by`, the denied,
interrupted and repeated-call messages) or that matches `PROBLEM_RE`,
which recognises a traceback, a pytest failure line or a shell's
"command not found". The last line of a result is taken before any
`[output capped:` or `[output trimmed:` notice, so a long pytest output
reports its own last line, not the notice.

### 6. A tool that raises

The third live run ended in a `FileNotFoundError` from a subagent's
`read_file` call. At the time nothing between the tool function and the
loop caught it, so in a chat the harness would have exited, with the
transcript saved for `--resume` and step 34's `recover`. Headless there
is no resume, so the run was over. The guard the capstone asked for is
`call`, which every step since the review carries:

`harness/tools.py`:

```python
def call(tool_call, args):
    """Call the tool itself. Never raises: a broken tool is a result, not a crash."""
    name = tool_call.function.name
    if name not in TOOLS:  # decide() refuses these first; call() alone must not raise either
        return f"Error: no tool named {name!r}."
    try:
        return as_text(TOOLS[name](**args))  # name -> function, JSON -> kwargs
    except Exception as e:  # wrong arguments, missing file, anything the tool raises
        return f"Error: {type(e).__name__}: {e}"
```

The result reaches the model as text, the same way a failed command or a
denied call does, and the model reads it and tries something else. The
guard sits in `call`, under `run`, so it covers the main loop, the
explorer subagent and the step 36 definitions alike. A name that is not
in the registry takes the same road, and so do arguments that are not a
JSON object, which `decide` answers before anything runs. The fix was
found here first and then carried back through the earlier steps, so
every step's `call` now reads like this.

## Run it

Prerequisites: Python 3.10+ and the `[capstone]` extra (fastapi, httpx,
uvicorn, pytest) installed in the interpreter that is `python` on the
agent's PATH. The checks run under the interpreter that runs `run.py`,
but the model's `python -m pytest` runs whatever `python` the shell
finds - `cmd.exe` on Windows, `/bin/sh` elsewhere - so a virtualenv that
holds the extra but is not activated makes the model's tests fail on
`ModuleNotFoundError: fastapi` while the checks pass, or the reverse.
Activate it, or install the extra where `python` points.

```bash
cd step_38_capstone
pip install -e ".[capstone]"
cd ..
python run_tests.py 38
python check_snippets.py 38
```

```powershell
cd step_38_capstone
pip install -e ".[capstone]"
cd ..
python run_tests.py 38
python check_snippets.py 38
```

Grade the reference solution without a model, from `step_38_capstone`:

```bash
harness eval capstone/evals --workspace capstone/reference
```

```powershell
harness eval capstone/evals --workspace capstone/reference
```

Run the capstone for real. It needs a model that follows a long system
prompt and calls tools well; a small chat model will not do. `API_KEY`,
`BASE_URL` and `MODEL` come from the environment or from
`~/.simple-harness/env`:

```bash
cd step_38_capstone
BASE_URL=https://api.openai.com/v1 API_KEY=... MODEL=gpt-4.1-mini python capstone/run.py
```

```powershell
cd step_38_capstone
$env:BASE_URL = "https://api.openai.com/v1"; $env:API_KEY = "..."; $env:MODEL = "gpt-4.1-mini"
python capstone/run.py
```

`run.py` imports `truststore`, when it is installed, so a machine behind
a TLS interceptor uses the OS trust store; `harness eval` does not.

### Expected output

Grading the reference prints one `eval <task> run 1/1` note per task on
stderr, then the step 30 table on stdout:

```text
                     eval evals · gpt-4.1-mini
  ┌──────────────────────┬──────┬───────┬────────┬───────┬────────┬──────┬────────┐
  │ task                 │ pass │  time │ prompt │ compl │ cached │ cost │ answer │
  ├──────────────────────┼──────┼───────┼────────┼───────┼────────┼──────┼────────┤
  │ 1_server_starts      │  1/1 │  1.1s │      0 │     0 │      0 │    - │        │
  │ 2_crud               │  1/1 │  1.2s │      0 │     0 │      0 │    - │        │
  │ 3_tests_pass         │  1/1 │  2.9s │      0 │     0 │      0 │    - │        │
  │ 4_readme             │  1/1 │  0.1s │      0 │     0 │      0 │    - │        │
  │ 5_no_outside_changes │  0/1 │  0.1s │      0 │     0 │      0 │    - │        │
  │ evals                │  4/5 │  5.4s │      0 │     0 │      0 │    - │        │
  └──────────────────────┴──────┴───────┴────────┴───────┴────────┴──────┴────────┘
report: capstone/evals/eval_report.json
```

Four pass and the fifth fails with `CAPSTONE_MANIFEST is not set`,
because nothing ran that could have made a manifest; `run.py` is what
sets it. The tokens are zero and the cost `-` because no model ran, and
the exit code is 1 because one check failed.

The real run: progress goes to stderr - the late injection, every tool
panel, the usage line per call, then one `eval` line per check. Stdout
carries two lines, and the exit code is 0 only when every check passed:

```text
score 4/5 · 11 model calls · 10 tool calls · 120,237 prompt tokens · cost 0.025941
report: C:\Users\you\simple-coding-harness\step_38_capstone\capstone\report.json
```

`--out DIR` puts the three files elsewhere; the path printed is absolute.

`report.json` has the keys `brief`, `model`, `started`, `seconds`,
`turns`, `continuations`, `model_calls`, `tool_calls`, `tool_call_total`,
`tool_errors`, `usage`, `cost`, `cost_note`, `notes`, `answer`,
`workspace_files`, `outside_changed`, `steps`, `evals` and `score`. Then
read `capstone/SCORECARD.md`. Add `--keep` to keep the temp workspace;
its path is printed last.

## Error handling

- A tool call with arguments that are not a JSON object, a name that is
  not a tool, or a tool that raises, gets one `Error: ...` tool message
  and the loop goes on - in the main agent and in `agent_planner`,
  which is what run 3 needed. A failing command is its output; a command
  over 60 s is killed with its process tree and the model reads the
  output so far.
- A dead model call: `call_llm` retries transport errors, 429 and 5xx
  five times with backoff; a 4xx is not retried. The turn then ends with
  the transcript valid, the runner sees a last message that is the
  user's and sends `CONTINUE`, at most twice. Run 1 is what that looks
  like: 400 on every call, score 1 of 5, exit code 1.
- A crash anywhere in the run (`run failed: <Type>: <message>` in the
  notes) still gets a report and a scorecard; the temp directories are
  removed either way unless `--keep`.
- Ctrl-C during the run: once is the step 35 steer prompt, which reads a
  line from the terminal even here; twice within two seconds ends the
  run with no report and the temp directories removed.
- Exit code: `0` when every check passed, `1` otherwise, including a run
  that never answered.
- `harness eval capstone/evals --workspace DIR` with a `DIR` that does
  not exist stops with `FileNotFoundError: workspace directory not found`.

## Gotchas / What this is not

- Windows has no OS sandbox, so a real run there relies on the model
  reading the brief and on check 5; the harness's write-outside guard is
  auto-approved for the run (section 3).
- Check 5 sees the parent temp directory only. Memory writes, checkpoints
  and the system temp directory are outside its view.
- The agent tools the model had - `agent_planner`, `agent_worker`,
  `agent_reviewer` - come from this step's `.agents/agents/`, read at
  import from the directory `run.py` was started in, not from the
  workspace. The shipped hooks do not run: `isolated` points the hook
  config at the workspace, which has none.
- The score is a model score. The reference solution passes 5 of 5 under
  `run.py` (the test replays it through a scripted fake); a real model's
  number moves with the model, the prompt and the day.
- `tool results with an error: 2` in the recorded run counts the two
  failed pytest outputs, matched by `PROBLEM_RE`, not two `Error:`
  results; there are none in that transcript.
- The tests check passes on any green suite, however small; the brief's
  "a test per endpoint" is not enforced.
- The tool named `bash` runs `cmd.exe` on Windows, so the model's
  commands are Windows commands there, and the recorded run's bugs are
  Windows bugs.

## The recorded run

The scorecard, report and transcript in `capstone/` are from the fourth
live run, on 2026-09-13, with `gpt-4.1-mini` through the OpenAI API. The
first three runs are documented here too, because two of them changed
the harness.

### Run 1: zero model calls

Every model call came back with a 400: the OpenAI API rejects a function
schema with `anyOf` at the top level, and the `task` tool's schema had one
to say that `description` or `descriptions` is required. OpenRouter and
DeepSeek had accepted it in every earlier step. The loop did what step 34
built it to do: it reported the error, did not retry a 4xx, and ended the
turn. The runner sent its two follow-ups, got the same answer, and wrote
a scorecard with a score of 1 out of 5, the one pass being the
outside-changes check. The fix is one line: the `anyOf` is gone and the
one-of-two rule lives in `task()`, which already returned an error when
neither came.

### Run 2: a question to nobody

| measure | value |
|---------|-------|
| score | 4 / 5 |
| model calls | 16 |
| tool calls | 15 |
| prompt tokens | 159,179 |
| cost | $0.030 |

The model wrote the app and the tests, ran pytest three times, fixed two
bugs, then answered with a summary that ended in "The README.md will be
created next. Would you like me to create it now?" In a chat the user
would say yes. Headless, the turn was over and the README check failed.
Step 30's isolation answers the `ask_user` tool with a note that nobody
is there, but a question in plain text is a final answer. The runner now
treats an answer that ends in a question mark the same way and sends the
same note as a user message.

### Run 3: a crash in a subagent

The first pytest run failed, and the model sent the step 36 `agent_planner`
tool to investigate. The planner tried to read `cli.py`, which does not
exist, and `read_file` raised. The exception went through the subagent's
loop, through `execute_all`, through `run_results` and out of `turn`. The
runner caught it, wrote a report with a score of 2 out of 5 and the note
`run failed: FileNotFoundError`. Section 6 above is the fix.

### Run 4: the recorded run

| measure | value |
|---------|-------|
| score | 4 / 5 |
| turns | 1 |
| model calls | 11 |
| tool calls | 10 |
| tool results with an error | 2 |
| prompt tokens | 120,237 |
| cached prompt tokens | 93,696 |
| completion tokens | 3,722 |
| cost | $0.026, estimated from list prices |
| wall time | 59.5 s |

Tool calls by name:

| tool | calls |
|------|-------|
| write_file | 3 |
| bash | 3 |
| agent_planner | 2 |
| str_replace | 2 |

The checks:

| check | result | detail |
|-------|--------|--------|
| 1_server_starts | pass | app.py starts and GET /health answers ok |
| 2_crud | fail | DELETE must return an empty body |
| 3_tests_pass | pass | test_app.py: 2 passed |
| 4_readme | pass | README.md has a 'Run' section with the uvicorn command |
| 5_no_outside_changes | pass | 2 files outside the workspace, none changed |

What happened, step by step:

1. The model wrote `app.py` in one call and `test_app.py` in the next.
   No `write_todos` this time; run 2 had planned first.
2. `python -m pytest -q` failed with `sqlite3.OperationalError: unable to
   open database file`. The test fixture opened a `NamedTemporaryFile`
   and handed its name to SQLite while the file was still open, which
   Windows does not allow. The output was 9,156 characters of tracebacks,
   just under the step 7 cap, so the model saw all of it.
3. The model called `agent_planner` with the error and the question of
   why the fixture fails. The planner, a read-only subagent from step 36,
   read both files and returned a numbered plan.
4. One `str_replace` changed the fixture to `delete=False` and an
   explicit close and unlink.
5. pytest failed again: `no such table: todos`. The fixture built a
   `TestClient` without a `with` block, so the startup code that creates
   the table never ran. This output was 10,097 characters: the cap kept
   the first 10,000, spilled the whole thing to a temp file and said so.
   The model never read the file; the first traceback was enough.
6. A second `agent_planner` call diagnosed exactly that.
7. One `str_replace` wrapped the client in `with`. pytest passed: 2
   tests.
8. The model wrote `README.md` with a `## Run` section and the endpoint
   list, and answered with a summary.

What went wrong and how the harness handled it:

- The two pytest failures are the model's bugs, and both are the kind a
  Windows machine exposes. The harness gave the model the traceback, the
  model asked a subagent, and the fix came back. The loop needed no help.
- The failed check is also the model's: the delete endpoint returns
  `JSONResponse(status_code=204, content=None)`, whose body is the text
  `null`, and the brief asked for an empty body. The model's own two
  tests did not cover it. The check did.
- Two tests is thin coverage. The brief asked for tests that cover every
  endpoint, and the tests check said "2 passed" and passed, because the
  check counts a passing suite, not its size. A stricter check would
  require one test per endpoint.
- 78% of the prompt tokens were served from the cache. The system prompt
  and the tool schemas are the stable prefix from step 6, and eleven
  calls paid for them once.
- The runner sent no follow-up. The turn ended with an answer and no
  question, the way run 2 did not.

The four runs together are one lesson: the harness is only tested by the
model it runs, and a new model is a new test. Two mechanisms that had
worked for eighteen steps failed on the first real run against a new
API, and both failures were invisible to a fake model that never rejects
a schema and never raises inside a tool.

### Run 5: the same tests on macOS

The recorded run was on Windows, where the harness has no OS sandbox.
The offline tests replay it on every platform in continuous integration,
and on macOS the pytest call inside the workspace failed. Two things
were wrong in `harness/sandbox.py`, both since step 12. The Seatbelt
profile was an f-string built once at import, with the project directory
of that moment, so under step 30's isolation the temp workspace was
still read-only; the review of the earlier steps made it a template
filled in per command. And pytest's `tmp_path` fixture, which the
model's tests used for the database, lives in the system temp directory,
which the profile never allowed; the Linux sandbox mounts a writable
`/tmp` since step 30, and the macOS profile now allows the temp
directory too, so both sandboxes agree:

`harness/sandbox.py`:

```python
(allow file-write* (subpath "{project}") (subpath "{tmp}") (literal "/dev/null"))
```

```python
        with tempfile.NamedTemporaryFile("w", prefix="simple-harness-", suffix=".sb", delete=False) as profile:
            profile.write(PROFILE.format(project=PROJECT, tmp=temp_dir()))
```

The profile goes to a fresh temp file per call rather than one shared
path, because two parallel tool calls writing one file would race.

The same run on macOS exposed one more: pytest printed more than the
300 characters stage 14 keeps once a turn is over, so the report's last
line for that call was the strip notice instead of "2 passed". The runner
now keeps every tool result as the model saw it, by wrapping
`history.strip` for the length of the run, and builds the report from
those.

Nothing about the model found this. A second operating system did.

## What to notice

- The checks import, they do not serve. A `TestClient` runs the app's
  startup code in-process, so there is no port, no process to kill and
  no race with a server that is still starting.
- The manifest is taken by the runner and read by the check. The check
  runs in a copy of the workspace and could not see the original parent
  on its own. The environment variable is the bridge, and the check
  fails without it.
- Grading is not running. With `workspace=`, `run_task` copies, skips
  the turn and checks. The task directories still need a `task.md`, and
  it is documentation now: what the check looks for.
- Every follow-up is recorded. The report's `continuations` list says
  which turn was sent and why, so a score is never a mystery of how many
  chances the model had.
- The cost is labelled. A number from the API and a number from a price
  table look the same in a cell. The report says which one it is.
- A tool exception is a result now. That is a change to the main loop's
  contract, made in this step because the capstone found it. The
  transcript stays valid either way; what changed is that the model gets
  to read what happened.
- The failed check stays failed. The reference solution passes every
  check, so the check is right and the model's delete endpoint is wrong.
  A capstone that only ever reports 5 out of 5 is measuring nothing.

## Diff from step 37

```bash
diff -r ../step_37_production_anatomy/harness harness
```

Added: `capstone/task.md`, `capstone/run.py` (`manifest`,
`workspace_files`, `plant_outside`, `cost_of`, `short_args`,
`summarise_transcript`, `why_continue`, `run_brief`, `run`,
`scorecard`, `transcript`, `main`), `capstone/evals/_common.py` and
the five check tasks, `capstone/reference/` (`app.py`, `test_app.py`,
`README.md`), `capstone/report.json`, `capstone/SCORECARD.md`,
`capstone/transcript.md`. Changed: `evaluate.py` (`run_task` and
`run_suite` take `workspace`; the report carries it; `load_suite`
resolves the suite path, so `harness eval evals` works with a relative
path), `agent.py` (`eval --workspace`), `sandbox.py` (`temp_dir`, the
macOS profile allows the temp directory), `pyproject.toml` (the
`capstone` extra: fastapi, httpx, uvicorn, pytest). Everything else is
unchanged from step 37.

## What the next step adds

Step 39 adds named approval modes: `default`, `accept-edits`,
`read-only`, `auto` and `plan`, a table that rewrites the verdict of the
rules before anyone is asked, switched with `/mode` or `--mode`.
