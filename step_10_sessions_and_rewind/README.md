# Step 10 - Sessions, slash commands, rewind

**New in this step:** every message is written to a JSONL file as it
happens; `--resume` picks up the last chat; `/sessions` opens any past chat;
`/rewind` jumps back to an earlier point.

```
~/.simple-harness/sessions/<project>/20260910-140212.jsonl
{"role": "system", "content": "..."}
{"role": "user", "content": "add a test for str_replace"}
{"role": "assistant", "content": null, "tool_calls": [...]}
{"role": "tool", "tool_call_id": "c1", "content": "..."}
{"rewind_to": 2}                        ← a rewind is an entry, not a delete
{"role": "user", "content": "actually, do it differently"}
```

## Append-only

`session.save()` writes only the messages that are not on disk yet, after
every single message - not at the end of the turn - so a crash mid-turn
loses nothing. It never rewrites the file.

A rewind is therefore *also* an append: `{"rewind_to": N}`. `load()` replays
the file from the top, growing the list on normal entries and cutting it on
markers. You get an undo that keeps the full history, and a file format
simple enough to read with `cat`.

## Slash commands

Anything starting with `/` is intercepted before it reaches the model. The
contract in `commands.py` is one function: take the message list, return
the list the loop should continue with. `/rewind` returns a shorter list;
`/sessions` returns a different one; anything else prints help. Step 13
adds `/compact` with the same shape.

## The screen has to follow the history

After a rewind or a session switch the screen shows things that are no
longer in `messages`. `commands.redraw()` clears it and replays the
transcript through the same `ui.agent` / `ui.tool` calls the live loop
uses, so a resumed chat looks exactly like it did when it was live.

## Run it

```bash
python -m harness
you> what is in this folder?
you> /rewind          # pick 1 to go back to just after your first message
you> /sessions        # or reopen any earlier chat
```

Then `python -m harness --resume` picks up where the newest chat left off.

## Diff from step 9

```bash
diff -r ../step_09_file_freshness/harness harness
```

New: `session.py`, `commands.py`. Changed: `agent.py` (`--resume`, save
calls, the `/` branch), `ui.py` (pick, replay, resumed, clear, user).
