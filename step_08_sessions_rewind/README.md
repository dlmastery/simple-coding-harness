# Stage 8 - Sessions, slash commands and rewind

This stage is in the reference commits but not narrated in the video; it is
the plumbing that makes the later demos (`--resume`, the installed
`neuralcode` command) work.

New: `session.py`, `commands.py`. Changed: `agent.py` (`--resume`,
`--debug`, the `/` branch, a `save()` after every message), `ui.py`
(replay, pick, injection panel, debug panel), `context.py`.

```
~/.simple-harness/sessions/<project>/20260910-140212.jsonl
{"role": "system", "content": "..."}
{"role": "user", "content": "add a test"}
{"role": "assistant", "content": null, "tool_calls": [...]}
{"role": "tool", "tool_call_id": "c1", "content": "..."}
{"rewind_to": 2}                     ← a rewind is an entry, not a delete
```

## Append-only

`session.save()` writes only the messages not yet on disk, after every
message, so a crash mid-turn loses nothing. A rewind appends a marker;
`load()` replays the file and applies markers as it goes. You get undo with
the full history preserved, in a format you can read with `cat`.

## Slash commands

Anything starting with `/` never reaches the model. A command takes the
message list and returns the list to continue with: shorter for `/rewind`,
a different one for `/sessions`. After either, the screen is redrawn from
the transcript through the same `ui.agent` / `ui.tool` calls the live loop
uses.

## Why freshness moves to git here

Stage 7's `SEEN` dict of mtimes lives in the process. Once chats can be
resumed in a new process, that memory is gone, so the check moves onto
`git status --porcelain`: the block lists every path whose status changed
since the previous call, and git remembers across processes. Same
`<system-reminder>`, different source of truth.

## Diff from stage 7

```bash
diff ../step_07_file_freshness/agent.py agent.py
diff ../step_07_file_freshness/context.py context.py
```
