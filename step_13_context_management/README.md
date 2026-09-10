# Step 13 - Context management

**New in this step:** four mechanisms that keep the transcript inside the
context window, an automatic compaction agent, `/compact`, and an input
line that can edit long messages.

The prompt is the whole conversation and it only grows. Sooner or later it
will not fit. This step is what every serious harness does about that,
ordered from cheapest to most expensive:

| # | Mechanism | When | What it does | Cost |
|---|-----------|------|--------------|------|
| 1 | `history.cap` | a tool result is born | keep 10k chars inline, spill the rest to a temp file the model can `grep` | free |
| 2 | `history.strip` | a turn ends | shrink that turn's tool results to a 300-char stub | free |
| 3 | `history.fit` | a request is still too big | drop whole tool results, oldest first | lossy |
| 4 | `compact.compact` | prompt crosses 85% of the window | a second agent writes a handoff note that replaces the old history | one API call, lossy |

## The rule underneath all four: never edit the prefix

Step 8 introduced prompt caching: the cached prefix is only useful if it is
byte-identical. So every mechanism here edits *only the tail*:

- `cap` decides once, when the result is created, before it is ever sent.
- `strip` runs after a turn ends, so it changes the newest messages, right
  before the next user message lands.
- `fit` and `compact` only touch what is after the **locked prefix** -
  system prompt plus the newest `<summary>` - which `history.locked()`
  derives by scanning, so it survives `/rewind` and session switches.

Compaction cuts deep (to 35% of the window, not 85%) on purpose: every
rebuild invalidates the whole cache, so you want it to happen rarely.

## The compaction agent

`compact.py` is a second, tool-less agent with one prompt: write the
handoff note a fresh agent would need. The note has fixed sections (Goal,
What happened, Files, State, Next) and the result is wrapped in
`<summary>` tags as a *user* message, with a line telling the model it is
its own memory, not something the user said.

`safe_boundary` matters: a tool result must keep the assistant message
that asked for it, so the cut can only land on a message that opens a
fresh exchange. Cut in the wrong place and the API rejects the request.

Compaction is also recorded in the session file (`{"compacted": [...]}`),
so `--resume` reloads the compacted list, not the original.

## Why prompt_toolkit

`input()` cannot edit a line that has wrapped. Long prompts to a coding
agent wrap. `inputline.py` swaps in prompt_toolkit: same `read()` contract,
plus persistent history and alt-enter for newlines.

## Run it

```bash
python -m harness
you> cat every .py file under harness
you> /compact
```

The first turn shows `[output trimmed: ...]` markers with temp-file paths.
`/compact` shows the handoff note in an orange panel and the message count
drop. Set `CONTEXT_WINDOW=4000` in the environment to watch automatic
compaction fire after a couple of turns.

## Diff from step 12

```bash
diff -r ../step_12_permissions_and_sandbox/harness harness
```

New: `history.py`, `compact.py`, `inputline.py`. Changed: `agent.py`
(fit / sweep / strip / auto-compact), `commands.py` (`/compact`),
`session.py` (compacted entries), `tools.py` (cap), `ui.py`, `config.py`,
`prompts.py`.
