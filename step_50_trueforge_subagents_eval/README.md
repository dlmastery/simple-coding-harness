# Step 50 - Subagents, sessions and evaluation on TrueForge

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
server is named `s50-...`.

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
where single quotes are not quotes. The tools server now runs `bash` when
one is on PATH, and every task passes.

## Why these three together

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
MCP server rooted at it.

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
        config=RuntimeConfig(dynamic_sub_agents=DynamicSubAgentsConfig(enabled=True)),
    )
```

Stage 15 wrote `subagent.py`: a loop with a withheld tool set and a
turn cap. TrueForge ships the loop. `dynamic_sub_agents.enabled` gives
the root agent a `create_sub_agent` tool; the model writes the
instructions for each child, the server runs the children in parallel,
and each child returns only its final message. The rules match stage 15:
a child gets the same tools and sandbox as the root, cannot ask the user,
and cannot spawn children of its own.

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
        return printer
    out.write(f"turn {turn_id} is {turn.state.status}; replaying its stored events\n")
    return replay(list_events(client, session_id, turn_id), out)
```

Step 34 made the harness survive a crash by writing the transcript before
every call and resuming from it. On TrueForge the turn keeps running when
the client goes away. `get_turn` says whether it is still running.
`subscribe_to_turn` reopens the stream, and `after_sequence_number` skips
the events the client already saw; the sequence number is the `id` line
of each server-sent event. A finished turn has no live stream, so the
function replays the stored log instead.

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
        config=RuntimeConfig(dynamic_sub_agents=DynamicSubAgentsConfig(enabled=True), iteration_limit=40),
    ))
```

```python
    started = time.perf_counter()
    try:
        with ToolsServer(workspace, port=port) as tools:
            register_tools(client, tools.url)
            session_id = client.sessions.create(agent=spec or build_spec()).data.id
            turn_id, answer, metrics = run_turn(client, session_id, task.prompt, on_event)
        passed, detail = check(task, workspace, answer)
    except Exception as failed:  # noqa: BLE001 - one broken run must not end the suite
        session_id, turn_id, answer, metrics = "", "", "", {}
        passed, detail = False, f"run failed: {type(failed).__name__}: {failed}"
```

The task's `workspace/` is copied to a temp directory, as in step 30. The
model cannot open that directory: TrueForge runs in its own process, on
this machine inside WSL. So the workspace is served over MCP by
`tools_server.py`, started on a thread of the runner and rooted at the
copy. `register_tools` points the `s50-tools` entry at it, the session
attaches that server with `require_approval_for_tools: []` so no call
pauses for a human (step 30 replaced `ui.approve` for the same reason),
and `preload: true` loads every tool schema up front. One turn runs, the
tools server stops, and the checker reads the workspace. The `try` turns
a crash into a failed result with the exception as its detail.

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
    @server.tool(annotations=destructive, structured_output=False)
    def bash(command: str) -> str:
        """Run a bash command in the project root and return its combined stdout and stderr."""
        try:
            completed = subprocess.run(
                [BASH, "-c", command] if BASH else command, shell=not BASH, cwd=project,
                stdin=subprocess.DEVNULL,  # a pipe stdin makes rg and friends read it instead of the tree
                capture_output=True, text=True, timeout=BASH_TIMEOUT,
            )
```

The five tools of stage 5 as one FastMCP server over streamable HTTP.
`resolve` keeps every path under the project root and turns an escape
into an error string, so a wrong path is a tool result and not a crash.
The annotations are what TrueForge's default approval policy reads:
`readOnlyHint` on the readers, `destructiveHint` on the writers. The eval
turns approvals off; a chat session with the default policy would pause
on every `write_file`, `str_replace` and `bash`. The `bash` tool runs a
real `bash` when one is on PATH, Git Bash on this machine, and falls back
to the OS shell.

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

Start the TrueForge server as in step 46. Then, from this directory:

```bash
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

The three tasks from step 30 run one after another, each on port 8932.
The table lists pass or fail, wall time, input and output tokens, and the
first line of the answer; `evals/eval_report.json` holds the rest. The
command exits 0 when every task passed. `--keep` leaves the temp
workspaces in place; `--port` moves the tools server when 8932 is busy.

Run the offline tests from the repository root:

```bash
python run_tests.py 50
python check_snippets.py 50
```

The tests start a fake TrueForge server on a free port and point the real
SDK at it. The eval test goes one step further: the fake server, when it
receives the turn, connects to the real tools server the runner started
and writes `hello.txt` through `write_file`, so the checker sees a real
file.

## What to notice

- One stream, many threads. The client never starts a thread pool. It
  reads the `thread_id` on every event and indents. The server decides
  how many subagents run and when each returns.
- A stored turn replays with the same printer. The server keeps the
  events it streamed, deltas merged. Step 44 built that log by hand.
- Reconnect is a lookup. A turn outlives the client. `get_turn` says
  whether it is still running; `subscribe_to_turn` resumes from a
  sequence number; a finished turn replays from the log.
- The eval needs no state reset. Step 30 saved and restored every
  module global between tasks. Here a task is a session and a fresh
  tools server; nothing carries over.
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
| Recovery | Step 34: transcript written before every call, resume from disk | `get_turn` then `subscribe_to_turn(after_sequence_number=...)` |
| Usage per turn | Step 44: a usage entry per model call in the log | `turn.done` `state.metrics` aggregates the whole turn, threads included |
| Eval runner | Step 30: `harness eval SUITE`, real `turn()` in a reset process | One session per task, the workspace served by `tools_server.py` over MCP, `require_approval_for_tools: []` |
| Tool permissions | Stage 11: rules in `permissions.py` | `readOnlyHint` / `destructiveHint` on each MCP tool, `require_approval_for_tools` per server |
