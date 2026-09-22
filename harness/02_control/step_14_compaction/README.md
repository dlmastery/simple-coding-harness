# Stage 14 - Compaction and context overflow

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Keep actions within limits**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 13 - Readable todos and a real input line](../step_13_readable_todos_input_line/README.md). Next: [Stage 15 - Exploration subagents](../step_15_subagents/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

The longer a chat session runs, the longer the messages array grows.
Nothing makes it shorter on its own. This stage adds several ways to do
that.

**What this stage adds:** three cheap ways to keep tool output small
(`history.py`), and one expensive way to shrink a whole transcript: a
compaction agent that summarises the past into a handoff note kept in the
system prompt (`compact.py`). Plus `/compact`.

## Why: the transcript only ever grows

Every tool result stays in `messages` for the rest of the session. One
`cat` of a 4,000-line file is 40,000 characters, about 10,000 tokens, and
it is resent on every call after that. Twenty such calls and a 128k model
answers with a 400 (`context_length_exceeded`); without this stage the
loop has no answer to that but a traceback. Long before the hard limit the
model also gets worse: a prompt full of stale `ls` output crowds out the
task. So the harness caps what a tool may return, shrinks results once
their turn is over, and when the prompt still reaches 85% of the window,
replaces the oldest part of the conversation with a written handoff note.

## Files

```text
step_14_compaction/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop calls fit(), sweep(), strip() and compact()
│   ├── commands.py      slash commands gain /compact
│   ├── compact.py       the compaction agent: summarize() and compact()
│   ├── config.py        settings, plus CONTEXT_WINDOW, COMPACT_AT, COMPACT_TO
│   ├── context.py       the late block, unchanged
│   ├── history.py       cap(), spill(), sweep(), strip() and fit()
│   ├── llm.py           call_llm takes an optional tool set
│   ├── permissions.py   the rule table, unchanged
│   ├── prompt.py        the input line, unchanged
│   ├── sandbox.py       the OS sandbox, unchanged
│   ├── session.py       the log records compactions so --resume reloads them
│   ├── skills.py        skills, unchanged
│   ├── todos.py         the plan, unchanged
│   ├── tools.py         bash and read_file cap their output via history.cap()
│   └── ui.py            the compacted() panel shows the handoff note
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: cap, strip, fit, the two markers, compaction, the log, bad tool calls
├── pyproject.toml       package metadata; version 0.14.0
└── README.md            this file
```

## Part 1 - Tool output (`history.py`)

Tool call output is the main reason a transcript explodes. Three
mechanisms, cheapest first, and two markers that tell them apart:

`harness/history.py`:

```python
CAP = 10_000  # chars of a fresh tool result the agent sees inline
STUB = 300    # chars kept once the turn that produced it is over

CAPPED = "[output capped:"    # from cap(): the full text is on disk until the turn ends
TRIMMED = "[output trimmed:"  # from strip() and fit(): gone for good; stripping twice is a no-op
```

`CAPPED` means "the rest is in a file for this turn"; `TRIMMED` means "the
rest is gone". `strip` and `fit` look for `TRIMMED` only, so a capped
result is still shrunk once its turn is over. (An earlier version used one
marker for both, and the largest results - exactly the ones that hit the
cap - were the only ones never stripped.)

### cap: trim a fresh result, park the rest in a file

`harness/history.py`:

```python
def cap(text):
    """Trim a fresh tool result, leaving a pointer to the whole thing."""
    if len(text) <= CAP:
        return text
    try:
        path = spill(text)
    except OSError:
        return text[:CAP] + f"\n\n{CAPPED} {len(text) - CAP} chars cut and could not be saved.]"
    return (
        text[:CAP] + f"\n\n{CAPPED} {len(text) - CAP} of {len(text)} chars cut. "
        f"The whole output is at {path} - page through it with head, tail, "
        "sed -n or grep. It is deleted when this turn ends.]"
    )
```

If a result is longer than the cap of 10,000 characters, it is trimmed.
The capped message tells the model where the whole output is, so it can
page through it with head, tail, sed or grep; the system prompt in
`llm.py` says the same. `bash` and `read_file` in `tools.py` wrap their
results in `history.cap(...)`; `sweep()` deletes the temp files at the end
of the turn, so the path in the message only works during that turn.

### strip: once a turn is over, shrink its results to a stub

`harness/history.py`:

```python
def strip(messages):
    """Shrink every tool result from finished turns. Returns how many shrank.

    Called after a turn ends, so "everything in the list" and "everything the
    model no longer needs in full" are the same set.
    """
    shrunk = 0
    for message in messages:
        content = message.get("content") or ""
        if message["role"] != "tool" or TRIMMED in content or len(content) <= STUB:
            continue
        message["content"] = (
            content[:STUB] + f"\n\n{TRIMMED} {len(content) - STUB} more chars. "
            "Run the command again if you need them.]"
        )
        shrunk += 1
    return shrunk
```

Strip touches past turns only. While the agent is still working through
the current message, it needs those tool outputs to take the next step.
Once the user has asked something new, it no longer needs the full tool
outputs from before. The `TRIMMED` marker makes stripping idempotent.
Stripping does break the KV cache, but only from the first tool result of
the previous turn onwards: everything in front of that - the system
prompt and every older, already-stripped turn - is byte-identical to the
last request and is served from the cache.

### fit: the panic button

`harness/history.py`:

```python
def fit(messages):
    """Last resort: discard whole tool results, oldest first, until it fits."""
    budget = config.CONTEXT_WINDOW * config.COMPACT_AT
    dropped = 0
    for message in messages:
        if estimate(messages) <= budget:
            break
        if message["role"] == "tool" and TRIMMED not in (message.get("content") or ""):
            message["content"] = f"{TRIMMED} dropped to fit the context window.]"
            dropped += 1
    return dropped
```

`fit` runs before every call. It walks the list from the front and blanks
tool results that are not yet trimmed, until the character estimate is
under 85% of the window. In practice everything from earlier turns is
already stripped, so what it can drop is the current turn's own results -
a turn whose forty `cat`s add up to more than the window. It never touches
user or assistant messages; a single pasted 300 KB user message is beyond
it (see Gotchas).

## Part 2 - Compaction (`compact.py`)

When the prompt reaches 85% of the context window, the harness cuts it
back to 35%. It cannot just drop the first messages at every turn, because
that breaks the KV cache. Instead it compacts: a summary of everything
that has happened in the session replaces the messages about to be
deleted.

### The thresholds

`harness/config.py`:

```python
CONTEXT_WINDOW = int(os.environ.get("CONTEXT_WINDOW", 128_000))
COMPACT_AT = 0.85  # compact once the prompt crosses this fraction of the window
COMPACT_TO = 0.35  # and cut back to this fraction, so it does not retrigger soon
```

In numbers, for the default 128k window: compaction fires once a request
measured 108,800 prompt tokens; the tail kept after it is about 44,800
tokens minus the size of the system prompt (with the new handoff note in
it, roughly 1,500 to 2,500 tokens). The transcript then has to grow by
some 60,000 tokens before the next compaction.

### The compaction agent

`harness/compact.py`:

```python
SYSTEM_PROMPT = """
You are compacting the transcript of a coding session. The session is out of
context window. Write the handoff note that lets a fresh agent pick the work up
without re-reading anything.
```

```python
def summarize(messages, previous=""):
    """One model call, no tools. Returns the handoff note."""
    message, _ = llm.call_llm(
        [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": render(messages, previous)}],
        tools=[],
    )
    if not message.content:
        raise RuntimeError("the summariser returned nothing")  # keep the transcript rather than replace it with nothing
    return message.content
```

The compaction agent is small. Its system prompt says that it is
compacting the transcript of a coding session, that the session is out of
context window, and that it must write the handoff note that lets a fresh
agent pick the work up. It is a second agent with the same `call_llm` and
no tools (`tools=[]`); its note has fixed sections: Goal, What happened,
Files, State, Next. `render` flattens the messages for it, tool calls
included as `[called bash: {...}]`. Note what it reads: by the time
compaction runs, every past tool result is already a 300-character stub,
so the "Files" section is reconstructed from those stubs and from what the
assistant said, not from full file contents. An empty answer is an error,
never an empty note - the transcript is worth more than a blank summary.

### Where the note goes: into the system prompt

`harness/compact.py`:

```python
def compact(messages):
    """[system + summary, ...recent tail]. Unchanged if nothing is old enough."""
    global COMPACTED_AT
    # the system prompt, handoff note included, is part of every request: budget for it
    budget = config.CONTEXT_WINDOW * config.COMPACT_TO - estimate(messages[:1])
    cut = tail_start(messages, budget)
    if cut <= 1:
        return messages

    system = messages[0]["content"]
    summary = summarize(messages[1:cut], previous_summary(system))
    kept = [
        {"role": "system", "content": base_prompt(system) + "\n\n" + HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now, while the prefix is already rebuilt
    COMPACTED_AT = len(kept)
    return kept
```

The messages about to be deleted pass through this compaction function.
The handoff note is appended to the system prompt. The transcript then has
to fill from 35% back to 85% before the next compaction, so the system
prompt stays the same in between and the cached prefix survives. A later
compaction hands the previous note to the summariser (`previous_summary`)
and replaces it (`base_prompt` strips the old block), so the system prompt
always holds exactly one note and nothing learned early is lost.

`tail_start` walks back from the end until the tail fills the budget, then
`safe_boundary` moves the cut forward to a message it is safe to cut at:

```python
def safe_boundary(messages, start):
    """First index at or after `start` where cutting cannot orphan a tool call.

    A tool result has to keep the assistant message that asked for it, and
    some providers refuse a transcript whose first message after the system
    prompt is not the user's, so the only safe cut points are user messages.
    """
    for index in range(max(start, 1), len(messages)):
        if messages[index]["role"] == "user":
            return index
    return len(messages)
```

A cut on an assistant or tool message could separate a tool call from its
result, which every API refuses; a cut on an assistant message that
follows a tool result is accepted by OpenAI but refused by stricter
providers behind OpenRouter. Cutting only at user messages avoids both.

### Wired into the loop

`harness/agent.py`:

```python
                if history.fit(messages):
                    ui.note("dropped old tool output to make this request fit")
```

```python
        history.sweep()          # the turn is over: bin its temp files...
        history.strip(messages)  # ...and shrink the tool output it produced

        if compact.needed(usage, messages):
            messages = commands.compact(messages)
```

`compact.needed(usage, messages)` looks at the real `prompt_tokens` of the
last call, not an estimate - and only ever after a turn, never in the
middle of one:

`harness/compact.py`:

```python
def needed(usage, messages):
    """Has the last request grown past the point where we rebuild?

    Never twice on the same transcript: if a compaction just happened and
    the prompt is still over the line, another one would only rewrite the
    system prompt again and throw the cache away for nothing.
    """
    over = (usage.get("prompt_tokens") or 0) > config.CONTEXT_WINDOW * config.COMPACT_AT
    return over and len(messages) > COMPACTED_AT
```

The second condition matters with a small window: the summary, the tool
schemas and the estimate error can leave the compacted prompt still over
85%, and without it the harness would call the summariser and rewrite the
system prompt again every turn - exactly the cache churn compaction exists
to prevent. `commands.compact` sets the same mark when the summariser
fails or when nothing is old enough, so a broken summariser costs one
failed call, not one per turn.

`harness/commands.py`:

```python
def compact(messages):
    before = len(messages)
    try:
        with ui.working("compacting"):
            compacted = compaction.compact(messages)
    except Exception as failure:  # noqa: BLE001
        # One more API call, fired when the window is nearly full - the worst
        # moment to lose the session over a rate limit. Keep going as we are.
        ui.note(f"compaction failed ({type(failure).__name__}); transcript kept as is")
        compaction.COMPACTED_AT = before  # do not try again until the transcript has grown
        return messages
```

The result is also recorded in the session file (`session.compacted`
appends a `{"compacted": [...]}` entry), so `--resume` and `/sessions`
reload the compacted list, not the original messages.

## Run it

bash:

```bash
CONTEXT_WINDOW=6000 harness
> cat every file under harness
> /compact
```

PowerShell:

```powershell
$env:CONTEXT_WINDOW = 6000; harness
> cat every file under harness
> /compact
```

`CONTEXT_WINDOW=6000` is far below any real model's window; it is there
so you can watch compaction fire in a two-minute session. With such a
small window the system prompt and tool schemas alone are near half of
it, so the harness leans on the "not twice on the same transcript" guard
rather than on a comfortable 35% target - see Gotchas.

### Expected output

```text
  ┌──────────────────────────────────────────────────────────────┐
  │ bash cat harness/*.py                                        │
  │ ──────────────────────────────────────────────────────────── │
  │ """Stage 14 - the loop keeps the transcript inside ...       │
  │ ...                                                          │
  │ [output capped: 23811 of 33811 chars cut. The whole output   │
  │ is at /tmp/harness-k2x9.txt - page through it with head,     │
  │ tail, sed -n or grep. It is deleted when this turn ends.]    │
  └──────────────────────────────────────────────────────────────┘

  agent
  Here is what each file does: ...

  ┌─ compacted · 9 → 3 messages ─────────────────────────────────┐
  │ ## Goal                                                      │
  │ Read every file under harness/ and explain them.             │
  │ ## What happened                                             │
  │ Ran cat harness/*.py; the output was capped at 10,000 chars  │
  │ ...                                                          │
  │ ## Next                                                      │
  │ Nothing pending; wait for the next request.                  │
  └──────────────────────────────────────────────────────────────┘
```

`[output capped: ...]` markers appear on long results while the turn is
running; after the turn `[output trimmed: ...]` stubs replace them in the
transcript (you do not see that - it is the model's view). The panel shows
the handoff note and the message count drop; when the prompt crossed 85%
on its own, the same panel appears without you typing `/compact`.

## Error handling

- Compaction failing (a rate limit, an empty answer from the summariser)
  is a note - `compaction failed (RuntimeError); transcript kept as is` -
  and the session goes on uncompacted; it is not retried until the
  transcript has grown.
- `/compact` on a short transcript says `nothing old enough to compact yet`.
- A temp file that cannot be written (`OSError`) leaves a capped result
  with no path in it; the model still gets the first 10,000 characters.
- Everything from stage 13 still holds: a bad tool call is an `Error:`
  result, a slow command times out, ctrl-c ends the turn with the pending
  tool calls answered, a dead model call is `model call failed: ...` and
  the prompt comes back.
- To leave: `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at
  the prompt.

## Gotchas / What this is not

- Compaction never fires mid-turn. A single turn of forty capped `bash`
  results is about 100k tokens; `fit` is what stands between that and a
  400, and it can only blank the current turn's results.
- `fit` cannot help with a huge user or assistant message. Paste a 300 KB
  log as your request and the next call fails with a 400; nothing here
  splits a message.
- With a tiny window like the demo's 6,000, one compaction may not get
  the prompt under 85% (the system prompt, schemas and note are most of
  it). The `COMPACTED_AT` guard stops the summariser from being called
  again every turn; the prompt just stays large until the transcript grows.
- The temp file path in a capped result is dead once the turn ends. A
  model that reads it in the next turn gets `No such file`; the system
  prompt tells it to re-run the command instead.
- The summariser sees stubs, not full tool output. What it writes under
  "Files" is only as good as what the assistant said about them.
- `session.compacted` rewrites the whole message list into the log,
  system prompt included, so a session file grows by one full transcript
  per compaction. `all_sessions()` titles a compacted session by its
  first surviving user message.

## What the next stage adds

Stage 15 adds a `task` tool: a subagent with its own context window that
explores the codebase and returns only its findings, so a search does not
fill the main transcript in the first place.

## Diff from stage 13

```bash
diff -r ../step_13_readable_todos_input_line/harness harness
```

New: `history.py`, `compact.py`. Changed: `agent.py`, `commands.py`
(`/compact`), `config.py`, `llm.py` (`tools=` argument), `session.py`,
`tools.py`, `ui.py`.
