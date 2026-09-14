# Stage 14 - Compaction and context overflow

The longer a chat session runs, the longer the messages array grows.
Nothing makes it shorter on its own. This stage adds several ways to do
that.

**What this stage adds:** three cheap ways to keep tool output small
(`history.py`), and one expensive way to shrink a whole transcript: a
compaction agent that summarises the past into a handoff note kept in the
system prompt (`compact.py`). Plus `/compact`.

## Files

```text
step_14_compaction/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop calls fit(), sweep(), strip() and compact()
│   ├── commands.py      slash commands gain /compact
│   ├── compact.py       the compaction agent: summarize() and compact()
│   ├── config.py        settings from the env or ~/.simple-harness/env
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
├── test_step.py         offline tests: cap, strip, fit, compaction, the log
├── pyproject.toml       package metadata; version 0.14.0
└── README.md            this file
```

## Part 1 - Tool output (`history.py`)

Tool call output is the main reason a transcript explodes.

### cap: trim a fresh result, park the rest in a file

`harness/history.py`:

```python
CAP = 10_000  # chars of a fresh tool result the agent sees inline
STUB = 300    # chars kept once the turn that produced it is over
```

```python
def cap(text):
    """Trim a fresh tool result, leaving a pointer to the whole thing."""
    if len(text) <= CAP:
        return text
    try:
        path = spill(text)
    except OSError:
        return text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} chars cut and could not be saved.]"
    return (
        text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} of {len(text)} chars cut. "
        f"The whole output is at {path} - page through it with head, tail, "
        "sed -n or grep. It is deleted when this turn ends.]"
    )
```

If a result is longer than the cap of 10,000 characters, it is trimmed.
The trimmed message tells the model where the whole output is, so it can
page through it with head, tail, sed or grep. The file is deleted when the
turn ends. `bash` and `read_file` in `tools.py` wrap their results in
`history.cap(...)`; `sweep()` deletes the temp files at the end of the
turn.

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
Stripping does break the KV cache, but only at the last message. The next
call reuses the cache that was already established in front of it.

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
    return message.content or "(the summariser returned nothing)"
```

The compaction agent is small. Its system prompt says that it is
compacting the transcript of a coding session, that the session is out of
context window, and that it must write the handoff note that lets a fresh
agent pick the work up. It is a second agent with the same `call_llm` and
no tools (`tools=[]`); its note has fixed sections: Goal, What happened,
Files, State, Next.

### Where the note goes: into the system prompt

`harness/compact.py`:

```python
def compact(messages):
    """[system + summary, ...recent tail]. Unchanged if nothing is old enough."""
    cut = tail_start(messages, config.CONTEXT_WINDOW * config.COMPACT_TO)
    if cut <= 1:
        return messages

    system = messages[0]["content"]
    summary = summarize(messages[1:cut], previous_summary(system))
    kept = [
        {"role": "system", "content": base_prompt(system) + "\n\n" + HANDOFF.format(summary=summary)},
        *messages[cut:],
    ]
    strip(kept)  # the tail is old news too; shrink it now, while the prefix is already rebuilt
    return kept
```

The messages about to be deleted pass through this compaction function.
The handoff note is appended to the system prompt. The transcript then has
to fill from 35% back to 85% before the next compaction, so the system
prompt stays the same in between and the cached prefix survives. A later
compaction hands the previous note to the summariser (`previous_summary`) and
replaces it (`base_prompt` strips the old block), so the system prompt
always holds exactly one note and nothing learned early is lost.

`safe_boundary` makes sure the cut lands on a message that opens a fresh
exchange, never between an assistant tool call and its `tool` result.

### Wired into the loop

`harness/agent.py`:

```python
            if history.fit(messages):
                ui.note("dropped old tool output to make this request fit")
```

```python
        history.sweep()          # the turn is over: bin its temp files...
        history.strip(messages)  # ...and shrink the tool output it produced

        if compact.needed(usage):
            messages = commands.compact(messages)
```

`compact.needed(usage)` looks at the real `prompt_tokens` of the last
call, not an estimate. The result is also recorded in the session file
(`session.compacted`), so `--resume` reloads the compacted list.

## Run it

```bash
CONTEXT_WINDOW=6000 harness
> cat every file under harness
> /compact
```

`[output trimmed: ...]` markers appear on long results; `/compact` shows
the handoff note in an orange panel and the message count drop.

## Diff from stage 13

```bash
diff -r ../step_13_readable_todos_input_line/harness harness
```

New: `history.py`, `compact.py`. Changed: `agent.py`, `commands.py`
(`/compact`), `config.py`, `llm.py` (`tools=` argument), `session.py`,
`tools.py`, `ui.py`.
