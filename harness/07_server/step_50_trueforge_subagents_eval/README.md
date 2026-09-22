# Step 50 - Subagents, sessions and evaluation on TrueForge

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Move the loop behind a service**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 49 - Context, questions and stop conditions on TrueForge](../step_49_trueforge_context/README.md). Next: [Step 51 - TrueForge versus this codelab versus managed agents](../step_51_trueforge_comparison/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** three capabilities of the hand-built harness, run
against the TrueForge server instead. Parallel subagents (stage 15, step
29) arrive as `thread.created` and `thread.done` events inside one turn
stream, and a printer indents every event by its thread. The session store
(stage 8, step 44) lives on the server: list sessions, list turns, replay a
finished turn from its stored events, and reconnect to a running one
(step 34). The step 30 evaluation format runs unchanged through TrueForge:
every task gets a temp workspace served by the step's own MCP tools server,
one session with approvals off, one turn, and a checker. The report carries
the pass rate and the turn metrics per task.

This step is standalone. It needs a running TrueForge server; the setup and
the Windows note are in step 46's README. Everything it registers on the
server is named `s50-...`. Three environments take part: TrueForge (in WSL
on this machine) runs the loop and the subagents; `tools_server.py`, a
thread of `demo.py` on Windows, runs the file tools and `bash`; `check.py`
runs in the same Windows process against the temp workspace. Only the
middle one is the client's shell.

## Quick demo

```bash
python demo.py --threads "compare three sorting algorithms in parallel and summarise"
```

```text
turn 01m2g69kxyxt59gq6v59gwdbvn.local started
main called create_sub_agent(compare_merge_sort)
main called create_sub_agent(compare_quick_sort)
main called create_sub_agent(compare_heap_sort)
main spawned t1 compare_merge_sort: Compare the merge sort algorithm in terms of time complex...
main spawned t2 compare_quick_sort: Compare the quick sort algorithm in terms of time complex...
main spawned t3 compare_heap_sort: Compare the heap sort algorithm in terms of time complexi...
    t1   said: Here is a comparison of the merge sort algorithm based on time complexity, space comp...
main tool -> t1 returned
    t1   done (done): Here is a comparison of the merge sort algorithm based on...
    t3   said: Here is a comparison of the heap sort algorithm in terms of time complexity, space co...
main tool -> t3 returned
    t3   done (done): Here is a comparison of the heap sort algorithm in terms ...
    t2   said: Here's a comparison of the Quick Sort algorithm based on various aspects: 1. Time Com...
main tool -> t2 returned
    t2   done (done): Here's a comparison of the Quick Sort algorithm based on ...
main said: Here is a summary comparison of the three sorting algorithms: Merge Sort, Quick Sort,...
turn done: done (cache_read_tokens=1024, input_tokens=3970, output_tokens=1492, tokens=5462)

session 01m2g69kwf9t8bsxqq87936834
final answer (1561 chars): Here is a summary comparison of the three sorting algorithms: Merge Sort, Quick Sort, and Heap Sort.
...
```

```bash
python demo.py --eval
```

```text
running find_function ...
  PASS  expected 'settings.py' found in the answer
running fix_test ...
  PASS  check.py exited 0: 2 passed in 0.23s
running write_hello ...
  PASS  check.py exited 0: hello.txt has five lines of hello
task            pass      sec      in    out  answer
----------------------------------------------------
find_function   yes      39.8    6988    136  The function `parse_config` is defined i
fix_test        yes      45.3    9950    160  The bug I fixed was that the add functio
write_hello     yes      34.1    3526     32  done
total           3/3     119.3   20464    328  pass rate 100%
report: eval_report.json
```

Both outputs were recorded against the local server with
`openai/gpt-4-1-mini`. The first run of the suite scored 2/3: the
`find_function` subagent ran `rg 'def parse_config'` through `cmd.exe`,
where single quotes are not quotes. The tools server now runs a real
`bash` (`find_bash` below: Git Bash on Windows, never the WSL launcher in
`system32`), and every task passes.

## Files

```text
step_50_trueforge_subagents_eval/
├── .gitignore       ignores eval_report.json and __pycache__
├── client/          threads, sessions and the eval runner on TrueForge
│   ├── __init__.py  package marker
│   ├── common.py    connect(), as_dict() and the EventIndex every module shares
│   ├── threads.py   parallel subagents as threads; ThreadPrinter indents by thread
│   ├── sessions.py  list sessions, turns and stored events; replay; reconnect
│   └── evaluate.py  the step 30 eval format, one session per task over MCP
├── evals/           one folder per task: task.md, check.py or expect.txt, optional workspace/
├── tools_server.py  the five coding tools as an MCP server for the eval runner
├── demo.py          --threads, --eval, --sessions, --replay
├── test_step.py     offline tests: a fake server in a thread, the real SDK
└── README.md        this file
```

## Why these three together, and what breaks without a terminal status

Stage 15 built a subagent as a second loop over the same tools. Step 29
ran several of them on a thread pool and printed their panels with a tag.
Stage 8 wrote the transcript to a file and step 44 played it back. Step 30
measured the whole harness with a suite of tasks and checkers. All three
share one need: a record of what happened, by whom, in what order.

On TrueForge that record is the turn stream. The server runs the
subagents, stores every event, and serves the log back. The client no
longer owns a thread pool, a session file or a message list. It reads one
stream of events, each stamped with a `thread_id`, and decides how to show
it. The same printer draws a live stream and a stored one, because the
server stores what it streamed with the deltas merged.

The eval runner gains from the same fact. Step 30 spent most of its code
restoring module-level state between tasks. Here a task is a session: the
server holds the state, and the session ends with the task. What remains
on the client side is the workspace, which the model reaches through an
MCP server rooted at it. The session is deleted when the task ends
(unless `--keep`), so the server does not fill up with one session per
eval run.

What breaks without a terminal status: a turn stream can end three ways
that are not an answer. The server can report `error` (the model was
unavailable, the iteration limit tripped), the turn can end `done` but
paused on a `tool.approval_required` or `ask_user_question` nobody in an
eval will answer, and the connection can drop before `turn.done` arrives
at all. A runner that reads only the last main-thread text scores all
three by running the checker on a half-finished workspace and reports
`check.py exited 1` with no reason. Here `run_turn` returns a `status`
that only `turn.done` can set, questions are switched off in the eval
spec, and a task whose turn did not end `done` fails with the reason in
its `detail`: `turn ended error: model unavailable`, `turn paused:
tool.approval_required`, or `the stream ended without turn.done`.

## The code, piece by piece

### 1. Deltas merge into their message

`client/common.py`:

```python
class EventIndex:
    """Merges streamed deltas into their `model.message` base, keyed by event id."""

    def __init__(self):
        self.messages: dict[str, dict] = {}

    def add(self, event: dict) -> dict | None:
        """Record one event. Returns the merged message when this event completes it."""
        kind = event.get("type")
        if kind == "model.message":
            base = dict(event)
            base.setdefault("content", "")
            base["tool_calls"] = list(base.get("tool_calls") or [])
            self.messages[event["id"]] = base
            # a stored event is already merged; a live base fills in through deltas
            return base if base.get("finish_reason") else None
        if kind != "model.message.delta":
            return None
...
        if event.get("finish_reason"):
            base["finish_reason"] = event["finish_reason"]
            return base
        return None
```

A live `model.message` arrives empty. Its text and its tool calls follow
as `model.message.delta` events that share its `id`; tool-call fragments
carry an `index`, and their `arguments` strings concatenate. The delta
that carries `finish_reason` completes the message, and `add` returns it.
A stored message arrives merged with its `finish_reason` set, so `add`
returns it at once. Every printer in this step works on the merged dict
and never sees a delta.

### 2. One line per event, indented by thread

`client/threads.py`:

```python
    def line(self, thread_id, text: str) -> None:
        """One output line; subagent threads are indented under the main thread."""
        if thread_id is None:
            self.out.write(f"{text}\n")
            return
        indent = "" if thread_id == "main" else "    "
        self.out.write(f"{indent}{self.label(thread_id):<4} {text}\n")

    def handle(self, event) -> None:
        event = as_dict(event)
        kind, thread_id = event.get("type"), event.get("thread_id")
        if kind == "turn.created":
            self.line(None, f"turn {event.get('turn_id')} started")
        elif kind == "thread.created":
            info = event.get("agent_info") or {}
            self.spawned[(event.get("parent") or {}).get("tool_call_id")] = thread_id
            self.line(event.get("parent", {}).get("thread_id", "main"), f"spawned {self.label(thread_id)} {event.get('title')}: {short(info.get('input', ''), 60)}")
        elif kind in ("model.message", "model.message.delta"):
            merged = self.index.add(event)
            if merged is not None:
                self.message(merged)
        elif kind == "tool.response":
            child = self.spawned.get(event.get("tool_call_id"))
            result = f"{self.label(child)} returned" if child else short(event.get("content", ""), 70)
            self.line(thread_id, f"tool -> {result}")
```

Every event carries a `thread_id`: `main` for the root agent, a generated
id for a subagent, `None` for turn-level events. The printer gives each
new thread a short label in order of creation, `t1`, `t2`, `t3`, and
indents its lines by four spaces. `thread.created` names the parent thread
and the tool call that spawned the child, so the printer remembers which
`create_sub_agent` call belongs to which thread and prints `t1 returned`
when the parent's `tool.response` for that call arrives. Step 29 tagged
each subagent's panels with a name from the thread pool; here the tag
comes from the server.

### 3. Subagents are a config flag

`client/threads.py`:

```python
def build_spec(instructions: str = INSTRUCTIONS, model: str = MODEL, mcp_servers=None) -> SessionAgentSpecBody:
    """An inline agent with dynamic subagents switched on (they are on by default; this says so)."""
    spec = AgentSpec(
        model=Model(name=model),
        instructions=instructions,
        config=RuntimeConfig(
            dynamic_sub_agents=DynamicSubAgentsConfig(enabled=True),
            ask_user_questions=AskUserQuestionsConfig(enabled=False),  # on by default; nothing here answers one
        ),
    )
```

Stage 15 wrote `subagent.py`: a loop with a withheld tool set and a
turn cap. TrueForge ships the loop. `dynamic_sub_agents.enabled` gives
the root agent a `create_sub_agent` tool; the model writes the
instructions for each child, the server runs the children in parallel,
and each child returns only its final message. The rules match stage 15:
a child gets the same tools and sandbox as the root, cannot ask the user,
and cannot spawn children of its own. `ask_user_questions` is on by
default too; this printer has no way to answer one, so the spec turns it
off. A pause that arrives anyway (an approval under the default policy)
prints as `paused: tool.approval_required for c9 (this client does not
resume it)`, and `run_threads` returns the status alongside the text.

### 4. The server keeps the log

`client/sessions.py`:

```python
def list_events(client, session_id: str, turn_id: str) -> list[dict]:
    """The stored events of one turn as dicts, in insertion order, deltas already merged."""
    events, token = [], None
    while True:
        page = client.sessions.list_turn_events(session_id=session_id, turn_id=turn_id, page_token=token)
        events.extend(as_dict(event) for event in page.data)
        token = page.pagination.next_page_token
        if not token:
            break
    return events


def replay(events: list, out=None) -> ThreadPrinter:
    """Print a finished turn from its stored events. Returns the printer with the final text and metrics."""
    printer = ThreadPrinter(out or sys.stdout)
    for event in events:
        printer.handle(event)
    return printer
```

`GET /api/v1/sessions/{id}/turns/{turn}/events` returns what the stream
carried, in insertion order, with the deltas folded into their messages
and a page token when there is more. `replay` feeds those events to the
same `ThreadPrinter` the live run used, so the stored turn prints the same
lines. Step 44 needed a clock stamp and a usage entry in the session file
to get this; the server records both on every event and every message.

### 5. Reconnect or replay

`client/sessions.py`:

```python
def reconnect(client, session_id: str, turn_id: str, after_sequence_number: int | None = None, out=None) -> ThreadPrinter:
    """Pick a turn up again: subscribe if it is still running, replay it if it has finished."""
    out = out or sys.stdout
    turn = client.sessions.get_turn(session_id=session_id, turn_id=turn_id).data
    if turn.state.status == "running":
        out.write(f"turn {turn_id} is still running; subscribing\n")
        printer = ThreadPrinter(out)
        stream = client.sessions.subscribe_to_turn(session_id=session_id, turn_id=turn_id, after_sequence_number=after_sequence_number)
        for event in stream:
            printer.handle(event)
        if printer.status != "incomplete":
            return printer
        out.write("the live stream ended before turn.done; replaying the stored events\n")  # it finished in between
    else:
        out.write(f"turn {turn_id} is {turn.state.status}; replaying its stored events\n")
    return replay(list_events(client, session_id, turn_id), out)
```

Step 34 made the harness survive a crash by writing the transcript before
every call and resuming from it. On TrueForge the turn keeps running when
the client goes away. `get_turn` says whether it is still running.
`subscribe_to_turn` reopens the stream, and `after_sequence_number` skips
the events the client already saw; the sequence number is the `id` line
of each server-sent event. A finished turn has no live stream, so the
function replays the stored log instead. The turn can finish between
`get_turn` and `subscribe_to_turn`; the subscribe stream is then short or
empty, the printer's `status` stays `incomplete`, and the function falls
back to the stored log.

What this is not: drop recovery. Nothing in this step records the `id`
line of the events it streams (`run_threads` iterates the stream, not
`with_metadata()`), `demo.py` always passes `after_sequence_number=None`,
and the Python SDK (0.1.3) never reconnects a dropped stream on its own.
`reconnect` backs `--replay`: a way to look at a turn again from another
process, from the start.

### 6. A task is a workspace, a tools server and a session

`client/evaluate.py`:

```python
def build_spec(model: str = MODEL) -> SessionAgentSpecBody:
    """The eval agent: the tools server attached, every tool loaded, no approvals, subagents on."""
    tools = McpServer(name=TOOLS_NAME, preload=True, require_approval_for_tools=[])
    return SessionAgentSpecBody(spec=AgentSpec(
        model=Model(name=model),
        instructions=INSTRUCTIONS,
        mcp_servers=[tools],
        config=RuntimeConfig(
            dynamic_sub_agents=DynamicSubAgentsConfig(enabled=True),
            ask_user_questions=AskUserQuestionsConfig(enabled=False),  # nobody answers during an eval; a question would pause the turn for good
            iteration_limit=40,
        ),
    ))
```

```python
    started = time.perf_counter()
    session_id = turn_id = answer = ""
    metrics, status = {}, "incomplete"
    try:
        with ToolsServer(workspace, port=port) as tools:
            register_tools(client, tools.url)
            session_id = client.sessions.create(agent=spec or build_spec()).data.id
            turn_id, answer, metrics, status = run_turn(client, session_id, task.prompt, on_event)
        if status == "done":
            passed, detail = check(task, workspace, answer)
        else:  # error, cancelled, paused or a cut stream: the checker would only add noise
            passed, detail = False, answer if status != "incomplete" else "the stream ended without turn.done"
    except Exception as failed:  # noqa: BLE001 - one broken run must not end the suite
        passed, detail = False, f"run failed: {type(failed).__name__}: {failed}"
    seconds = round(time.perf_counter() - started, 3)
    if not keep:
        shutil.rmtree(root, ignore_errors=True)
        if session_id:  # the server keeps sessions forever otherwise; the report keeps the id
            try:
                client.sessions.delete(session_id=session_id)
            except Exception as failed:  # noqa: BLE001 - a leftover session is worth one line, not a failed task
                detail += f" (session {session_id} not deleted: {type(failed).__name__})"
```

The task's `workspace/` is copied to a temp directory, as in step 30. The
model cannot open that directory: TrueForge runs in its own process, on
this machine inside WSL. So the workspace is served over MCP by
`tools_server.py`, started on a thread of the runner and rooted at the
copy. `register_tools` points the `s50-tools` entry at it, the session
attaches that server with `require_approval_for_tools: []` so no call
pauses for a human (step 30 replaced `ui.approve` for the same reason),
and `preload: true` loads every tool schema up front. One turn runs, the
tools server stops, and the checker reads the workspace, but only when the
turn ended `done`: an `error`, a pause or a cut stream is a failed task
whose `detail` is the reason, and `status` goes into the report. The `try`
turns a crash into a failed result with the exception as its detail. The
session is deleted afterwards unless `--keep`; the ids stay in the report
either way. A `find_function` prompt invites a clarifying question, which
is why `ask_user_questions` is off: a question would end the turn `done`
with no output and leave the session pending on the server.

### 7. The tools, with their annotations

`tools_server.py`:

```python
    read_only = ToolAnnotations(readOnlyHint=True, destructiveHint=False)
    destructive = ToolAnnotations(readOnlyHint=False, destructiveHint=True)

    @server.tool(annotations=read_only, structured_output=False)
    def read_file(path: str) -> str:
        """Read a text file and return its contents. Paths are relative to the project root."""
        try:
            return resolve(project, path).read_text(encoding="utf-8")
        except (OSError, ValueError, UnicodeDecodeError) as failed:
            return f"Error: {failed}"
```

```python
def find_bash() -> str | None:
    """The bash the tool runs: /bin/bash elsewhere, Git Bash on Windows.

    From PowerShell `shutil.which("bash")` is `system32/bash.exe`,
    the WSL launcher: a different PATH, a `/mnt/c/...` cwd and no `python`.
    Git Bash is preferred wherever it is; None means the OS shell.
    """
    for candidate in (shutil.which("bash"), GIT_BASH):
        if candidate and Path(candidate).exists() and "system32" not in candidate.lower():
            return candidate
    return None
```

```python
    @server.tool(annotations=destructive, structured_output=False)
    def bash(command: str) -> str:
        """Run a bash command in the project root and return its combined stdout and stderr."""
        proc = subprocess.Popen(
            [BASH, "-c", command] if BASH else command, shell=not BASH, cwd=project,
            stdin=subprocess.DEVNULL,  # a pipe stdin makes rg and friends read it instead of the tree
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace",  # never a UnicodeDecodeError on odd output
            env=BASH_ENV, **NEW_GROUP,
        )
        try:
            out, err = proc.communicate(timeout=BASH_TIMEOUT)
        except subprocess.TimeoutExpired:
            kill_tree(proc.pid)
            out, err = proc.communicate()
            return f"Timed out after {BASH_TIMEOUT}s and was killed. Output so far:\n{(out + err).strip()}"
```

The five tools of stage 5 as one FastMCP server over streamable HTTP.
`resolve` keeps every path under the project root and turns an escape
into an error string, so a wrong path is a tool result and not a crash.
The annotations are what TrueForge's default approval policy reads:
`readOnlyHint` on the readers, `destructiveHint` on the writers. The eval
turns approvals off; a chat session with the default policy would pause
on every `write_file`, `str_replace` and `bash`. The `bash` tool runs on
the *client* machine, in whichever shell `find_bash` resolves: `/bin/bash`
on Linux and macOS; on Windows, Git Bash from PATH or from its default
install path, and never `C:\Windows\system32\bash.exe`. That one is the
WSL launcher, which is what `shutil.which("bash")` returns from a
PowerShell prompt: it would run every command inside WSL with a
`/mnt/c/...` cwd and no `python` on PATH, and `fix_test`'s `python -m
pytest` would fail with `command not found`. With no bash at all the tool
falls back to the OS shell (`cmd.exe`), where single quotes do not quote.
The command gets no stdin and no pager, runs in its own process group,
and a timeout kills the whole group and returns the partial output.

`ToolsServer.start()` refuses a port that already accepts connections
(`OSError: port 8932 is already in use; pick another with --port`).
Without that check, a previous task's server still draining a connection
would keep the port, uvicorn's bind would fail inside its thread, and the
next task would talk to the old server rooted at a workspace that no
longer exists.

### 8. The report

`client/evaluate.py`:

```python
def summarise(results: list[Result]) -> dict:
    """Pass rate and summed metrics over a list of results."""
    passed = sum(1 for r in results if r.passed)
    totals: dict = {}
    for result in results:
        for key, value in result.metrics.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0) + value
    return {
        "runs": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results), 3) if results else 0.0,
        "seconds": round(sum(r.seconds for r in results), 3),
        "metrics": totals,
    }
```

Each result keeps the `metrics` dict from its `turn.done`:
`total_input_tokens`, `total_output_tokens`, `total_tokens`, the cache
counters, and `total_cost_in_usd` when the provider reports one. The
summary sums every numeric field. Step 30 got the same numbers by
intercepting `ui.usage` on every model call, subagents included; here the
server aggregates the whole turn, threads included, into one dict.
`eval_report.json` holds the summary, the model, and one entry per task
with its answer, its detail, its session and turn ids, so `demo.py
--replay SESSION` can show any run again.

## Run it

Prerequisites: the TrueForge server of step 46 (in WSL on Windows) with
the model registered; `pip install mcp uvicorn` for the tools server (the
root `requirements.txt` lists both). `TRUEFORGE_BASE_URL` and
`TRUEFORGE_MODEL` are honoured, and `--base-url` overrides the first. From
this directory, in bash or PowerShell (the commands are the same):

```bash
python demo.py --threads "compare three sorting algorithms in parallel and summarise"
```

```powershell
python demo.py --threads "compare three sorting algorithms in parallel and summarise"
```

Expect three `spawned` lines, the three subagents' `said` lines indented,
three `returned` lines on the main thread, the summary, and the token
totals of the whole turn. Then:

```bash
python demo.py --sessions
python demo.py --replay SESSION_ID
```

`--sessions` lists the newest five sessions with their turns. `--replay`
prints the last turn of a session from the stored log; the lines match the
live run. Then:

```bash
python demo.py --eval
```

The three tasks from step 30 run one after another, each on port 8932;
between tasks the previous server must have let go of the port, or the
next task fails with `run failed: OSError: port 8932 is already in use`.
The table lists pass or fail, wall time, input and output tokens, and the
first line of the answer; `evals/eval_report.json` holds the rest. The
command exits 0 when every task passed. `--keep` leaves the temp
workspaces and the sessions in place; without it each session is deleted
after its check. `--port` moves the tools server when 8932 is busy.

Expected output: the Quick demo above. The API has no delete for MCP
server settings, so `s50-tools` stays registered after the suite, pointing
at a port nothing listens on; the next run replaces it in place.

Run the offline tests from the repository root:

```bash
python run_tests.py 50
python check_snippets.py 50
```

The tests start a fake TrueForge server on a free port and point the real
SDK at it. The eval test goes one step further: the fake server, when it
receives the turn, connects to the real tools server the runner started
and writes `hello.txt` through `write_file`, so the checker sees a real
file. Other tests end a turn in `error`, pause it, cut the stream before
`turn.done`, refuse a port in use, resolve `bash` past the WSL launcher,
round-trip UTF-8 through `write_file` and `bash`, and kill a stuck
command.

## Error handling

- **Server down or a refused request.** `request failed: http://localhost:8790 is not answering (ConnectError: ...)`
  on stderr, exit 1, in every mode. Inside `--eval` a failed request is one
  failed task (`run failed: ConnectError: ...`) and the suite goes on.
- **A turn that ends in `error` or `cancelled`.** `--threads` prints
  `turn done: error (...) model unavailable` and exits 1; the tokens spent
  before the stop are still in the line. `--eval` fails the task with
  `turn ended error: ...` and never runs the checker.
- **A paused turn.** `--threads` prints `paused: tool.approval_required
  for ... (this client does not resume it)` and exits 0 because the turn
  ended `done`; `--eval` fails the task with `turn paused: ...`.
- **A dropped stream.** No `turn.done`: the status is `incomplete`,
  `--threads` exits 1, `--eval` fails the task with `the stream ended
  without turn.done`. The turn may still be running on the server;
  `--replay SESSION` shows it once it has finished.
- **A tool that fails.** Every tool returns `Error: ...` as its result;
  `bash` returns `Timed out after 120s and was killed. Output so far:`
  plus the partial output. Nothing raises on the tools server side.
- **`--replay` on a session with no turns.** `session ... has no turns`,
  exit 1. An unknown session id is a refused request (404), exit 1.
- **ctrl-c.** There is no prompt in this step to interrupt. ctrl-c while a
  turn streams ends the demo with a `KeyboardInterrupt`; the turn keeps
  running on the server and the session is not deleted.

## Gotchas / what this is not

- **Three environments.** TrueForge (WSL) runs the model loop and the
  subagents; `tools_server.py` runs the file tools and `bash` in the
  `demo.py` process on Windows; `check.py` runs in that same process. A
  path in a task prompt means the workspace on the client, not anything
  the server can see.
- **`bash` on Windows** is Git Bash, found by `find_bash`; `python` and
  `rg` must be on *that* PATH for `fix_test` and `find_function`. Without
  Git Bash the tool runs `cmd.exe`.
- **No drop recovery.** `reconnect` is a lookup for `--replay`; no
  sequence number is recorded while streaming, and the SDK does not
  reconnect on its own. A dropped stream is `incomplete`, not resumed.
- **Sessions are deleted after an eval task** (unless `--keep`), not
  after `--threads`; those stay on the server. `s50-tools` stays
  registered after every run.
- **Port reuse.** One port for the whole suite; a server that has not let
  go of it by the next task fails that task rather than serving a stale
  workspace.
- **Questions are off** in both specs; a prompt that needs one gets a
  plain answer or a refusal. Subagents get no approval prompt either: the
  eval sets `require_approval_for_tools: []`, and `--threads` has no tools.

## What to notice

- One stream, many threads. The client never starts a thread pool. It
  reads the `thread_id` on every event and indents. The server decides
  how many subagents run and when each returns.
- A stored turn replays with the same printer. The server keeps the
  events it streamed, deltas merged. Step 44 built that log by hand.
- Reconnect is a lookup. A turn outlives the client. `get_turn` says
  whether it is still running; `subscribe_to_turn` can resume from a
  sequence number (this step passes none); a finished turn replays from
  the log.
- The eval needs no state reset. Step 30 saved and restored every
  module global between tasks. Here a task is a session and a fresh
  tools server; nothing carries over, and the session is deleted at the
  end.
- A status is not a text. `run_turn`, `run_threads` and `reconnect` all
  hand back a status that only `turn.done` can set, so a dropped stream,
  an error and a pause are three outcomes, not an empty answer.
- The workspace is a service. TrueForge cannot open the client's files.
  The tools server makes one directory reachable and nothing else, and
  `resolve` enforces that boundary inside every tool.
- Annotations are the permission rules. `readOnlyHint` and
  `destructiveHint` on the MCP tools are what `require_approval_for_tools`
  reads. The eval sets it to `[]`; a chat would keep the default.
- The pass rate is a number about the environment too. The first suite
  run lost `find_function` to `cmd.exe` quoting, not to the model.

## This codelab versus TrueForge

| Capability | This codelab | TrueForge |
|------------|--------------|-----------|
| Subagent | Stage 15: `subagent.py`, a second loop with a withheld tool set | `config.dynamic_sub_agents.enabled`; the model calls `create_sub_agent` |
| Parallel subagents | Step 29: `task` takes a list, runs them on a thread pool, tags the panels | Several `create_sub_agent` calls in one message; `thread.created` / `thread.done` per child, `thread_id` on every event |
| Session store | Stage 8: JSONL file per session, `--resume` | Sessions and turns on the server; `sessions.list`, `list_turns`, `previous_turn_id: auto` |
| Replay | Step 44: `harness replay <id>` from the stamped log | `GET .../turns/{turn}/events`, deltas already merged, through the same printer |
| Recovery | Step 34: transcript written before every call, resume from disk | `get_turn` then `subscribe_to_turn(after_sequence_number=...)`; the client must record the sequence numbers itself (this step does not) |
| Usage per turn | Step 44: a usage entry per model call in the log | `turn.done` `state.metrics` aggregates the whole turn, threads included |
| Eval runner | Step 30: `harness eval SUITE`, real `turn()` in a reset process | One session per task, the workspace served by `tools_server.py` over MCP, `require_approval_for_tools: []` |
| Tool permissions | Stage 11: rules in `permissions.py` | `readOnlyHint` / `destructiveHint` on each MCP tool, `require_approval_for_tools` per server |

## What the next step adds

Step 51 is a written comparison, not code: the hand-built harness of
steps 01 to 45 against TrueForge across every capability of steps 46 to
50, with the token and cost numbers of both.

<!-- harness-learning-check -->
## Check your understanding

Why reconcile live-stream state with stored events when reconnecting?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

The turn can finish between observation and subscription. A reliable account needs the actual terminal outcome, not an assumption about connection timing.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
