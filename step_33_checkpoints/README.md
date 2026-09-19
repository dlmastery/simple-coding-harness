# Step 33 - Workspace checkpoints and /undo

**What this step adds:** a copy of every file before the agent changes
it, and three commands that use those copies. Before `write_file` or
`str_replace` runs, the file as it is now goes into
`~/.simple-harness/checkpoints/<session>/<turn>/<hashed path>`, and one
line goes into that turn's manifest. `/undo` puts the files of the last
turn back and cuts the transcript to the start of that turn. `/rewind`
now restores the files as well as the messages. `/checkpoints` lists the
turns and the files each one changed. The capture is a hook, not a change
to the tools: `hooks.py` gains a `BUILTIN` list that the harness
registers itself, and `tools.run` fires it once a call is allowed, so only
a write that really happens is captured.

## Files

```text
step_33_checkpoints/
├── harness/
│   ├── llm.py                        the model call; lists the deferred tools, offers active_schemas()
│   ├── tools.py                      the registry; deferred tools, load_tool(), active_schemas()
│   ├── agent.py                      the loop; turn() numbers each turn and calls begin_turn()
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
├── pyproject.toml                    package metadata; version 0.33.0
└── README.md                         this file
```

## Why checkpoints

Step 8 gave the chat a `/rewind`. It cut the transcript back to an
earlier message, and the model forgot what came after. The files did not.
A rewind after a bad edit left the workspace in the state the transcript
no longer described. The next turn started from a model that thought the
edit had never happened and a file that said otherwise.

The fix is to make the workspace rewind with the transcript. Git could do
it, but not every workspace is a repository, and a commit per tool call
would bury the user's own history. The harness keeps its own copies
instead, outside the workspace, keyed by session and by turn. A turn is
the unit because that is what the user sees: one prompt, one answer, one
`/undo`.

The copies are cheap. A file is captured once per turn, before the first
edit, so a turn that rewrites one file twenty times stores it once. A
file that did not exist is recorded as absent, so undoing the turn deletes
it. The manifest is a JSONL file on disk, like the session log, so a
resumed session can still undo the turn that ran before the restart.

### What breaks without it

Ask for a refactor of three files, watch the model rewrite them, and
decide it went the wrong way. Up to step 32 the choices were `/rewind`,
which forgets the messages and leaves the files as the model left them, or
`git checkout`, if the workspace is a repository and the files were
committed before the turn. After a `/rewind` alone, the next turn starts
from a model that thinks the refactor never happened and a workspace that
says it did; the model reads a file, finds its own edit, and "fixes" it
back. One `/undo` here puts both back together.

## The code, piece by piece

### 1. The store

`harness/checkpoint.py`:

```python
ROOT = Path.home() / ".simple-harness" / "checkpoints"

EDIT_TOOLS = ("write_file", "str_replace")  # the tools whose target file is captured

MANIFEST = "manifest.jsonl"  # one JSON line per captured file, in capture order
TURN_FILE = "turn.json"      # where the transcript stood when the turn began

TURN = 0  # the number of the turn now running; 0 before the first begin_turn
...
def hashed(path):
    """A short, file-system safe name for a path: the first 16 hex digits of its SHA-1."""
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:16]


def session_dir(session_id=None):
    return ROOT / (session_id or session.CURRENT)


def turn_dir(turn=None, session_id=None):
    return session_dir(session_id) / f"{TURN if turn is None else turn:04d}"
```

One directory per session, one per turn under it. A captured file is
stored under a hash of its absolute path, because a path with slashes
and drive letters cannot be a file name, and because the manifest keeps
the real path anyway. The session directory is named by `session.CURRENT`,
the same id the session log uses, so `--resume` finds both.

### 2. Numbering the turn

`harness/checkpoint.py`:

```python
def begin_turn(message_count):
    """Number the next turn and record how long the transcript is before it.

    The number continues from what is on disk, so a resumed session does
    not reuse a turn number that still holds checkpoints.
    """
    global TURN
    TURN = max(turns(), default=0) + 1
    folder = turn_dir()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / TURN_FILE).write_text(json.dumps({"turn": TURN, "messages": message_count}), encoding="utf-8")
    return TURN
```

`harness/agent.py`:

```python
    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    messages.append({"role": "user", "content": user_input})
```

The loop calls `begin_turn` once per user message, after the prompt
hooks let it through and before the message is appended. The number it
records is the length of the transcript at that moment: the index the
user message is about to take. `/undo` cuts the transcript to exactly
that length. The turn number is not a counter in memory. It is one more
than the highest directory on disk, so a session that resumes after a
restart carries on from where its checkpoints stopped.

### 3. The capture

`harness/checkpoint.py`:

```python
def capture(path, tool=None):
    """Save the file as it is before the tool changes it. Returns the manifest entry, or None.

    Once per file per turn: a second write in the same turn keeps the first
    copy, which is the state the turn started from.
    """
    target = Path(path).resolve()
    blob = hashed(target)
    with LOCK:
        folder = turn_dir()
        if any(entry["blob"] == blob for entry in manifest(TURN)):
            return None
        folder.mkdir(parents=True, exist_ok=True)
        existed = target.is_file()
        if existed:
            shutil.copy2(target, folder / blob)
        entry = {"path": str(target), "blob": blob, "existed": existed, "tool": tool, "time": datetime.now().isoformat(timespec="seconds")}
        with (folder / MANIFEST).open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    return entry


def pre_tool_use(event):
    ...
    if event.get("tool_name") not in EDIT_TOOLS:
        return None
    path = (event.get("tool_input") or {}).get("path")
    if not path:
        return None
    try:
        capture(path, tool=event["tool_name"])
    except OSError as failed:
        from .ui import ui  # here, not at the top: ui imports todos, tools imports this module's hook

        ui.note(f"checkpoint: could not capture {path} ({failed}); /undo will not restore it")
    return None
```

`capture` reads the manifest before it writes, so the second edit of a
file in one turn changes nothing. The first copy is the state the turn
started from, and that is the one an undo must bring back. The lock is
there because step 22 runs tool calls in threads and step 29 runs
subagents in threads; two captures of the same file at the same time
would both copy and both append.

`pre_tool_use` is the hook. It takes the event dict every hook takes,
looks at two keys, and returns `None`, which the hook system reads as
"carry on". A copy that fails (a file the process may not read, a full
disk) is said out loud with the file's name: the edit still goes ahead,
because a checkpoint is a convenience and the edit is what the user asked
for, but the note says that `/undo` will not bring this file back.

### 4. A built-in hook

`harness/hooks.py`:

```python
BUILTIN = {  # the harness's own hooks; same shape as a config entry, run first
    "PreToolUse": [{"matcher": "write_file|str_replace", "python": "harness.checkpoint:pre_tool_use"}],
}
...
def run_builtin(event_name, event=None):
    ...
    event = {key: None for key in EVENT_KEYS} | (event or {})
    event["event"] = event_name
    event["cwd"] = event["cwd"] or os.getcwd()
    for hook in BUILTIN.get(event_name, []):
        if matches(hook, event.get("tool_name")):
            run_hook(hook, event)
```

`harness/tools.py`:

```python
    hooks.run_builtin("PreToolUse", {"tool_name": tool_call.function.name, "tool_input": args})  # the checkpoint capture, once the call is allowed
    result = call(tool_call, args)
```

The capture could have been two lines at the top of `tools.run`. It is a
hook instead, for three reasons.

The first is placement. Step 27 already defined the point "before a tool
runs, with its name and its arguments". That is the point the capture
needs, and the matcher already answers "which tools". Adding the same
point again inside `tools.run` would be a second copy of the same idea.

The second is that the tools stay ignorant. `write_file` and
`str_replace` are unchanged from step 5. A new edit tool, or an MCP tool
that writes files, joins the capture by adding its name to the matcher,
not by learning about checkpoints.

The third is honesty about the hook system. If the harness's own
features can be built on it, it is enough for the user's features too.
`BUILTIN` has the same shape as an entry in `hooks.json`, runs through
the same `run_hook`, and shows up in `/hooks` with a `(built-in)` tag.

Where it runs is the one difference from a configured hook. The hooks
from `hooks.json` run in `decide`, before the permission prompt, because
a hook may block a call and the user should not be asked about a call
that will not happen. The built-in runs in `tools.run`, after the prompt:
a write the user declines, or a configured hook blocks, is never
captured, so `/checkpoints` lists only files a turn changed and `/undo`
never "restores" a file to the content it already has.

### 5. Undo

`harness/checkpoint.py`:

```python
def restore(entry, turn, session_id=None):
    """Put one file back as it was: copy the blob over it, or delete it if it was new."""
    target = Path(entry["path"])
    if entry["existed"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(turn_dir(turn, session_id) / entry["blob"], target)
    elif target.exists():
        target.unlink()
    return str(target)


def undo_turn(turn=None, session_id=None):
    """Restore every file of one turn (the last, by default) in reverse order.

    Returns (turn number, transcript length at its start, restored paths),
    or None when there is no turn to undo. The turn's checkpoints are
    removed afterwards: an undone turn cannot be undone twice.
    """
    if turn is None:
        found = turns(session_id)
        if not found:
            return None
        turn = found[-1]
    with LOCK:
        restored = [restore(entry, turn, session_id) for entry in reversed(manifest(turn, session_id))]
        start = start_of(turn, session_id)
        shutil.rmtree(turn_dir(turn, session_id), ignore_errors=True)
    return turn, start, restored
```

An undo walks the manifest backwards. A file that existed gets its copy
back; a file that did not exist is deleted. Then the turn directory goes.
That last step is what makes a second `/undo` move to the turn before,
instead of restoring the same files again and cutting the transcript to
a point it is already at.

### 6. /undo

`harness/commands.py`:

```python
def undo(messages):
    """Restore the files of the last turn and cut the transcript to where that turn began."""
    undone = checkpoint.undo_turn()
    if undone is None:
        ui.note("nothing to undo")
        return messages
    turn, start, restored = undone
    ui.note(f"turn {turn} undone: " + (", ".join(restored) if restored else "no files were changed"))
    if start is None or start > len(messages):
        ui.note("that turn's place in the transcript is not known; the messages stay")
        return messages
    session.rewind_to(start)
    return redraw(messages[:start], "undone")
```

The two halves of an undo are the files and the messages. The files come
first, from the manifest. Then `session.rewind_to` appends the same
`{"rewind_to": N}` marker step 8 uses, so the session log replays to the
same place, and the screen is redrawn from the shortened list. A turn
that changed no files is still a turn: `/undo` on it cuts the transcript
and says so.

### 7. /rewind restores files too

`harness/checkpoint.py`:

```python
def undo_since(message_count, session_id=None):
    """Undo every turn that began at or after a transcript length, newest first.

    This is what `/rewind` needs: keeping the first N messages means the
    files must go back to how they were when message N was about to be
    written.
    """
    undone = []
    for turn in reversed(turns(session_id)):
        start = start_of(turn, session_id)
        if start is None or start < message_count:
            continue
        undone.append(undo_turn(turn, session_id))
    return undone
```

`harness/commands.py`:

```python
def rewind(messages):
    ...
    session.save(messages)  # a fresh chat has no file yet; the rewind entry needs one
    rows = [(i, m) for i, m in enumerate(messages) if m["role"] == "user"]
    choice = ui.pick("rewind to before", [f"{i:<3} {preview(m)}" for i, m in rows])
    if choice is None:
        return messages
    cut = rows[choice][0]
    undone = checkpoint.undo_since(cut)
    restored = [path for _, _, paths in undone for path in paths]
    if undone:
        ui.note(f"{len(undone)} turn(s) undone, {len(restored)} file(s) restored")
    session.rewind_to(cut)
    return redraw(messages[:cut], "rewound")
```

The picker offers turn boundaries, not messages: one row per user message,
labelled with its index, and the cut lands just before the one chosen. Two things go wrong with a cut
anywhere else. An assistant message with tool calls that loses its results
leaves the transcript in a state the API refuses (`tool_calls` without a
`tool` message each). And a turn that began before the cut but wrote
files after it would keep its edits while its messages vanish, the
mismatch this step exists to remove. A cut at a user message is a cut at a
turn boundary, so `undo_since(cut)` takes back exactly the turns whose
messages go, newest first.

### 8. Compaction and /checkpoints

`harness/checkpoint.py`:

```python
def compacted(before, after):
    """Compaction cut the transcript; move every recorded start with it.

    The compacted list is one summary message plus the tail of the old
    list, so a start inside the tail shifts by a constant. A start inside
    the summarised part has no place in the new list any more and is
    recorded as unknown; its files can still be undone, its transcript
    position cannot.
    """
    cut = before - after + 1
```

`harness/commands.py`:

```python
    session.compacted(compacted)
    checkpoint.compacted(before, len(compacted))  # the turn starts move with the messages
    ui.compacted(before, compacted)
    return compacted
...
def checkpoint_list(messages):
    """One row per turn: its number, where it began, and the files it captured."""
    rows = checkpoint.summary()
    ui.note("\n".join(rows) if rows else "no checkpoints in this chat yet")
    return messages
```

Compaction replaces the old messages with one summary and keeps the
tail, so every index in the tail moves by the same amount. The recorded
starts move with them. A turn that was summarised away keeps its files,
but its start becomes unknown: `/undo` on it restores the files and
leaves the messages, and says so.

The arithmetic, worked once. `compact()` returns `[system] + messages[cut:]`,
so a transcript of `before = 41` messages compacted to `after = 11` keeps
the last ten old messages: `cut = 41 - 11 + 1 = 31`, and old index 31 is
new index 1, just after the system message. A turn that started at 35
starts at `35 - 31 + 1 = 5` now; one that started at 20 is inside the
summary and is recorded as `None`.

## Run it

Prerequisites: as step 31. The copies go under
`~/.simple-harness/checkpoints/<session>/`; nothing else is needed.

bash:

```bash
pip install -e .
harness
> create hello.py that prints hello
> change the greeting to "hi there"
> /checkpoints
```

PowerShell:

```powershell
pip install -e .
harness
> create hello.py that prints hello
> change the greeting to "hi there"
> /checkpoints
```

### Expected output

```text
> /checkpoints

  turn 1    from message 1         1 file(s)  hello.py (new)
  turn 2    from message 5         1 file(s)  hello.py

> /undo

  turn 2 undone: C:\work\hello.py
  undone · 5 messages · 1 turns
```

The list shows two turns. Turn 1 has `hello.py (new)`; turn 2 has
`hello.py`. After `/undo` the screen is redrawn with the first turn only,
and `hello.py` prints hello again. A second `/undo` deletes the file and
empties the chat. A third says `nothing to undo`.

Now try the same with `/rewind`. After three turns the picker offers three
rows, one per user message (`1`, `5`, `9`: the index of each in the
transcript), each with the first words of that turn's request. Pick the
second: the note says `2 turn(s) undone, 2 file(s) restored` and the files
are back to how they were after turn 1.

Type `/hooks` and the first row is the capture:

```text
PreToolUse         write_file|str_replace    harness.checkpoint:pre_tool_use  (built-in)
```

Quit, run `harness --resume`, and `/undo` still works: the manifest is on
disk under `~/.simple-harness/checkpoints/<session>/`.

Run the offline tests from the repository root:

```bash
python run_tests.py 33
python check_snippets.py 33
```

## Error handling

The guards of the earlier steps stand: one tool message per call, an
`Error:` string for a bad tool call, a note for a dead model call, ctrl-c
fills the missing results with `(interrupted before this tool ran)`, and
`/exit`, ctrl-d or ctrl-z+enter leave. New in this step:

- **A capture that fails.** `checkpoint: could not capture <path>
  (<reason>); /undo will not restore it` as a note. The edit goes ahead.
- **`/undo` with nothing to undo.** `nothing to undo`. A turn whose start
  is unknown (summarised away by `/compact`) restores its files and says
  `that turn's place in the transcript is not known; the messages stay`.
- **`/rewind` on a fresh chat.** The picker has one row per user message;
  with none it shows nothing to pick and ctrl-d or an out-of-range number
  leaves the chat as it is.
- **A declined or blocked write.** Not captured, so it does not appear in
  `/checkpoints`; the model gets `The user denied this tool call.` or
  `Blocked by hook: ...` as before.
- **A crash mid-turn.** `session.load` still repairs the transcript on
  `--resume` and `/sessions` (step 31); the turn's checkpoints are on
  disk, and the next `/undo` takes that turn back, files and messages.

## Gotchas / What this is not

- **Only the edit tools are captured.** A `bash` command that runs `rm`,
  `sed -i` or `git checkout` changes files the checkpoints do not know
  about. Git is still the safety net for that.
- **Only files are rolled back.** `/undo` does not touch the todo list,
  the plan and its mode, the loaded deferred tools, memories written with
  `remember`, or background jobs. The todo list and the loaded tools are
  rebuilt from the shortened transcript; the rest survives the undo and
  the `<plan>` block may describe a turn that no longer exists.
- **Nothing prunes the store.** Every turn makes a directory and a
  `turn.json` (headless `-p` runs too), and the first write of a file per
  turn copies the whole file. Sessions accumulate under
  `~/.simple-harness/checkpoints/` until you delete them; only an eval run
  cleans up after itself. A session directory whose `.jsonl` you deleted
  is safe to delete too.
- **A rewind is a turn boundary.** The picker offers user messages only.
  There is no way to keep half a turn, by design (section 7).
- **Recovery after a crash is not in this step.** On `--resume`, a call the
  crash left without a result gets a stand-in result, not a re-run, and no
  turn directory is opened for it. Step 34 re-runs such calls and places
  them in the turn that crashed.
- **The copy is whole-file.** A 200 MB file edited by `str_replace` is
  copied once per turn. There is no diffing.
- **Windows.** A path is resolved to its on-disk spelling before it is
  hashed, so `c:/work/a.py` and `C:\work\a.py` are one entry. The tool
  named `bash` still runs through `cmd.exe` and there is no OS sandbox;
  neither changes here.

## What to notice

- A checkpoint is taken before the edit, not after. What is stored is
  the state to go back to, never the state the agent produced.
- The unit is the turn. The parallel tool calls of one reply all land in
  the turn that was running, and one `/undo` takes them all back. A
  subagent is read-only (step 15): its tool set has no edit tool, and from
  step 31 naming one anyway is refused, so it never contributes an entry.
- The turn number lives on disk, not in memory. `begin_turn` reads the
  directory to pick the next one, so a resumed session continues the
  numbering and never overwrites an old turn's copies.
- The capture is a hook. `tools.run` gained one line, the call to
  `run_builtin`; the matcher `write_file|str_replace` is the only place
  that says which tools are captured.
- An undone turn is removed from the store. Undo is not idempotent by
  design: each `/undo` moves one turn further back.
- Only the edit tools are captured. A `bash` command that runs `rm` or
  `sed -i` changes files the checkpoints do not know about. Git is still
  the safety net for that.

## Diff from step 32

```bash
diff -r ../step_32_context_budget/harness harness
```

Added: `checkpoint.py` (`ROOT`, `EDIT_TOOLS`, `MANIFEST`, `TURN_FILE`,
`TURN`, `LOCK`, `hashed`, `session_dir`, `turn_dir`, `turns`,
`begin_turn`, `start_of`, `manifest`, `capture`, `pre_tool_use`,
`restore`, `undo_turn`, `undo_since`, `compacted`, `summary`).
Changed: `hooks.py` (`BUILTIN`, `run_builtin`), `tools.py` (`run` fires the built-ins), `agent.py`
(`checkpoint.begin_turn` in `turn`), `commands.py` (`/undo`,
`/checkpoints`, `rewind` restores files, `compact` moves the turn
starts, `hook_list` shows the built-ins), `ui.py` (`/undo` in the
banner), `evaluate.py` (`isolated` removes the checkpoints of an eval run
and restores `checkpoint.TURN`). Everything else is unchanged from step
32.

## What the next step adds

Step 34 makes the loop survive a bad network, a stuck model and a crash:
retries with backoff, a repeat detector, a per-turn call cap, and recovery
of the tool calls a crash left unanswered.
