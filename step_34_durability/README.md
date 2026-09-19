# Step 34 - Durability and recovery

**What this step adds:** three guards against the ways a long session
dies. A model call that hits a rate limit, a dropped connection, a
timeout, a 5xx answer or an error event inside the stream is retried with
exponential backoff, five tries in all, and gives up with a message
instead of a traceback; the SDK's own silent retries are switched off so
those five are the whole policy. A tool call repeated three times in a
row with the same arguments is answered with a warning instead of being
run again. On `--resume` and on `/sessions`, a transcript that ends in
tool calls without results, the mark of a crash mid-turn, is finished:
the calls run, the results are saved, and the UI says how many were
recovered. The per-turn cap `MAX_CALLS = 40` is carried from step 31.

## Files

```text
step_34_durability/
├── harness/
│   ├── llm.py                        the model call; retries with backoff, returns failed, never raises
│   ├── tools.py                      the registry; deferred tools, load_tool(), active_schemas()
│   ├── agent.py                      the loop; MAX_CALLS, the loop detector, recover() on --resume
│   ├── durability.py                 LoopDetector and unanswered(): repeats and crash leftovers
│   ├── checkpoint.py                 workspace checkpoints: capture before a write, undo a turn
│   ├── hooks.py                      hooks; BUILTIN holds the checkpoint capture on PreToolUse
│   ├── commands.py                   slash commands; /undo, /rewind restores files, /checkpoints
│   ├── evaluate.py                   the eval harness; isolated() clears the run's checkpoints
│   ├── budget.py                     the context budget: breakdown(), render(), check()
│   ├── plan.py                       plan mode; load_tool joins the read-only tools
│   ├── instructions.py               finds AGENTS.md / CLAUDE.md from home and git root down
│   ├── jobs.py                       background jobs: Popen through the sandbox, a job table, kill_all
│   ├── subagent.py                   the subagent loop; task runs one subagent per description
│   ├── permissions.py                allow / ask / deny; a job is rated by the bash rules
│   ├── context.py                    the late injection block, with a <jobs> tag
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
│   ├── ui.py                         rich panels; usage() shows the estimate, context() the breakdown
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
├── AGENTS.md                         the project instruction file the harness reads at start
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.34.0
└── README.md                         this file
```

## Why the loop must not trust the network, the model or itself

An agent loop runs for minutes and makes dozens of requests. Over that
time the network hiccups, the provider sheds load, and a proxy times out.
Up to step 33 any of those raised an exception out of `call_llm`; the
loop caught it, printed `model call failed: ...` and ended the turn. The
session survived, but the user had to type `try again` for every blip,
and a blip in the middle of a forty-call turn threw away the turn.

The model is not reliable either. It can get stuck: the same `grep` with
the same pattern, reply after reply, because the result did not contain
what it hoped for and it has no better idea. Without a limit, a stuck
model burns the whole context window and the user's money before it
stops. A per-turn cap and a repeat detector make the failure short and
visible.

The last guard is for the crash that happens anyway: a power cut, a kill,
a bug in a tool. Step 8 saves after every message, so the transcript on
disk ends exactly where the loop was. When that place is between a model
reply with tool calls and the results of those calls, the transcript
cannot be sent back to the API, which wants a result for every call.
Recovery runs the missing calls, through the same permissions and hooks
as always, so the resumed session starts from a valid state.

### What breaks without it

Ask for a refactor that takes thirty tool calls. On call nineteen the
provider answers 502 for two seconds. Without the retry the turn ends
with a note and the model's half-finished plan; `try again` starts the
reasoning over from the transcript, which now holds eighteen results the
model has to re-read. With the retry the note says `retry 1 of 4 in
0.5s`, the same request goes out again, and the turn continues where it
was. Without the detector, a model that greps for a name that is not
there tries the same grep forty times, one per call, and the cap ends the
turn ten minutes and a few dollars later; with it, the third identical
call gets a sentence instead of a result, and the model changes approach
on call four.

## The code, piece by piece

### 1. What is worth a retry

`harness/llm.py`:

```python
client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY, max_retries=0)  # the retry policy is ours, below
MODEL = config.MODEL

BACKOFF = (0.5, 1.0, 2.0, 4.0)  # seconds to wait before retry 1, 2, 3 and 4
MAX_TRIES = len(BACKOFF) + 1    # the first try plus one per wait
sleep = time.sleep              # a name the tests can replace
...
TRANSIENT_CODES = {408, 409, 429, 500, 502, 503, 504, 529}  # from an error event inside a stream


def retryable(error):
    ...
    if isinstance(error, openai.RateLimitError):
        return True
    if isinstance(error, openai.APIConnectionError):  # APITimeoutError is a subclass
        return True
    if isinstance(error, openai.APIStatusError):
        return error.status_code >= 500
    if isinstance(error, httpx_lib.HTTPError):  # the SDK wraps the request, not the read of the stream
        return True
    if isinstance(error, openai.APIError):
        body = error.body if isinstance(error.body, dict) else {}
        code = body.get("code") or body.get("status")
        text = f"{body.get('message', '')} {error}".lower()
        return code in TRANSIENT_CODES or "overloaded" in text or "rate limit" in text
    return False
```

The line is drawn by who is at fault. A 429, a dropped connection, a
timeout and a 5xx are the provider's or the network's problem, and the
same request may well succeed a second later. A 4xx is the request's
problem: a bad key, a context too long, a malformed tool schema. Sending
it again gives the same answer, so it is never retried. The waits double
from half a second, so five tries span about eight seconds of waiting.

Two cases are easy to miss. The SDK wraps the *request* in its own error
classes, but once `create()` has returned, reading the stream is raw
`httpx` (`httpx2` in openai 3.x, which vendors it), and a connection that
drops mid-reply raises `RemoteProtocolError` or `ReadError`, not an
`APIError`. Those are retried. And a provider that fails *after* HTTP 200,
which is how OpenRouter reports an upstream outage, sends an error event
inside the stream; the SDK raises it as a bare `APIError` with the body,
and the body's code or wording decides.

`max_retries=0` on the client matters as much as the list. The SDK's
default is two silent retries with its own backoff on connection errors
and on 408, 409, 429 and 5xx, inside every one of the harness's tries:
five noted tries would really be up to fifteen requests and tens of
seconds of unexplained waiting. With it off, the notes on screen are the
whole story.

### 2. The whole stream inside the retry

`harness/llm.py`:

```python
def stream_once(request, on_delta=None):
    """One request, its stream read to the end. Returns (message, usage).

    A failure anywhere in here, from the first byte to the last, raises,
    and call_llm decides whether to try again.
    """
    stream = client.chat.completions.create(**request)
    ...
    for chunk in stream:
        ...
    message = StreamedMessage(
        content="".join(parts) or None,
        tool_calls=[calls[key] for key in sorted(calls, key=str)] or None,
    )
    return message, usage_from(final_usage)
```

```python
    for attempt in range(1, MAX_TRIES + 1):
        seen = []  # what this try streamed, so a retry can say it starts over

        def deltas(text):
            seen.append(text)
            if on_delta:
                on_delta(text)

        try:
            return stream_once(request, deltas)
        except (openai.APIError, httpx_lib.HTTPError) as error:
            if not retryable(error):
                reason = f"model call failed and will not be retried ({describe(error)}): {error}"
                break
            if attempt == MAX_TRIES:
                reason = f"model call failed {MAX_TRIES} times, giving up ({describe(error)}): {error}"
                break
            wait = BACKOFF[attempt - 1]
            ui.note(f"model call failed ({describe(error)}); retry {attempt} of {MAX_TRIES - 1} in {wait:g}s")
            if seen and on_restart:
                on_restart()  # the partial reply on screen is not the reply
            sleep(wait)

    return StreamedMessage(content=None, failed=reason), usage_from(None)
```

The request and the read of its stream are one function, and the retry
wraps that function. A streamed reply can break after the first chunk as
easily as before it, and a half-assembled message is worth nothing. So a
broken stream starts the reply over. The deltas of the broken attempt
were already shown; `on_restart` lets the caller say so, and the loop
prints `that reply broke off and is discarded; the retry starts it over`
before the fresh text begins.

When the tries run out, `call_llm` does not raise. It returns a message
with the new `failed` field set and everything else empty. That field is
not part of `model_dump`, so a failed message can never enter a
transcript.

### 3. The loop shows the failure and goes on

`harness/agent.py`:

```python
    usage = {}
    detector = durability.LoopDetector()

    try:
        for _ in range(MAX_CALLS):
            ...
            with spinner:
                message, usage = call_llm(with_mode(messages) + [injection], tools=schemas, on_delta=on_delta, on_restart=on_restart)

            if getattr(message, "failed", None):
                # every retry failed: the user message stays, nothing dangles, so 'try again' works
                if streamed:
                    ui.stream_end()  # a stream that broke may have shown part of a reply
                ui.note(message.failed)
                break
            ...
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
```

A failed call ends the turn. The user message stays in the transcript
(it was saved the moment it was appended), so the user can say "try
again" and the model sees what was asked; the next turn simply adds a
second user message after it. The `try/except openai.APIError` of the
earlier steps is gone from the loop: nothing raises out of `call_llm` any
more. The `for` runs at most `MAX_CALLS` times, and its `else` says so
when the cap is reached; the results of the last call are saved before
the loop stops, so the transcript ends in tool results, which is a valid
place to continue from.

`harness/compact.py`:

```python
    if getattr(message, "failed", None) or not message.content:
        # never fold an empty note into the prompt: the caller keeps the transcript as it is
        raise RuntimeError(getattr(message, "failed", None) or "the summariser returned nothing")
    return message.content
```

Every other caller of `call_llm` reads `failed` too, each in the way that
suits it. The subagent returns `(the subagent stopped: ...)` as its
report, so the main agent reads what happened. The compaction agent
raises, so `commands.compact` keeps the transcript as it is and says
`compaction failed`; a transcript replaced by a summary that says nothing
would be the one failure worse than a crash. The eval judge raises too,
and `run_task` records `run failed: ...` instead of scoring the task as a
model FAIL.

### 4. The repeat detector

`harness/durability.py`:

```python
REPEAT_LIMIT = 3
REPEATED = "Repeated call detected; change approach or ask the user"

# calls that look the same on purpose: polling a job, taking another look at the screen or the page
OBSERVE = {"job_status", "job_wait", "computer_screenshot", "browser_read", "browser_screenshot"}
...
def signature(tool_call):
    """What makes two calls the same: the name and the canonical JSON of the arguments."""
    return (tool_call.function.name, json.dumps(parse_args(tool_call), sort_keys=True))


class LoopDetector:
    """Counts how many replies in a row have carried each (name, arguments) pair."""

    def __init__(self, limit=REPEAT_LIMIT):
        self.limit = limit
        self.streaks = {}  # signature -> replies in a row that carried it

    def observe(self, tool_calls):
        """Record one reply. Returns one flag per call: True when it has repeated `limit` times."""
        keys = [signature(call) for call in tool_calls]
        self.streaks = {key: self.streaks.get(key, 0) + 1 for key in set(keys)}  # a pair not in this reply starts over
        return [self.streaks[key] >= self.limit and key[0] not in OBSERVE for key in keys]
```

The signature is the tool name plus the arguments as canonical JSON, keys
sorted, so two calls that differ only in key order count as the same
call. The detector keeps one streak per signature and rebuilds the table
on every reply, so a signature missing from a reply drops to zero. A
reply with several calls advances each of them: `[grep, cat]` followed
by `[grep, ls]` followed by `[grep]` flags the third `grep`. The
`OBSERVE` tools are exempt: `job_status` on the same job three replies
running, or a screenshot while a dialog is expected, is polling, not a
loop.

`harness/agent.py`:

```python
            repeated = detector.observe(message.tool_calls)
            for tool_call, flag in zip(message.tool_calls, repeated):
                if flag:
                    ui.note(f"repeated call detected: {tool_call.function.name} with the same arguments {durability.REPEAT_LIMIT} times in a row")
            run_results(messages, message.tool_calls, repeated)
...
    repeated = repeated or [False] * len(tool_calls)
    fresh = [call for call, flag in zip(tool_calls, repeated) if not flag]
    ran = iter(execute_all(fresh) if fresh else [])
    pictures = []  # (tool name, PNG path) for every image a result asked to show
    for tool_call, flag in zip(tool_calls, repeated):
        args, result = (durability.parse_args(tool_call), durability.REPEATED) if flag else next(ran)
```

`run_results` is the tool-running half of the turn, moved out of `turn()`
so that `recover()` below can use it too. A flagged call is not run. Running it a third time would give the same
result and might repeat a side effect. Its result is the fixed sentence,
which the model reads in the next request. The turn goes on: the model
usually changes approach, and if it does not, the call cap ends the turn.

### 5. Finding what a crash left behind

`harness/durability.py`:

```python
def unanswered(messages):
    """The tool calls of the last assistant message that have no result yet.

    Returns [] when the transcript ends in anything but that message and its
    tool results. The calls come back as StreamedToolCall objects, the same
    shape the loop hands to execute_all.
    """
    index = len(messages) - 1
    while index >= 0 and messages[index].get("role") == "tool":
        index -= 1
    if index < 0 or messages[index].get("role") != "assistant":
        return []
    answered = {message.get("tool_call_id") for message in messages[index + 1:]}
    return [
        StreamedToolCall(id=call["id"], function=StreamedFunction(call["function"]["name"], call["function"]["arguments"]))
        for call in messages[index].get("tool_calls") or []
        if call["id"] not in answered
    ]
```

The scan walks back over the tool results at the end of the transcript
to the assistant message that asked for them, then returns the calls
whose id has no result. A crash after one of three results was saved
leaves two to recover, not three. A transcript that ends in a user
message, a text reply or a screenshot has nothing to recover.

### 6. Recovery on resume

`harness/agent.py`:

```python
def recover(messages):
    ...
    pending = durability.unanswered(messages)
    if not pending:
        return 0
    # the edits belong to the turn that crashed, so /undo takes them back with it: its start is
    # the user message before the reply, not where the transcript stands now
    start = max((i for i, m in enumerate(messages) if m.get("role") == "user" and isinstance(m.get("content"), str)), default=len(messages))
    checkpoint.TURN = max(checkpoint.turns(), default=0) or checkpoint.begin_turn(start)
    try:
        run_results(messages, pending)
    except Exception as failed:  # noqa: BLE001 - a recovery that crashes would crash every resume after it
        for call in durability.unanswered(messages):
            messages.append({"role": "tool", "tool_call_id": call.id, "content": f"Error: {type(failed).__name__}: {failed}"})
        session.save(messages)
    count = len(pending)
    ui.note(f"recovered {count} tool call{'s' if count != 1 else ''} left unanswered by the last run")
    return count
```

```python
    if cli.resume:
        messages = resume_last(messages)
        ui.resumed(messages)
        ui.replay(messages)
        recover(messages)  # a crash mid-turn left tool calls without results: run them now
```

`harness/commands.py`:

```python
    from .agent import recover  # here, not at the top: agent imports this module

    opened = session.open_session(saved[choice]["id"])
    redraw(opened, "opened")
    recover(opened)  # a crash mid-turn left tool calls without results: run them now, as --resume does
    return opened
```

The recovered calls go through `run_results`, the same function the turn
uses, so `execute_all` decides each one through the permission rules and
the hooks: a command that asks still asks, a denied one gets the denial
as its result, and the checkpoint hook captures an edit. `session.repair`
of the earlier steps, which gave every hanging call the stand-in result
`(the harness stopped before this tool ran; no result was recorded)`, is
gone: `session.load` returns the transcript as the crash left it, this
step replaces the stand-in with a real result, and `/sessions` recovers
the same way `--resume` does (headless `-p --resume` too), so there is no
way to open a crashed chat that leaves it unsendable.

Two details keep the recovery itself from becoming the thing that
crashes. The checkpoint turn is the last one on disk, the turn that was
running at the crash, so `/undo` takes the recovered edit back together
with the rest of that turn; when there is no turn directory (a session
from before step 33, a cleaned store), a turn is opened whose start is
the user message that began the crashed turn, not the end of the
transcript, so that `/undo` cuts at a turn boundary and leaves no tool
call without a result. And the tools themselves never raise (step 31),
but if anything else in the path does, every call still waiting gets an
`Error:` result and the transcript is saved, so the next `--resume` opens
a complete transcript instead of failing in the same place again.

## Run it

Prerequisites: as step 31. The demos below need a way to break the
network: unplug it, or point `BASE_URL` at a port with nothing behind it.

bash:

```bash
pip install -e .
harness
> what is in this directory
```

PowerShell:

```powershell
pip install -e .
harness
> what is in this directory
```

### Expected output

Pull the network cable, or start with `BASE_URL=http://127.0.0.1:9` (bash)
or `$env:BASE_URL = "http://127.0.0.1:9"` (PowerShell), and ask again.
The notes count the tries; with the SDK's own retries off, each note
follows the failure at once:

```text
> what is in this directory

  model call failed (APIConnectionError); retry 1 of 4 in 0.5s
  model call failed (APIConnectionError); retry 2 of 4 in 1s
  model call failed (APIConnectionError); retry 3 of 4 in 2s
  model call failed (APIConnectionError); retry 4 of 4 in 4s
  model call failed 5 times, giving up (APIConnectionError): Connection error.

>
```

The prompt comes back. Plug the cable in and type `try again`, and the
model answers the question that is still in the transcript.

To see the recovery, ask for something with a tool call and kill the
process between the reply and its result, for example with a `bash`
command that sleeps for a minute:

```text
> run: sleep 60

  run: sleep 60
  allow? (y/n)> y
```

Close the terminal while the command runs. Then:

```bash
harness --resume
```

```text
  resumed · 3 messages · 1 turns
  > run: sleep 60
    run: sleep 60

  run: sleep 60
  allow? (y/n)> y
  recovered 1 tool call left unanswered by the last run
```

The transcript is redrawn, the command asks for approval again as it did
the first time, the sleep runs, and one line reports the recovery. The
same happens when the chat is opened with `/sessions` instead.

Run the offline tests from the repository root:

```bash
python run_tests.py 34
python check_snippets.py 34
```

## Error handling

- **A bad tool call.** As in step 31: `Error: the arguments of ... are not
  a JSON object`, `Error: no tool named 'x'.`, `Error: TypeError: ...`;
  one tool message per call, always.
- **A model call that fails for good.** A note, `model call failed 5
  times, giving up (...)` or `model call failed and will not be retried
  (APIStatusError 400): ...`, and the turn ends. Nothing is appended to
  the transcript for the failed call; the user message stays. A 400 for
  context length is not fixed by `try again`: `/compact` first.
- **A stream that breaks after it started.** The partial text on screen is
  followed by `that reply broke off and is discarded; the retry starts it
  over`, then the fresh reply.
- **A stuck model.** `repeated call detected: bash with the same arguments
  3 times in a row`; the call gets `Repeated call detected; change approach
  or ask the user` as its result and the turn continues.
- **Forty calls in one turn.** `stopped after 40 model calls in one turn;
  say 'continue' to go on`. The transcript is complete at that point.
- **ctrl-c.** During a model call, a backoff wait or a tool run: the turn
  stops, any tool call without a result gets `(interrupted before this
  tool ran)`, the note says `interrupted`, and the prompt comes back. A
  ctrl-c during a threaded batch cancels the calls that have not started;
  the ones in flight finish on their own.
- **A crash mid-turn.** `--resume` and `/sessions` re-run the calls that
  have no result. A tool that fails during the re-run yields an `Error:`
  result; the session is always resumable.
- **`/compact` with a dead model.** `compaction failed (RuntimeError);
  transcript kept as is`. The history is never replaced by an empty note.
- **`harness -p`.** Exit code 1 when no answer came (every retry failed,
  or a 4xx); a script can tell "no answer" from "empty answer".
- **Leaving.** `/exit`, `/quit`, ctrl-d, ctrl-z then enter on Windows, or
  ctrl-c at the prompt.

## Gotchas / What this is not

- **Recovery re-runs, it does not replay.** A crash after `bash "git
  commit"` ran but before its result was saved commits again on resume;
  `bash_background` starts a second job. The recovered calls go through
  the permission rules, so a command the rules rate `ask` asks again and
  can be declined; an `allow`-rated one runs without a question. Check
  `git log` after a recovery that involved a commit.
- **The detector has false positives.** Three replies in a row that each
  carry an edit plus `pytest` flag the `pytest`; the `OBSERVE` exemptions
  cover polling, not every legitimate repeat. The sentence is a result,
  not a block: the model can explain and the user can say "continue".
- **`try again` after a 4xx repeats the 4xx.** A context-length error
  needs `/compact`; a bad key needs a new key. The note names the status
  so the reader can tell.
- **What a failed call leaves.** Nothing in the transcript, but the user
  message is there, so the next turn has two user messages in a row. The
  API accepts that.
- **Backoff is short by design.** About eight seconds in all. A provider
  outage of minutes ends with `giving up`; the session is intact and
  `try again` is one line.
- **Not a job queue.** Nothing is persisted about a retry; a process
  killed during a backoff wait has simply lost that call, and recovery
  on resume covers the tool side only.
- **Windows.** ctrl-c reaches the harness as `KeyboardInterrupt` in the
  same places; `taskkill /T` ends a timed-out command's tree. The tool
  named `bash` still runs through `cmd.exe`, without an OS sandbox.

## What to notice

- **The retry wraps the stream, not just the request.** With streaming,
  the request succeeds the moment the first byte arrives, and the
  failure comes later as an `httpx` error, not an SDK one. A retry around
  `create()` alone, or one that catches `APIError` alone, would miss most
  real failures.
- **Never on a 4xx.** A retry only helps when the next answer can differ.
  A rejected request is rejected again, and four more tries would only
  hide the reason for eight seconds.
- **A failure is a value, not an exception.** `call_llm` returns a
  message with `failed` set. Every caller reads it: the turn ends with a
  note, the subagent reports it, the compaction agent and the eval judge
  raise it so their callers keep what they had.
- **The cap and the detector are per turn.** The detector starts fresh
  with every user message, and so does the counter. A user who says
  "continue" gets another forty calls.
- **The repeated call does not run.** Its result is the warning text.
  This is cheaper than running it, and safe for a tool with side
  effects.
- **Recovery is the ordinary tool path.** `recover` calls the same
  `run_results` the turn calls. Permissions, hooks and checkpoints apply
  because nothing new was written for them.
- **The SDK's retries are off.** `max_retries=0` makes the notes on
  screen the whole policy. Leave it on and every note hides up to two
  silent requests.

## Diff from step 33

```bash
diff -r ../step_33_checkpoints/harness harness
```

Added: `durability.py` (`REPEAT_LIMIT`, `REPEATED`, `OBSERVE`,
`parse_args`, `signature`, `LoopDetector`, `unanswered`). Changed:
`llm.py` (`max_retries=0`, `httpx_lib`, `BACKOFF`, `MAX_TRIES`, `sleep`,
`TRANSIENT_CODES`, `retryable`, `describe`, `stream_once`, `call_llm`
retries with `on_restart` and returns a failed message,
`StreamedMessage.failed`), `agent.py` (`turn` stops on a failed message
and runs the detector, `on_restart`, the tool-running half of `turn`
moved out into `run_results`, which takes `repeated`, `recover`,
`answer_pending` through `durability.unanswered`, `chat` recovers on
`--resume`), `commands.py` (`/sessions` recovers), `compact.py` and
`evaluate.py` (a failed call raises), `subagent.py` (a failed model call
becomes the report), `session.py` (`load` no longer writes stand-in
results; `repair` and `UNANSWERED` are gone, `recover` does that job).
Everything else is unchanged from step 33.

## What the next step adds

Step 35 puts a human in the loop: session-wide permission rules the user
sets at the prompt, and a way to steer the model between tool calls.
