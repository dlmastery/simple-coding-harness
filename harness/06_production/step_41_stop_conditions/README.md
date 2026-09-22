# Step 41 - Stop conditions

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Make a run inspectable**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 40 - Handoffs](../step_40_handoffs/README.md). Next: [Step 42 - Streaming tool output](../step_42_streaming_tool_output/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** the turn gets explicit ways to end, and budgets
for when it does not end on its own. `harness/stop.py` holds all of
them. A `finish(summary)` tool lets the model say the turn is over: the
result is the summary, the loop stops after that reply's results are
in, and the summary is the answer `-p` prints. Three budgets guard the
loop: `MAX_TURN_CALLS`, step 34's cap on model calls per turn, moved
here; `MAX_SESSION_COST`, a cap in dollars on the whole session, priced
from the cost OpenRouter reports when asked and estimated from a price
table on every other host; and `MAX_TURN_SECONDS`, a cap on the
wall-clock time of one turn. When one trips, the loop stops and prints
why; the caps are checked before a model call, never during a tool. A
`Stop` hook joins step 27's hook events: it runs when the turn is about
to end, and a hook that exits 2 blocks the stop, its stderr becomes a
user message, `Stop blocked: ...`, and the agent continues. The shipped
example, `.agents/require_tests.py`, sends the agent back when a turn
edited a `.py` file and did not run pytest after the edit. `/cost`
shows what the session spent and the budgets.

## Files

```text
step_41_stop_conditions/
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
│   ├── evaluate.py       the evaluation harness; every task is its own session budget and records its cost
│   ├── handoff.py        handoffs: the conversation moves to another agent definition
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events; Stop joins them, and an exit 2 blocks the stop
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs: commands that run while the chat goes on
│   ├── llm.py            the model call with retries; EXTRA_BODY asks OpenRouter for the cost
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── modes.py          named permission policies, one layer above the rules
│   ├── permissions.py    the rules, then modes.apply rewrites an allow or an ask
│   ├── pipeline.py       the plan, work, review pipeline behind /pipeline
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line
│   ├── sandbox.py        an OS sandbox for bash; popen() and kill_tree() for a timeout
│   ├── session.py        JSONL session log; {"handoff": name} markers replayed by load(), not by all_sessions()
│   ├── skills.py         skills, unchanged since stage 9
│   ├── stop.py           stop conditions: finish, the three budgets, the Stop hook
│   ├── subagent.py       the subagent loop; spends and checks the session budget
│   ├── todos.py          the plan behind write_todos
│   ├── tools.py          the tool registry; finish in TOOLS but not TOOL_SCHEMAS
│   └── ui.py             rich panels; handoff() draws the handoff -> name line
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
├── test_step.py     offline tests: finish, the budgets, the Stop hook, a denied finish, eval budgets
├── pyproject.toml   package metadata; version 0.41.0
└── README.md        this file
```

## Why a loop needs more than one way to stop

Up to now a turn ended in one of three ways: the model answered without
tool calls, a model call failed for good, or `MAX_CALLS` calls had been
made. The first is the normal end, and it is the model's decision by
omission: it stops calling tools, so the loop stops. That is implicit,
and it has two problems.

The first problem is that the model has no way to say "done" while it
still has calls to make. A reply that writes the last file and wants to
end has to spend one more call to say so. `finish` removes that call:
the reply carries the last edit and the summary together, and the loop
knows the turn is over as soon as the results are in.

The second problem is the opposite: the model stops too early, before
the tests ran or before the work is checked. A user watching the screen
says "run the tests" and the agent goes on. A user who is not watching,
a headless run or an evaluation, gets a half-finished answer. A `Stop`
hook is the check that runs at that moment. It reads what the turn did
and can refuse the end. The refusal is a user message, so the agent
reads it the way it reads any instruction and goes on. A cap on the
refusals keeps a hook that is never satisfied from running the agent
forever.

The budgets are for the turns that never reach either end. Step 34
capped the calls of one turn. A cap on calls does not cap money: forty
calls on a long transcript cost more than forty short ones, and a
session of many turns has no cap at all. A cap on calls does not cap
time either: one call can wait minutes on a slow provider. The three
caps together are the promise the harness makes to the person paying
for it: a turn ends, and a session ends, whatever the model does.

### What breaks without it

Step 40's loop has one cap, forty calls per turn. A model that reads a
file, edits it, reads it again and never answers spends forty calls of a
100k-token transcript - a few dollars - before the harness notices, and
then the next user message starts the count again. Ask it in a loop
from a script and there is no ceiling at all. With no `finish`, a
headless `-p` run prints whatever text happened to be in the last reply,
which after a batch of tool calls is often nothing. And with no Stop
hook, "always run the tests before you answer" is a sentence in the
system prompt the model is free to forget.

## The code, piece by piece

### 1. The finish tool

`harness/stop.py`:

```python
SPENT = 0.0       # dollars this session has cost so far, every model call counted
STARTED = None    # clock() when the current turn began
SUMMARY = None    # the summary a finish call gave in this reply, until the loop reads it
BLOCKS = 0        # times the Stop hooks have sent the agent back this turn
...
def finish(summary: str) -> str:
    """End the turn after this reply's results are in. Returns the summary."""
    global SUMMARY
    SUMMARY = (str(summary) if summary else "").strip() or "(finished without a summary)"
    return SUMMARY
...
def finished():
    """The summary a finish call gave in this reply, or None. Reading it clears it."""
    global SUMMARY
    summary, SUMMARY = SUMMARY, None
    return summary
```

`finish` is a tool like any other: it runs through the permissions, the
hooks and the executor, and its result goes in the transcript. What it
does is record the summary. The loop reads it with `finished()` after
the results of the reply are in, so a reply that carries an edit and a
`finish` runs the edit first. The tool is in `TOOLS` but not in
`TOOL_SCHEMAS`: `agent.turn` adds its schema next to the active agent's
set, `subagent.WITHHELD` keeps it from every subagent, and
`plan.offered` lets it run in plan mode, like `submit_plan`.

### 2. The price of a call

`harness/stop.py`:

```python
def cost_of(usage):
    """The dollars one model call cost, and where the number came from.

    The cost the usage carries wins: OpenRouter reports one when asked
    (llm.EXTRA_BODY). Otherwise the tokens are priced from PRICES, with
    the cached part of the prompt at its own rate.
    """
    usage = usage or {}
    if usage.get("cost") is not None:
        return float(usage["cost"]), "reported by the API"
    prompt_price, completion_price, cached_price = prices()
    cached = int(usage.get("cached_tokens") or 0)
    prompt = max(int(usage.get("prompt_tokens") or 0) - cached, 0)
    completion = int(usage.get("completion_tokens") or 0)
    return (prompt * prompt_price + completion * completion_price + cached * cached_price) / 1_000_000, "estimated from list prices"


def record(usage):
    """Add one model call to SPENT. Returns what the call cost."""
    global SPENT
    cost, _ = cost_of(usage)
    SPENT += cost
    return cost
```

Only OpenRouter reports a cost, and only when asked. `harness/llm.py`:

```python
EXTRA_BODY = {"usage": {"include": True}} if "openrouter" in config.BASE_URL else {}
```

goes out as `extra_body` on every request, and `usage_from` reads the
`cost` field of the usage chunk into the usage dict, `None` on any
other host. When that key is present it is the number. When it is not,
the tokens are priced: `PRICES` maps a model to its prompt, completion
and cached-prompt price per million tokens, and a model not in the
table gets `FALLBACK_PRICES`, which the `PRICE_PROMPT`,
`PRICE_COMPLETION` and `PRICE_CACHED` environment variables set. The
table has three `gpt-4.1` entries; the default model,
`deepseek/deepseek-v4-flash`, is not in it, so a default install on a
non-OpenRouter host is priced at the fallback $1 / $4 / $0.25 per
million, which is far above that model's list price. `/cost` says so
(`fallback prices, set PRICE_PROMPT, ...`); set the three variables to
the real prices or the $5 cap trips early. `record` is called wherever
a model call returns: the main loop, the subagent loop and the
compaction summariser. A subagent spends the same budget as the agent
that started it, and checks it too: `subagent.loop` asks
`stop.tripped(0)` before each of its own calls and returns `(the
subagent stopped: ...)` when the session's cost or the turn's clock is
over.

### 3. The three budgets

`harness/stop.py`:

```python
MAX_TURN_CALLS = env_number("MAX_TURN_CALLS", 40)       # model calls one turn may make
MAX_SESSION_COST = env_number("MAX_SESSION_COST", 5.0)  # dollars one session may spend
MAX_TURN_SECONDS = env_number("MAX_TURN_SECONDS", 900.0)  # wall-clock seconds one turn may take
MAX_STOP_BLOCKS = 3      # times the Stop hooks may send the agent back in one turn
...
def tripped(calls):
    """The report for the budget this turn has crossed, or None when it may go on.

    calls is how many model calls the turn has made. The three checks run
    before every model call, so the call that would cross a line is the
    one that is not made.
    """
    if calls >= MAX_TURN_CALLS:
        return f"stopped after {calls} model calls in one turn (MAX_TURN_CALLS={MAX_TURN_CALLS}); say continue to go on"
    if SPENT >= MAX_SESSION_COST:
        return (
            f"stopped: this session has cost ${SPENT:.4f}, over MAX_SESSION_COST=${MAX_SESSION_COST:.2f}; "
            "raise it in the environment and start again"
        )
    seconds = elapsed()
    if seconds >= MAX_TURN_SECONDS:
        return f"stopped after {seconds:.0f}s in one turn (MAX_TURN_SECONDS={MAX_TURN_SECONDS:.0f}); say continue to go on"
    return None
```

One function, asked before every model call, answers with the report
or with `None`. The check sits before the call, not after, so the call
that would cross a line is the one that is not made. The transcript
ends in a valid place either way: every call that was made has its
results. Two of the caps reset per turn, and their reports say
`continue` goes on. The cost cap is per session and stays tripped:
`agent.turn` asks `stop.tripped(0)` before it appends the next user
message, so a spent session prints the same report and leaves the
transcript as it was, and the way on is a higher `MAX_SESSION_COST` in
the environment. `env_number` reads each variable: a value that is not
a number is a note on stderr and the default, not a crash at import.

The settings, in one place:

| variable | default | unit | scope |
|---|---|---|---|
| `MAX_TURN_CALLS` | 40 | model calls | per turn; `continue` starts a new turn |
| `MAX_SESSION_COST` | 5.0 | dollars | per session (per task in `eval`) |
| `MAX_TURN_SECONDS` | 900 | seconds of wall clock | per turn |
| `MAX_STOP_BLOCKS` | 3 (not an env var) | Stop hook blocks | per turn |
| `PRICE_PROMPT` / `PRICE_COMPLETION` / `PRICE_CACHED` | 1.0 / 4.0 / 0.25 | dollars per million tokens | models not in `PRICES` |

### 4. The Stop event

`harness/hooks.py`:

```python
EVENTS = ("PreToolUse", "PostToolUse", "UserPromptSubmit", "PreCompact", "SessionStart", "SessionEnd", "Stop")
...
EVENT_KEYS = ("event", "tool_name", "tool_input", "tool_result", "ok", "prompt", "cwd", "answer", "calls", "blocks", "ended_by")  # the last four: Stop
```

`harness/stop.py`:

```python
def turn_calls(messages, start):
...
    results = {m.get("tool_call_id"): m.get("content") for m in messages[start:] if m.get("role") == "tool"}
    calls = []
    for message in messages[start:]:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
...
            calls.append({
                "tool_name": call["function"]["name"],
                "tool_input": args if isinstance(args, dict) else {},
                "tool_result": result if not isinstance(result, str) else result[:RESULT_CHARS],
            })
    return calls
```

The hook machinery of step 27 is unchanged: one more event name, and
four more keys the event may carry. A `Stop` event has `answer`, the
final text or the finish summary; `calls`, every tool call of the turn
with the same three keys a `PostToolUse` event has; `blocks`, how many
times a Stop hook already sent the agent back this turn; and
`ended_by`, `answer` or `finish`. The calls are read from the
transcript, from the index where the turn began, so a hook sees what
ran and what came back, and a call without a result yet has
`tool_result` `None`.

### 5. Asking the hooks, and sending the agent back

`harness/stop.py`:

```python
def may_stop(messages, start, answer, ended_by="answer"):
...
    global BLOCKS
    if BLOCKS >= MAX_STOP_BLOCKS:
        _note(f"the Stop hooks blocked {BLOCKS} times this turn; stopping anyway")
        return None
    outcome = hooks.run_hooks("Stop", {"answer": answer, "calls": turn_calls(messages, start), "blocks": BLOCKS, "ended_by": ended_by})
    if not outcome.blocked:
        return None
    BLOCKS += 1
    return outcome.reason


def send_back(messages, reason):
    """Append the block as a user message, so the agent reads it on the next call."""
    from . import session  # here, not at the top: session imports handoff, which imports the tools

    line = f"Stop blocked: {reason}"
    messages.append({"role": "user", "content": line})
    session.save(messages)
    _note(line)
```

`may_stop` runs the hooks and returns the reason of the first block, or
`None`. A command hook blocks by exiting 2, and its stderr is the
reason, as it has been since step 27. `send_back` turns the reason into
a user message, saved like every other message, so a crash after a
block resumes with the block in place. `MAX_STOP_BLOCKS` is the
guard: after three blocks in one turn the hooks are not asked again,
and the turn ends with a note that says so.

### 6. The loop

`harness/agent.py`:

```python
    while True:
        report = stop.tripped(calls)
        if report:
            ui.note(report)  # a budget is crossed: no more calls this turn
            break
...
        if not message.tool_calls:
            reason = stop.may_stop(messages, start, message.content or "")  # the Stop hooks have the last word
            if reason:
                stop.send_back(messages, reason)
                continue  # the block is a user message now; the agent reads it on the next call
            break
...
        finally:
            handoff.switch(messages)  # a handoff_to result in this reply: the next call is the new agent's - even when the user leaves

        summary = stop.finished()
        if summary is not None:  # the reply called finish: its other calls ran, and the turn ends here
            reason = stop.may_stop(messages, start, summary, ended_by="finish")
            if reason:
                stop.send_back(messages, reason)
                continue
            ui.note("finish: the turn ends here")
            break
```

The `MAX_CALLS` check of step 34 became `stop.tripped(calls)`. The
`break` on a reply without tool calls became a question to the Stop
hooks first. And after the results of a reply and a pending handoff, a
`finish` is applied the same way: the hooks first, then the end. Both
ends go through the same `may_stop`, so a model cannot get past a Stop
hook by calling `finish` instead of answering. A budget trip does not
ask the hooks: a budget is the harness's decision, and a hook that
sent the agent back would spend past the cap.

Headless, `last_reply` is what `-p` prints, and a `finish` counts only
when it ran:

```python
def last_reply(messages):
...
    results = {m.get("tool_call_id"): m.get("content") for m in messages if m.get("role") == "tool"}
    for message in reversed(messages):
        if message["role"] != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            summary = stop.finish_summary(call["function"]["arguments"])
            if call["function"]["name"] == "finish" and results.get(call["id"]) == summary:
                return summary
        if message.get("content"):
            return message["content"]
    return ""
```

A `finish` that a PreToolUse hook blocked or a session `never` denied
has `Blocked by ...` as its tool result, not the summary, so it is not
the answer; the text of the last reply is.

### 7. The example hook

`.agents/require_tests.py`:

```python
event = json.load(sys.stdin)
calls = event.get("calls") or []

last_edit = None  # (index in calls, path) of the newest edit to a .py file
for index, call in enumerate(calls):
    path = str((call.get("tool_input") or {}).get("path") or "")
    if call.get("tool_name") in ("write_file", "str_replace") and path.endswith(".py"):
        last_edit = (index, path)

if last_edit is not None:
    index, path = last_edit
    tested = any(
        call.get("tool_name") == "bash" and "pytest" in str((call.get("tool_input") or {}).get("command") or "")
        for call in calls[index + 1:]
    )
    if not tested:
        print(f"tests were not run after editing {path}; run pytest, then answer", file=sys.stderr)
        sys.exit(2)
```

The hook finds the newest edit to a `.py` file and looks for a `bash`
call whose command contains `pytest` after it. It is a substring
check, not "the tests passed": `echo pytest` satisfies it (the tests
use exactly that), and a pytest run that failed satisfies it too. A
hook that reads `tool_result` for `passed` is a few more lines. No
edit, or an edit followed by pytest, exits 0 and the turn ends. An
edit with no pytest after it exits 2, and the agent reads `Stop
blocked: tests were not run after editing calc.py; run pytest, then
answer`. `.agents/hooks.json` registers it under `"Stop"`, with no
matcher: a Stop event has no tool name, so every Stop hook runs.

## Run it

Prerequisites: Python 3.10+, `API_KEY` (and optionally `BASE_URL`,
`MODEL`) in the environment or in `~/.simple-harness/env`. For a
model outside `PRICES` on a host that is not OpenRouter, set
`PRICE_PROMPT`, `PRICE_COMPLETION` and `PRICE_CACHED` to its list
prices per million tokens.

```bash
pip install -e .
harness
```

```powershell
pip install -e .
harness
```

### Expected output

```text
> add a subtract function to calc.py

  ╭──────────────────────────────────────────────────────────────╮
  │ str_replace {"path": "calc.py", "old_str": ..., "new_str": ...} │
  │ ──────────────────────────────────────────────────────────── │
  │ Replaced 1 match(es) in calc.py                              │
  ╰──────────────────────────────────────────────────────────────╯

  1,204 prompt (estimate 1,180) · 96 completion · $0.0016

  Stop blocked: tests were not run after editing calc.py; run pytest, then answer

  ╭──────────────────────────────────────────────────────────────╮
  │ bash pytest -q                                               │
  │ ──────────────────────────────────────────────────────────── │
  │ 3 passed in 0.12s                                            │
  ╰──────────────────────────────────────────────────────────────╯

  ╭──────────────────────────────────────────────────────────────╮
  │ finish Added subtract(a, b) to calc.py; 3 tests pass.        │
  │ ──────────────────────────────────────────────────────────── │
  │ Added subtract(a, b) to calc.py; 3 tests pass.               │
  ╰──────────────────────────────────────────────────────────────╯

  1,530 prompt (estimate 1,502) · 61 completion · $0.0018

  finish: the turn ends here
```

The agent writes the function and answers. Before the answer shows, the
Stop hook runs and blocks it: a muted line reads `Stop blocked: ...`,
and the spinner comes back. The next reply runs pytest, and the one
after it answers, or calls `finish` with a summary. Either way the hook
now lets the turn end. Every usage line carries the call's cost, and
the summary table at exit has a `cost` row.

Type `/cost`. With one of the `gpt-4.1` models:

```text
session cost $0.0123 of MAX_SESSION_COST=$5.00 (list prices); MAX_TURN_CALLS=40; MAX_TURN_SECONDS=900; Stop hook blocks this turn: 1
```

With the default model and no `PRICE_*` variables:

```text
session cost $0.0412 of MAX_SESSION_COST=$5.00 (fallback prices, set PRICE_PROMPT, PRICE_COMPLETION and PRICE_CACHED); MAX_TURN_CALLS=40; MAX_TURN_SECONDS=900; Stop hook blocks this turn: 0
```

Trip a budget on purpose. Start with `MAX_SESSION_COST=0.01 harness`
and ask for something that takes a few calls. After the call that
crosses a cent, the loop prints `stopped: this session has cost
$0.0112, over MAX_SESSION_COST=$0.01; raise it in the environment and
start again` and the prompt returns. `MAX_TURN_SECONDS=20` does the
same for a slow turn, with `say continue to go on`, because that cap
is per turn.

Headless, the summary is the answer:

```bash
harness -p "create hello.txt with the word hello, then finish"
```

prints the summary the model gave to `finish`, not the empty text of
the reply that carried it.

Run the offline tests from the repository root:

```bash
python run_tests.py 41
python check_snippets.py 41
```

```powershell
python run_tests.py 41
python check_snippets.py 41
```

## Error handling

- **A bad tool call.** As in step 39: malformed arguments, an unknown
  tool, a missing argument and a tool that raises each become one
  `Error:` tool message. `finish` with no summary records `(finished
  without a summary)` and still ends the turn.
- **A failing command.** Its output is the result; over 60 s it is
  killed with its tree and the result starts `Timed out after 60s and
  was killed. Output so far:`. The turn clock keeps running through it.
- **Ctrl-C.** The steer prompt; a second ctrl-c leaves. The turn clock
  and the block count are per turn, so a steered turn keeps them.
- **A dead model call.** After the retries the turn ends with a note;
  nothing is charged for a call that returned no usage.
- **A tripped budget.** A note, and the prompt is back. The call cap
  and the clock reset with the next message; the cost cap does not:
  every later message gets the same note and is not added to the
  transcript.
- **A bad number in the environment.** `MAX_SESSION_COST=abc` prints
  `MAX_SESSION_COST='abc' is not a number; using 5.0` on stderr at start
  and goes on with the default.
- **Leaving.** `/exit`, `/quit`, ctrl-d, or ctrl-z then enter on
  Windows.

## Gotchas / What this is not

- The cost is an estimate on every host but OpenRouter, and the
  default model is priced with the fallback table until `PRICE_*` is
  set. `/cost` names the source.
- The caps are checked before a model call, never after or during. A
  turn can run `MAX_TURN_SECONDS` plus one whole tool batch: a 60 s
  `bash`, a `job_wait` up to its own timeout, or a subagent's turns
  (the subagent checks the session cost and the turn clock before each
  of its own calls, but a running tool is never cut short).
- `MAX_SESSION_COST` is per session. In `eval` every task starts at
  zero and its spend is in the report (`Result.cost`); a chat keeps
  the total until it exits.
- `finish` runs through the permissions and the hooks like any call. A
  PreToolUse hook or a session `never` on `finish` means the turn
  cannot end that way; the model has to answer with text, and `-p`
  prints that text, not the denied summary.
- `require_tests.py` matches the substring `pytest` in a bash command.
  It is an example of the shape, not a test gate.
- After `MAX_STOP_BLOCKS` blocks the hooks lose: the turn ends with a
  note and whatever answer the model gave.

## What to notice

- `finish` is a tool, not a special case in the loop. It runs through
  the permissions, the hooks and the executor like any other call, and
  the loop learns about it from one global after the results are in.
  A reply can carry the last edit and the end together.
- The budgets are checked before a call, never after. The call that
  would cross a line is the one that is not made, so a tripped budget
  never leaves a call without its results.
- Cost is one number per call, from one function. OpenRouter's own
  figure wins when it is there; the price table is the fallback, and
  its source is named in `/cost`, so an estimate is never mistaken for
  a bill.
- A subagent spends the parent's budget. `record` runs in the subagent
  loop and in the compaction call too, because those are the calls a
  user does not see one by one.
- The Stop hook reads the turn, not the world. The event carries every
  call with its input and result, so a hook can answer "did pytest run
  after the last edit" without touching the transcript on disk.
- A block is a user message. The agent reads it the way it reads any
  instruction, and `--resume` after a crash finds it in the log.
- The refusals are capped. `MAX_STOP_BLOCKS` keeps a hook that is never
  satisfied from running the agent to `MAX_TURN_CALLS`, and the note
  says the hook lost.
- Step 34's repeat detector still applies. A model that answers a block
  by calling `finish` again with the same summary gets `Repeated call
  detected` on the third try, and the turn goes on until it changes
  something.

## Diff from step 40

```bash
diff -r ../step_40_handoffs/harness harness
```

Added: `stop.py` (`MAX_TURN_CALLS`, `MAX_SESSION_COST`,
`MAX_TURN_SECONDS`, `MAX_STOP_BLOCKS`, `PRICES`, `FALLBACK_PRICES`,
`SPENT`, `FINISH_SCHEMA`, `finish`, `finish_summary`, `begin_turn`,
`finished`, `elapsed`, `prices`, `cost_of`, `record`, `tripped`,
`status`, `turn_calls`, `may_stop`, `send_back`, `reset`),
`.agents/require_tests.py`. Changed: `agent.py` (`MAX_CALLS` removed;
`stop.tripped(0)` before the user message, `stop.begin_turn`,
`stop.tripped`, the finish schema in the offered tools, `stop.record`
on the usage line, `may_stop` and `send_back` on both ends,
`last_reply` reads a finish summary that ran), `hooks.py` (`Stop` in
`EVENTS`, four keys in `EVENT_KEYS`), `tools.py` (`finish` in `TOOLS`),
`subagent.py` (`finish` in `WITHHELD`, `stop.tripped(0)` and
`stop.record` in the loop), `compact.py` (`stop.record` after the
summariser call), `plan.py` (`offered` lets `finish` run in plan mode),
`ui.py` (`usage(cost=)`; the summary's `cost` row is from step 30),
`evaluate.py` (`stop.SPENT` saved, zeroed and restored per task; the
usage recorder adds `cost`), `commands.py` (`/cost`),
`.agents/hooks.json` (the `Stop` entry). Everything else, `capstone/`
included, is unchanged from step 40.

## What the next step adds

Step 42 streams a command's output: the lines of a `bash` call, a
background job and a subagent run reach a live panel as they arrive,
and a timed-out command hands the model what it printed.
