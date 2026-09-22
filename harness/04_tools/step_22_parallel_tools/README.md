# Step 22 - Parallel tool calls

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 21 - Streaming and headless mode](../step_21_streaming_headless/README.md). Next: [Step 23 - Browser use](../step_23_browser_use/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** when the model puts several tool calls in one
reply, the harness runs them at the same time. The permission questions
still come one at a time, in order, before anything runs. The results
come back in the order the model asked for them. The subagent gets the
same behaviour, because it uses the same code. A reply that holds a
`task` call runs the old way, one call after another, because a subagent
may need to ask the user itself.

## Why run tool calls together, and what breaks without it

A model that has learned to batch its work sends replies like this: read
`agent.py`, read `tools.py`, read `ui.py`. Three tool calls, one reply.
Up to step 21 the loop ran them one after another. Each `read_file` is
fast, but a `bash` call that runs the test suite is not, and three
`grep`s over a big tree add up. Three of those in a row is three times
the wait for no reason: the calls do not depend on each other, or the
model would have sent them in separate replies. A turn that reads ten
files to answer one question spends most of its wall-clock time waiting
on the disk, serially.

The obvious fix has a catch. Some calls need a yes from the user first.
If four threads each ask a question at once, the prompts land on top of
each other and the answers go to the wrong call. So the work splits in
two. First the harness looks at every call, in order, on the main thread,
and asks whatever it needs to ask. Then the calls that may run go to a
thread pool. Denied calls never enter the pool; their result is the
denial message. When the pool finishes, the results line up in the
original order and the loop appends them as it always did.

`execute()` used to do both halves in one function. This step splits it
into `decide()` and `run()`, and keeps `execute()` as the sum of the two
for a single call.

## The code, piece by piece

### 1. Decide, without running

`harness/tools.py`:

```python
def decide(tool_call, allowed=None):
    """Parse the arguments and rate the call. Returns (args, action, reason).

    Nothing runs here. This is the half of execute() that must stay on the
    main thread, because an `ask` verdict turns into a prompt. A fourth
    verdict, `error`, carries the message for a call that cannot be used:
    arguments that are not a JSON object, or a name not in the table.
    """
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:  # the model wrote broken JSON
        return {}, "error", f"Error: the arguments of {name} are not a JSON object: {e}"
    if allowed is not None and name not in allowed:  # offered set == executable set
        return args, "deny", f"{name} is not available to this agent"
    if name not in TOOLS:  # a name that is not in the table
        return args, "error", f"Error: no tool named {name!r}."
    action, reason = check(name, args)
    return args, action, reason
```

`decide()` is the first half of the old `execute()`: parse the JSON
arguments, then ask `permissions.check` for a verdict. It returns the
parsed arguments too, so nothing parses them twice. It never touches a
tool, and it never prompts. It is cheap and safe to call for every tool
call in a reply before any of them runs.

There are four verdicts, not three. `error` is for a call that cannot be
used at all - arguments that are not JSON, or not an object, or a tool
name the table does not know - and it carries the message the model will
get as the result. Without it, one broken call
in a batch of four would raise before any of the four had a result, and
the transcript would be left with an assistant message the API refuses to
see again. `allowed` is the set of tool names the caller offered; a
subagent that names a tool it was not given gets a `deny`.

### 2. Run, without deciding

`harness/tools.py`:

```python
def run(tool_call, args):
    """Run the tool with already-parsed arguments. No permission check here."""
    name = tool_call.function.name
    if name not in TOOLS:  # decide() refuses these first; run() alone must not raise either
        return f"Error: no tool named {name!r}."
    try:
        result = TOOLS[name](**args)  # name -> function, JSON -> kwargs
    except Exception as e:  # wrong arguments, missing file, anything the tool raises
        return f"Error: {type(e).__name__}: {e}"
    if not isinstance(result, str):  # a tool message must be text
        result = "(no output)" if result is None else json.dumps(result, default=str)
    return result
```

`run()` is the second half. It takes the arguments `decide()` produced
and calls the tool. There is no permission check inside, on purpose. The
check belongs to the thread that can talk to the user, and `run()` is the
function that goes to the worker threads.

`run()` never raises either. An unknown tool name, a missing required
argument (`TypeError`), a file that is not there - each becomes an
`Error: ...` string. That matters more here than in step 21: an
exception inside one worker would surface from `future.result()` and
abort the loop that collects the others, losing results that had already
finished.

### 3. Turning a verdict into a result

`harness/tools.py`:

```python
def settle(action, reason):
    """Turn a verdict into a result string, or None when the call may run.

    A `deny` never runs. An `ask` prompts the user and runs only on yes. An
    `error` is already its own result.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if action == "error":
        return reason
    if action == "deny":
        return f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return DENIED
    return None
```

`settle()` holds the prompt. It maps a verdict to one of four outcomes:
the error message itself, a policy block, a user denial, or `None`, which
means the call may run. The message strings are the same ones step 15
produced, so the model sees no difference.

### 4. The direct path

`harness/tools.py`:

```python
def execute(tool_call, allowed=None):
    """Turn one tool call into (args, result). Never raises: whatever goes
    wrong becomes the result string, so the model reads it and tries again.

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. `allowed` is the
    set of tool names the caller offered; a call outside it is denied. This
    is decide, settle and run in one step, for callers that want the direct path.
    """
    args, action, reason = decide(tool_call, allowed)
    result = settle(action, reason)
    if result is not None:
        return args, result
    return args, run(tool_call, args)
```

`execute()` keeps its signature and its behaviour. It is now three lines
of glue over the pieces above. A single tool call still goes through it,
on the calling thread, with no pool.

### 5. Many calls at once

`harness/tools.py`:

```python
MAX_WORKERS = 4  # tool calls of one reply that may run at the same time
```

```python
# Tools whose order matters, or that talk to the user themselves: a reply
# that holds one of these runs sequentially, on the calling thread.
SERIAL = {"task"}
```

```python
def execute_all(tool_calls, allowed=None):
    """Run every tool call of one reply. Returns [(args, result)] in the same order.

    One call takes the direct path, and so does a batch that holds a SERIAL
    tool: its order matters, or it asks the user itself, so it cannot share
    a pool. Otherwise the calls are decided first, one at a time on this
    thread, so the prompts appear in order. Then the allowed ones run
    together in a thread pool. A denied or declined call gets its message as
    the result and never runs.
    """
    if len(tool_calls) == 1 or any(c.function.name in SERIAL for c in tool_calls):
        return [execute(tool_call, allowed) for tool_call in tool_calls]

    outcomes = []  # (args, result) per call; result is None until it has run
    for tool_call in tool_calls:
        args, action, reason = decide(tool_call, allowed)
        outcomes.append((args, settle(action, reason)))

    pending = [i for i, (_, result) in enumerate(outcomes) if result is None]
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    try:
        futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
        for i, future in futures.items():
            outcomes[i] = (outcomes[i][0], future.result())
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # do not sit through a 60s command
        raise
    pool.shutdown(wait=True)
    return outcomes
```

`execute_all()` is the new entry point for a whole reply. The first
branch keeps the single call on the direct path, and sends a batch that
contains a `SERIAL` tool down the same path, one call after another. For
everything else, the first loop runs on the main thread: decide, settle,
record. After it, `outcomes` holds a result for every denied, declined
or broken call and `None` for every call that may run. The prompts
appeared one at a time, in the model's order, because this loop is
sequential.

The pool takes only the `None` entries. `pool.submit` returns a future
per call, keyed by its position. The second loop waits on each future and
writes its result into that position. Position, not completion time,
decides the order, so `outcomes` comes back in the model's order even
when the third call finishes first. `shutdown(wait=True)` does not return
until every worker is done.

The pool is not a `with` block, because of ctrl-c. `ThreadPoolExecutor`'s
`__exit__` waits for every running future, which means a ctrl-c during a
60-second `bash` call would be delayed by up to 60 seconds. Instead, the
interrupt cancels the queued calls and re-raises at once; the running
ones finish in the background, and `turn()` answers every call that has
no result with `(interrupted before this tool ran)`.

`MAX_WORKERS = 4` caps the pool. A reply with six calls runs four, then
the last two as workers free up. Results still land in order.

Why is `task` serial? A subagent runs its own loop, with its own
`execute_all` and its own `ui.approve`. Run two of them on two pool
threads and both can ask the user at the same moment, racing for the one
keyboard. On the calling thread they ask one at a time, like everything
else. The set grows in later steps: step 23 adds `browse` and the
browser tools, step 24 the computer tools.

### 6. The loops

`harness/agent.py`:

```python
            # decide every call first, run the allowed ones together, then report in order
            outcomes = execute_all(message.tool_calls)
            for tool_call, (args, result) in zip(message.tool_calls, outcomes):
                ui.tool(tool_call.function.name, args, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
                session.save(messages)  # after every message, so a crash loses nothing
```

`harness/subagent.py`:

```python
        # the same executor as the main loop: same permissions, same sandbox, same pool
        outcomes = execute_all(message.tool_calls, allowed)
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

Both loops change in the same way. One call to `execute_all()` replaces
the per-call `execute()`. Then a loop over the reply's calls and their
outcomes, zipped, prints a panel and appends a tool message for each.
The panels print after every call has finished, because `execute_all()`
returns only then. While the pool runs, the screen is quiet. The
subagent passes `allowed`, the names of the schemas it was offered, so
it cannot run `write_file` or `task` by naming them.

### 7. One prompt at a time, one spinner at a time

`harness/ui.py`:

```python
APPROVE_LOCK = threading.Lock()  # one approval question at a time, whichever thread asks
```

```python
class Idle:
    """A spinner that does nothing: used off the main thread, where rich cannot draw one."""
```

Two small guards in `ui.py` for code that now runs on worker threads.
`approve()` takes `APPROVE_LOCK`, so even if two threads do ask, the
questions come one after the other rather than interleaved. And
`working()` returns an `Idle` spinner off the main thread: `rich`
allows one live display at a time, and a second one from a worker would
raise `LiveError` and take the turn down.

### 8. Telling the model

`harness/llm.py`:

```python
When several tool calls do not depend on each other - reading three files,
running two greps - put them all in one reply. They run at the same time and
the results come back together, in order. A call that needs the result of
another one goes in the next reply.
```

The harness can run calls together only if the model sends them together.
The system prompt says so, and says when not to: a call that reads the
output of another must wait for the next reply.

## Run it

Bash:

```bash
pip install -e .
harness
```

PowerShell:

```powershell
pip install -e .
harness
```

Then:

```text
> read agent.py, tools.py and subagent.py, then tell me how a tool call flows
```

The model answers with three `read_file` calls in one reply. The spinner
runs while the pool reads all three, then three tool panels print at
once, in the order the model asked, then the reply streams in. Try a
reply that mixes verdicts:

```text
> run `python -c "print(1)"` and `python -c "print(2)"` and also list the directory
```

Two prompts appear, one after the other, before anything runs. Answer
`y` to the first and `n` to the second. Then the panels print: the first
command's output, the denial message, and the directory listing.

Run the offline tests from the repository root:

```bash
python run_tests.py 22
```

The test with three slow calls asserts that three 0.3 second tools finish
in under 0.7 seconds. It fails if the calls run one after another.

### Expected output

```text
> run `python -c "print(1)"` and `python -c "print(2)"` and also list the directory

  run: python -c "print(1)"
  allow? (y/n)> y

  run: python -c "print(2)"
  allow? (y/n)> n

  ┌──────────────────────────────────────────────┐
  │ bash {"command": "python -c \"print(1)\""}   │
  │ ──────────────────────────────────────────── │
  │ 1                                            │
  └──────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────┐
  │ bash {"command": "python -c \"print(2)\""}   │
  │ ──────────────────────────────────────────── │
  │ The user denied this tool call.              │
  └──────────────────────────────────────────────┘
  ┌──────────────────────────────────────────────┐
  │ bash {"command": "ls"}                       │
  │ ──────────────────────────────────────────── │
  │ README.md                                    │
  │ harness                                      │
  │ ...                                          │
  └──────────────────────────────────────────────┘

  agent

  The first command printed 1. You declined the second. The directory holds ...
```

## Error handling

- **A bad call in a batch.** `decide()` rates it `error` and its message
  (`Error: the arguments of bash are not a JSON object: ...`) is its
  result; the other calls in the batch still run. An unknown tool
  (`Error: no tool named 'nope'.`) and an exception inside a tool
  (`Error: FileNotFoundError: ...`) come out of `run()` the same way.
  Every call in the reply gets exactly one tool message.
- **A failing command.** As in step 21: the output, or `Timed out after
  60s and was killed. Output so far: ...`. A timeout in one worker does
  not affect the others.
- **A dead model call** ends the turn with `model call failed: ...`; the
  user message stays and the next turn retries. In print mode the exit
  code is 1.
- **ctrl-c during a batch.** Queued calls are cancelled, the running ones
  are abandoned, every call without a result gets `(interrupted before
  this tool ran)`, and the prompt comes back at once - not after the
  slowest worker.
- **Leaving.** `/exit` or `/quit`, ctrl-d, or on Windows ctrl-z then
  enter. An empty line does nothing.

## Gotchas / What this is not

- **Workers can still prompt - through a subagent.** That is why `task`
  is `SERIAL`. `run()` itself never asks, but `task` starts a whole loop
  that does. A batch with a `task` in it runs one call at a time on the
  calling thread, so the prompts stay in order; it does not run in
  parallel.
- **Stateful tools race.** Two `write_todos` in one reply: last writer
  wins. Two `write_file` or `str_replace` on the same path: undefined.
  The harness does not detect this; the prompt tells the model to put
  dependent calls in separate replies, and the harness trusts it.
- **The screen is quiet while the pool runs.** Panels print when the
  whole batch is done. A batch with one slow call looks like one slow
  call.
- **Nested spinners.** A subagent on a worker thread gets an `Idle`
  spinner, so there is no visible progress for it. `rich>=14` can nest
  live displays; the code does not rely on that.
- **`bash` is `cmd.exe` on Windows, with no sandbox**, as in every step
  since 12. Four of them at once are four `cmd.exe` processes.
- **Not a scheduler.** Four workers, one reply, no queue across replies,
  no priorities. Step 29 adds parallel subagents with their own tags.

## What to notice

- Two halves, two threads. `decide()` and `settle()` run on the main
  thread, where the prompt lives. `run()` goes to the pool and never
  prompts. The one tool that can, `task`, is kept off the pool.
- Denied calls cost nothing. They never enter the pool. Their result is
  the same string step 15 returned, in the same position.
- Order is by position, not by finish time. The futures are keyed by
  index and read back by index. The model sees its results in the order
  it sent the calls, whatever the pool did.
- The single call path is unchanged. One tool call still goes through
  `execute()`, on the calling thread, with no pool. Most replies have one
  call, so most replies pay nothing for this step.
- Errors are values. The fourth verdict and the try/except in `run()`
  exist because a worker that raises loses its siblings' results. Once
  every failure is a string, `future.result()` cannot raise for a tool
  problem, and the collecting loop is straight-line code.

## Files

```text
step_22_parallel_tools/
├── harness/
│   ├── tools.py       execute() splits into decide() and run(); execute_all() uses a pool; SERIAL
│   ├── agent.py       one reply's tool calls go to execute_all(); results back in order
│   ├── subagent.py    exploration subagents, now on the parallel tool path
│   ├── llm.py         streams; the system prompt says independent calls run together
│   ├── ui.py          streaming panels and headless() from step 21; APPROVE_LOCK, Idle
│   ├── commands.py    slash commands: /rewind /sessions /compact /exit
│   ├── compact.py     the compaction agent from stage 14
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py     the late injection block, unchanged since stage 10
│   ├── history.py     keeps the transcript small: caps, strips and drops old tool output
│   ├── permissions.py allow / ask / deny rules; which tool calls need a human
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash; one profile file per call on macOS
│   ├── session.py     append-only JSONL session log; load() repairs a cut-off turn
│   ├── skills.py      skills, unchanged since stage 9
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests: ordering, decisions on one thread, the pool, SERIAL
├── pyproject.toml     package metadata; version 0.22.0
└── README.md          this file
```

## Diff from step 21

```bash
diff -r ../step_21_streaming_headless/harness harness
```

Changed: `tools.py` (`decide`, `run`, `settle`, `execute_all`,
`MAX_WORKERS`, `SERIAL`, `execute` rebuilt on them), `agent.py` and
`subagent.py` (one `execute_all` call, then a loop over the outcomes),
`llm.py` (a paragraph in the system prompt), `ui.py` (`APPROVE_LOCK`,
`Idle`, the thread check in `working`). Everything else is unchanged
from step 21.

## What the next step adds

Step 23 gives the harness a browser: a `browse` subagent with its own
tools, on one browser thread, and a `browser_open` permission rule keyed
by host.
