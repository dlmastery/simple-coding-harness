# Step 34 - Durability and recovery

**What this step adds:** three guards against the ways a long session
dies. A model call that hits a rate limit, a dropped connection, a
timeout or a 5xx answer is retried with exponential backoff, five tries
in all, and gives up with a message instead of a traceback. A turn stops
after `MAX_CALLS = 40` model calls, and a tool call repeated three times
in a row with the same arguments is answered with a warning instead of
being run again. On `--resume`, a transcript that ends in tool calls
without results, the mark of a crash mid-turn, is finished: the calls
run, the results are saved, and the UI says how many were recovered.

## Why the loop must not trust the network, the model or itself

An agent loop runs for minutes and makes dozens of requests. Over that
time the network hiccups, the provider sheds load, and a proxy times out.
Up to step 33 any of those raised an exception out of `call_llm`, and the
exception went straight through `turn()` and ended the process. The
session file survived, but the user had to notice, restart, and resume.

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

## The code, piece by piece

### 1. What is worth a retry

`harness/llm.py`:

```python
BACKOFF = (0.5, 1.0, 2.0, 4.0)  # seconds to wait before retry 1, 2, 3 and 4
MAX_TRIES = len(BACKOFF) + 1    # the first try plus one per wait
sleep = time.sleep              # a name the tests can replace
...
def retryable(error):
    """True when a failed request may succeed on a retry.

    Rate limits, connection failures and timeouts pass. A status error
    passes only for a 5xx answer: a 4xx is the request's fault and comes
    back the same every time.
    """
    if isinstance(error, openai.RateLimitError):
        return True
    if isinstance(error, openai.APIConnectionError):  # APITimeoutError is a subclass
        return True
    if isinstance(error, openai.APIStatusError):
        return error.status_code >= 500
    return False
```

The line is drawn by who is at fault. A 429, a dropped connection, a
timeout and a 5xx are the provider's or the network's problem, and the
same request may well succeed a second later. A 4xx is the request's
problem: a bad key, a context too long, a malformed tool schema. Sending
it again gives the same answer, so it is never retried. The waits double
from half a second, so five tries span about eight seconds of waiting.

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
        tool_calls=[calls[index] for index in sorted(calls)] or None,
    )
    return message, usage_from(final_usage)
```

```python
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return stream_once(request, on_delta)
        except openai.APIError as error:
            if not retryable(error):
                reason = f"model call failed and will not be retried ({describe(error)}): {error}"
                break
            if attempt == MAX_TRIES:
                reason = f"model call failed {MAX_TRIES} times, giving up ({describe(error)}): {error}"
                break
            wait = BACKOFF[attempt - 1]
            ui.note(f"model call failed ({describe(error)}); retry {attempt} of {MAX_TRIES - 1} in {wait:g}s")
            sleep(wait)

    return StreamedMessage(content=None, failed=reason), usage_from(None)
```

The request and the read of its stream are one function, and the retry
wraps that function. A streamed reply can break after the first chunk as
easily as before it, and a half-assembled message is worth nothing. So a
broken stream starts the reply over: the deltas of the broken attempt
were already shown, and the note tells the user why the text starts
again.

When the tries run out, `call_llm` does not raise. It returns a message
with the new `failed` field set and everything else empty. That field is
not part of `model_dump`, so a failed message can never enter a
transcript.

### 3. The loop shows the failure and goes on

`harness/agent.py`:

```python
MAX_CALLS = 40  # model calls one turn may make before the loop stops and asks
...
    detector = durability.LoopDetector()
    calls = 0  # model calls so far in this turn
    usage = {}

    while True:
        if calls >= MAX_CALLS:
            ui.note(f"stopped after {calls} model calls in one turn; say continue to go on")
            break
        ...
        calls += 1

        if getattr(message, "failed", None):
            if streamed:
                ui.stream_end()  # a stream that broke may have shown part of a reply
            ui.note(message.failed)  # the model never answered; nothing goes in the transcript
            break
```

A failed call ends the turn. The user message stays in the transcript,
so the user can say "try again" and the model sees what was asked. The
call counter is checked before each call, so a turn makes at most
`MAX_CALLS` calls, and the results of the last one are saved before the
loop stops. The transcript ends in tool results, which is a valid place
to continue from.

### 4. The repeat detector

`harness/durability.py`:

```python
REPEAT_LIMIT = 3
REPEATED = "Repeated call detected; change approach or ask the user"
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
        return [self.streaks[key] >= self.limit for key in keys]
```

The signature is the tool name plus the arguments as canonical JSON, keys
sorted, so two calls that differ only in key order count as the same
call. The detector keeps one streak per signature and rebuilds the table
on every reply, so a signature missing from a reply drops to zero. A
reply with several calls advances each of them: `[grep, cat]` followed
by `[grep, ls]` followed by `[grep]` flags the third `grep`.

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

A flagged call is not run. Running it a third time would give the same
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
    """Finish the tool calls a crash left without results. Returns how many ran.
    ...
    """
    pending = durability.unanswered(messages)
    if not pending:
        return 0
    # the edits belong to the turn that crashed, so /undo takes them back with it
    checkpoint.TURN = max(checkpoint.turns(), default=0) or checkpoint.begin_turn(len(messages))
    run_results(messages, pending)
    count = len(pending)
    ui.note(f"recovered {count} tool call{'s' if count != 1 else ''} left unanswered by the last run")
    return count
...
            messages = session.open_session(saved[0]["id"])
            history.strip(messages)
            ui.resumed(messages)
            ui.replay(messages)
            recover(messages)  # a crash mid-turn left tool calls without results: run them now
```

The recovered calls go through `run_results`, the same function the turn
uses, so `execute_all` decides each one through the permission rules and
the hooks: a command that asks still asks, a denied one gets the denial
as its result, and the checkpoint hook captures an edit. The checkpoint
turn is set to the last one on disk, the turn that was running at the
crash, so `/undo` takes the recovered edit back together with the rest of
that turn. Every result is saved as it lands, so a second crash during
recovery loses nothing either.

## Run it

```bash
pip install -e .
harness
> what is in this directory
```

Pull the network cable, or point `BASE_URL` at a port with nothing
behind it, and ask again. The notes count the tries:

```text
model call failed (APIConnectionError); retry 1 of 4 in 0.5s
model call failed (APIConnectionError); retry 2 of 4 in 1s
model call failed (APIConnectionError); retry 3 of 4 in 2s
model call failed (APIConnectionError); retry 4 of 4 in 4s
model call failed 5 times, giving up (APIConnectionError): Connection error.
```

The prompt comes back. Plug the cable in and type `try again`, and the
model answers the question that is still in the transcript.

To see the recovery, ask for something with a tool call and kill the
process between the reply and its result, for example with a `bash`
command that sleeps for a minute:

```text
> run: sleep 60
```

Close the terminal while the command runs. Then:

```bash
harness --resume
```

The transcript is redrawn, the command asks for approval again as it did
the first time, the sleep runs, and one line reports:

```text
recovered 1 tool call left unanswered by the last run
```

Run the offline tests from the repository root:

```bash
python run_tests.py 34
python check_snippets.py 34
```

## What to notice

- **The retry wraps the stream, not just the request.** With streaming,
  the request succeeds the moment the first byte arrives, and the
  failure comes later. A retry around `create()` alone would miss most
  real failures.
- **Never on a 4xx.** A retry only helps when the next answer can differ.
  A rejected request is rejected again, and four more tries would only
  hide the reason for eight seconds.
- **A failure is a value, not an exception.** `call_llm` returns a
  message with `failed` set. Every caller, the turn, the subagent, the
  compaction agent and the eval judge, reads it without a `try` block.
- **The cap and the detector are per turn.** The detector starts fresh
  with every user message, and so does the counter. A user who says
  "continue" gets another forty calls.
- **The repeated call does not run.** Its result is the warning text.
  This is cheaper than running it, and safe for a tool with side
  effects.
- **Recovery is the ordinary tool path.** `recover` calls the same
  `run_results` the turn calls. Permissions, hooks and checkpoints apply
  because nothing new was written for them.

## Diff from step 33

```bash
diff -r ../step_33_checkpoints/harness harness
```

Added: `durability.py` (`REPEAT_LIMIT`, `REPEATED`, `parse_args`,
`signature`, `LoopDetector`, `unanswered`). Changed: `llm.py`
(`BACKOFF`, `MAX_TRIES`, `sleep`, `retryable`, `describe`, `stream_once`,
`call_llm` retries and returns a failed message, `StreamedMessage.failed`),
`agent.py` (`MAX_CALLS`, `turn` counts calls, stops on a failed message and
runs the detector, `run_results`, `recover`, `chat` recovers on
`--resume`), `subagent.py` (a failed model call becomes the report).
Everything else is unchanged from step 33.
