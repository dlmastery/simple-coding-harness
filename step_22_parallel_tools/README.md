# Step 22 - Parallel tool calls

**What this step adds:** when the model puts several tool calls in one
reply, the harness runs them at the same time. The permission questions
still come one at a time, in order, before anything runs. The results
come back in the order the model asked for them. The subagent gets the
same behaviour, because it uses the same code.

## Why run tool calls together

A model that has learned to batch its work sends replies like this: read
`agent.py`, read `tools.py`, read `ui.py`. Three tool calls, one reply.
Up to step 21 the loop ran them one after another. Each `read_file` is
fast, but a `bash` call that runs the test suite is not, and a `task`
subagent takes many seconds. Three of those in a row is three times the
wait for no reason: the calls do not depend on each other, or the model
would have sent them in separate replies.

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
def decide(tool_call):
    """Parse the arguments and rate the call. Returns (args, action, reason).

    Nothing runs here. This is the half of execute() that must stay on the
    main thread, because an `ask` verdict turns into a prompt.
    """
    args = json.loads(tool_call.function.arguments)
    action, reason = check(tool_call.function.name, args)
    return args, action, reason
```

`decide()` is the first half of the old `execute()`: parse the JSON
arguments, then ask `permissions.check` for a verdict. It returns the
parsed arguments too, so nothing parses them twice. It never touches a
tool, and it never prompts. It is cheap and safe to call for every tool
call in a reply before any of them runs.

### 2. Run, without deciding

`harness/tools.py`:

```python
def run(tool_call, args):
    """Run the tool with already-parsed arguments. No permission check here."""
    return TOOLS[tool_call.function.name](**args)
```

`run()` is the second half. It takes the arguments `decide()` produced
and calls the tool. There is no permission check inside, on purpose. The
check belongs to the thread that can talk to the user, and `run()` is the
function that goes to the worker threads.

### 3. Turning a verdict into a result

`harness/tools.py`:

```python
def settle(action, reason):
    """Turn a verdict into a result string, or None when the call may run.

    A `deny` never runs. An `ask` prompts the user and runs only on yes.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if action == "deny":
        return f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return DENIED
    return None
```

`settle()` holds the prompt. It maps a verdict to one of three outcomes:
a policy block, a user denial, or `None`, which means the call may run.
The two message strings are the same ones step 15 produced, so the model
sees no difference.

### 4. The direct path

`harness/tools.py`:

```python
def execute(tool_call):
    """Run one tool call through the permission layer. Returns (args, result).

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. This is decide,
    settle and run in one step, for callers that want the direct path.
    """
    args, action, reason = decide(tool_call)
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
def execute_all(tool_calls):
    """Run every tool call of one reply. Returns [(args, result)] in the same order.

    One call takes the direct path. Several calls are decided first, one at a
    time on this thread, so the prompts appear in order. Then the allowed
    ones run together in a thread pool. A denied or declined call gets its
    message as the result and never runs.
    """
    if len(tool_calls) == 1:
        return [execute(tool_calls[0])]

    outcomes = []  # (args, result) per call; result is None until it has run
    for tool_call in tool_calls:
        args, action, reason = decide(tool_call)
        outcomes.append((args, settle(action, reason)))

    pending = [i for i, (_, result) in enumerate(outcomes) if result is None]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
        for i, future in futures.items():
            outcomes[i] = (outcomes[i][0], future.result())
    return outcomes
```

`execute_all()` is the new entry point for a whole reply. The first
branch keeps the single call on the direct path. For several calls, the
first loop runs on the main thread: decide, settle, record. After it,
`outcomes` holds a result for every denied or declined call and `None`
for every call that may run. The prompts appeared one at a time, in the
model's order, because this loop is sequential.

The pool takes only the `None` entries. `pool.submit` returns a future
per call, keyed by its position. The second loop waits on each future and
writes its result into that position. Position, not completion time,
decides the order, so `outcomes` comes back in the model's order even
when the third call finishes first. The `with` block does not exit until
every worker is done.

`MAX_WORKERS = 4` caps the pool. A reply with six calls runs four, then
the last two as workers free up. Results still land in order.

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
        outcomes = execute_all(message.tool_calls)
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

Both loops change in the same way. One call to `execute_all()` replaces
the per-call `execute()`. Then a loop over the reply's calls and their
outcomes, zipped, prints a panel and appends a tool message for each.
The panels print after every call has finished, because `execute_all()`
returns only then. While the pool runs, the screen is quiet.

### 7. Telling the model

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

```bash
pip install -e .
harness
> read agent.py, tools.py and subagent.py, then tell me how a tool call flows
```

The model answers with three `read_file` calls in one reply. The spinner
runs while the pool reads all three, then three tool panels print at
once, in the order the model asked, then the reply streams in. Try a
reply that mixes verdicts:

```bash
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

## What to notice

- Two halves, two threads. `decide()` and `settle()` run on the main
  thread, where the prompt lives. `run()` goes to the pool. Nothing in
  the pool can ask the user anything, so the prompts cannot collide.
- Denied calls cost nothing. They never enter the pool. Their result is
  the same string step 15 returned, in the same position.
- Order is by position, not by finish time. The futures are keyed by
  index and read back by index. The model sees its results in the order
  it sent the calls, whatever the pool did.
- The single call path is unchanged. One tool call still goes through
  `execute()`, on the calling thread, with no pool. Most replies have one
  call, so most replies pay nothing for this step.
- Tools must be safe to run side by side. `read_file` and `bash` are.
  Two `write_file` calls on the same path would race. The model is told
  to put dependent calls in separate replies, and the harness trusts it.
- A `task` call inside a batch runs its whole subagent on a worker
  thread. Its nested panels and spinner share the screen with the other
  workers. That is acceptable for one subagent and noisy for several. Step
  29 gives parallel subagents their own tagging.

## Diff from step 21

```bash
diff -r ../step_21_streaming_headless/harness harness
```

Changed: `tools.py` (`decide`, `run`, `settle`, `execute_all`,
`MAX_WORKERS`, `execute` rebuilt on them), `agent.py` and `subagent.py`
(one `execute_all` call, then a loop over the outcomes), `llm.py` (a
paragraph in the system prompt). Everything else is unchanged from
step 21.
