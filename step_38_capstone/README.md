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
    with isolated(workspace, root / "sessions", session_id, usage) as cwd:
        messages = [{"role": "system", "content": system_prompt_for(cwd)}]
        try:
            if not grading:
                messages = agent.turn(messages, task.prompt)
            answer, error = agent.last_reply(messages), None
```

Every task still gets its own fresh copy, so a check that leaves files
behind, such as pytest with its caches, cannot affect the next one. The
model turn is skipped, and the `task.md` of each task describes what the
check looks for rather than prompting an agent. The `harness eval`
subcommand exposes the same thing as `--workspace DIR`.

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
in the scorecard. The tests check runs `python -m pytest -q` and fails on
exit code 5 as well, because a suite that collects nothing is not a
passing suite. The README check finds a heading that contains "run" and
requires the word `uvicorn` under it.

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
and the transcript ends in a tool result. The model call fails for good
and the transcript ends in the user message. Or the model answers with a
question, which in a chat would wait for the user and here waits for
nobody. The runner sends a follow-up for each, at most twice, and records
why. The second live run below is the reason the question case exists.

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
and the score. The cost comes from the usage dict when the API reports
one, as OpenRouter does, and otherwise from a small price table for the
OpenAI models, and the report says which. The scorecard is the same data
as markdown. The transcript file keeps every message with tool results
cut to forty lines.

### 6. A tool that raises

The third live run ended in a `FileNotFoundError` from a subagent's
`read_file` call. Nothing between the tool function and the loop caught
it, so in a chat the harness would have exited, with the transcript saved
for `--resume` and step 34's `recover`. Headless there is no resume, so
the run was over.

`harness/tools.py`:

```python
    try:
        result = TOOLS[tool_call.function.name](**args)
    except Exception as failed:  # noqa: BLE001 - a missing file or a wrong argument is the model's problem to fix
        result = f"Error: {type(failed).__name__}: {failed}"
```

The result reaches the model as text, the same way a failed command or a
denied call does, and the model reads it and tries something else. The
change sits in `run`, so it covers the main loop, the explorer subagent
and the step 36 definitions alike.

## Run it

Install the harness and the capstone extras, then run the tests:

```bash
pip install -e ".[capstone]"
python run_tests.py 38
python check_snippets.py 38
```

Grade the reference solution without a model:

```bash
harness eval capstone/evals --workspace capstone/reference
```

Four checks pass and the fifth reports that `CAPSTONE_MANIFEST` is not
set, because nothing ran that could have changed anything.

Run the capstone for real. It needs a model that follows a long system
prompt and calls tools well; a small chat model will not do:

```bash
BASE_URL=https://api.openai.com/v1 API_KEY=... MODEL=gpt-4.1-mini python capstone/run.py
```

Progress goes to stderr: the late injection, every tool panel, the
usage line per call, then one `eval` note per check. Stdout ends with
one line of numbers and the report path, and the exit code is 0 only
when every check passed. Then read `capstone/SCORECARD.md`. Add `--keep`
to keep the temp workspace and its path is printed last.

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
path), `agent.py`
(`eval --workspace`), `tools.py` (`run` turns an exception into an
`Error:` result), `subagent.py` (`TASK_SCHEMA` has no top-level
`anyOf`), `pyproject.toml` (the `capstone` extra: fastapi, httpx,
uvicorn, pytest). Everything else is unchanged from step 37.
