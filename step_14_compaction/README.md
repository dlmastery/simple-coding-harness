# Stage 14 - Compaction and context overflow (video 36:50 - 41:51)

> "The longer a chat session goes, the messages array keeps increasing and
> increasing and there's no way to make it shorter. So we are going to do a
> couple of things."

New files `harness/history.py` and `harness/compact.py`; `/compact`
command; `CONTEXT_WINDOW` in config.

## 1. Tool outputs (`history.py`)

"Tool call outputs is one of the main reasons why messages explode."

| | when | what |
|---|---|---|
| **cap** | a tool result is born | over 10,000 characters, the rest is saved to a temp file and the model is told to page through it with `head`, `tail`, `sed`, `grep`. "It is deleted when this whole message turn ends." |
| **strip** | a turn ends | that turn's tool results shrink to a 300-character stub. "This strip only happens on past messages" - the current turn keeps them in full. |
| **fit** | a request is still too big | drop whole tool results, oldest first. |

"Technically this does break the KV cache but this breakage is only for the
last message. The moment you go to the message after that you still use
the cache that has already been established."

## 2. Compaction (`compact.py`)

"When the number of tokens reaches 85% of the total context length, we're
going to reduce it to 35%." Not by dropping old messages every turn -
"that's going to break the KV cache" - but by summarising them once:

- A second agent with no tools reads the messages about to be deleted and
  writes "the handoff note that lets a fresh agent pick the work up
  without re-reading everything": Goal, What happened, Files, State, Next.
- The note is folded into the **system prompt**. "We kept the compaction
  string at the start of the system prompt", so the prefix is rebuilt once
  and then stays byte-identical while the transcript fills from 35% back
  to 85%.
- The cut lands on a message that opens a fresh exchange, so no tool
  result is ever separated from the call that asked for it.
- A later compaction hands the previous note to the summariser, so nothing
  learned early is lost.

The result is also recorded in the session file, so `--resume` reloads the
compacted list.

## Run it

```bash
CONTEXT_WINDOW=6000 harness
> cat every file under harness
> /compact
```

Watch `[output trimmed: ...]` markers appear, then the handoff note in an
orange panel and the message count drop.

## Diff from stage 13

```bash
diff -r ../step_13_readable_todos_input_line/harness harness
```
