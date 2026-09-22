# Stage 8 - Sessions, slash commands and rewind

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 7 - File freshness reminders](../step_07_file_freshness/README.md). Next: [Stage 9 - An installable command](../../02_control/step_09_installable_command/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

This stage is the plumbing behind the features that follow: `--resume`,
`/sessions`, `/rewind`, and the installed command of stage 9.

**What this stage adds:** every message is written to disk as it happens,
a chat can be reopened in a new process, and you can jump back to before
any of your own messages. The transcript is an append-only JSONL file: a
rewind is a marker in the file, not a deletion, and what the agent has
read (`SEEN`, from stage 7) is saved with it so a resumed chat still knows
which files it has looked at.

```text
~/.simple-harness/sessions/<project>/20260910-140212.jsonl
{"role": "system", "content": "..."}
{"role": "user", "content": "add a test"}
{"role": "assistant", "content": null, "tool_calls": [...]}
{"role": "tool", "tool_call_id": "c1", "content": "..."}
{"seen": {"C:\\work\\a.txt": "9c1185a5..."}}   ← state, not a message: what the agent has read
{"role": "assistant", "content": "done"}
{"rewind_to": 1}                                ← a rewind is an entry, not a delete
{"role": "user", "content": "actually, do it differently"}
```

On Windows the folder is `%USERPROFILE%\.simple-harness\sessions\<project>\`;
`<project>` is the current directory's path with every non-alphanumeric
character replaced by `-`.

## What breaks without it

Stages 1-7 keep the transcript in a Python list. Close the terminal, hit
ctrl-c at the wrong moment, or let the model wander down a bad path for
ten minutes, and the whole chat is gone: you start again from "hi". Once
a chat can be paused and continued, three things have to hold at once:

- Nothing is lost between two saves. The loop saves after *every*
  message, including each tool result and your own line before the model
  answers it.
- What comes back off disk is valid to send. A transcript that ends in an
  assistant message whose tool calls never got results is refused by the
  API (400), so a crash between "the model asked for a tool" and "the tool
  answered" would make the chat un-resumable. `session.load` repairs that.
- Undo does not destroy history. You can rewind past a wrong turn and
  still read what happened in the file.

## The code, piece by piece

### 1. Append-only saving

`session.py`:

```python
def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN, SEEN_SAVED
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
        if context.SEEN != SEEN_SAVED:  # what the agent has read: a state entry, not a message
            SEEN_SAVED = dict(context.SEEN)
            f.write(json.dumps({"seen": SEEN_SAVED}) + "\n")
    WRITTEN = len(messages)
```

`WRITTEN` counts how many messages are already in the file, so each call
appends only the new tail. Whenever the agent has read or written a file
since the last save, a `{"seen": ...}` line goes in too; it is state, not
a message, and never reaches the model.

`agent.py` calls `save` after every single message:

```python
    messages.append({"role": "user", "content": user_input})
    session.save(messages)  # on disk before the model answers: ctrl-c during the call loses nothing
```

```python
            messages.append(entry(message))
            session.save(messages)
```

```python
                session.save(messages)  # after every message, so a crash loses nothing
```

Your line is saved before the model call, the reply is saved before the
tools run, and each tool result is saved as it arrives.

### 2. Rewind as an entry

`session.py`:

```python
def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = min(WRITTEN, count)  # a fresh chat has fewer lines on disk than count
```

```python
def replay(session_id, seen=None):
    """Replay the log: messages accumulate, rewinds cut them back, and the
    latest "seen" entry lands in `seen` when a dict is given."""
    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written last line from a kill mid-save
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        elif "seen" in entry:
            if seen is not None:
                seen.clear()
                seen.update(entry["seen"])
        else:
            messages.append(entry)
    return messages
```

A rewind appends a marker; loading replays the file from the top and
applies markers as it meets them. You get undo with the full history kept,
in a format you can inspect with `cat`. The `seen` entries are applied the
same way, so a resumed chat knows what it has read.

### 3. Loading repairs what a crash left behind

`session.py`:

```python
def repair(messages, note=INTERRUPTED):
    """A transcript can end in an assistant message whose tool calls never got results
    (a crash, a kill, ctrl-c). Give each one a result, or the next request is refused."""
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    last = next((m for m in reversed(messages) if m["role"] != "tool"), None)
    if last and last["role"] == "assistant":
        for call in last.get("tool_calls") or []:
            if call["id"] not in answered:
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": note})
    return messages


def load(session_id, seen=None):
    """The messages of a past chat, valid to send: replayed, then repaired."""
    return repair(replay(session_id, seen))
```

Because the reply is saved before its tools run, a kill in between leaves
the file ending in an assistant message with unanswered tool calls. `load`
gives each of those a tool message saying
`(the harness stopped before this tool ran; no result was recorded)`, so
the model sees what happened and the next request is valid. Stage 7's
ctrl-c handler used the same repair with a different note; it now lives
here, because the loop and the loader both need it.

`agent.py`:

```python
    except KeyboardInterrupt:  # ctrl-c mid-turn: keep the transcript valid and ask again
        session.repair(messages, "(interrupted before this tool ran)")
        session.save(messages)
        ui.note("interrupted")
```

### 4. Slash commands never reach the model

`agent.py`:

```python
    if user_input.startswith("/"):  # anything starting with / is a command, never a message
        messages = commands.handle(user_input, messages)
        session.save(messages)
        continue
```

`commands.py`:

```python
def rewind(messages):
    """Offer your own messages and cut just before the one you pick. Cutting anywhere
    else could strand a tool call without its result, which the API refuses."""
    session.save(messages)  # so a fresh chat is on disk before its first marker
    turns = [i for i, m in enumerate(messages) if m["role"] == "user"]
    rows = [f"{i:<4} {preview(messages[i])}" for i in turns]
    choice = ui.pick("rewind to before", rows)
    if choice is None:
        return messages
    count = turns[choice]
    session.rewind_to(count)
    return redraw(messages[:count], "rewound")
```

The contract is one function: take the list, return the list to continue
with. `/rewind` returns a shorter one, `/sessions` a different one. After
either, `redraw` clears the screen and replays the transcript through the
same `ui.agent` / `ui.tool` calls the live loop uses, so a reopened chat
looks as it did.

`/rewind` offers only your own messages, and cuts *before* the one you
pick: everything up to the previous answer stays, and you type the message
again, differently. Assistant and tool rows are not offered because a cut
in the middle of a tool round would leave a tool call without its result.
Any other line starting with `/` (including a typo, or a path like
`/tmp`) prints the command list instead of going to the model; `/exit`
and `/quit` leave.

### 5. Freshness survives a restart

Stage 7 kept `SEEN` as `path -> mtime` in the process. That is not enough
once a chat can be resumed: the dict dies with the process, and an mtime
means nothing after a restart, when the whole file may have been touched
by a checkout. So `SEEN` moves into the session file (the `seen` entry
above) and records a content hash instead:

`context.py`:

```python
def note_seen(path):
    """Called by the read and write tools: remember the content as the agent saw it."""
    path = os.path.abspath(path)
    digest = file_hash(path)
    if digest:
        SEEN[path] = digest
```

```python
def file_changes():
    """Files the agent has seen whose content is no longer what it saw, labelled by git.
    The agent's own writes update SEEN, so they never show up here; an outside edit,
    a second outside edit, a revert or a delete all do."""
    status = git_status()
    changed = {}
    for path, digest in list(SEEN.items()):
        now = file_hash(path)
        if now == digest:
            continue
        code = status.get(path, "D" if now is None else "M")
        changed[path] = LABELS.get(code, code)
        if now is None:
            del SEEN[path]  # deleted: reported once, there is nothing left to re-read
    return changed
```

The check is the same as stage 7's, on content instead of time: a file the
agent has read whose bytes differ now is listed in the late block until
the agent reads it again. `git status --porcelain` only supplies the label
(`modified`, `deleted`, `new`, `renamed`); outside a git repository the
label falls back to `modified` or `deleted`, and the check works the same.
The tools still call `note_seen`, so the agent's own `write_file` and
`str_replace` never trigger the note; edits it makes through `bash` do,
which is right, because it has not seen the result.

## Run it

bash:

```bash
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python agent.py
python agent.py --resume      # continue the most recent chat in this folder
python agent.py --debug       # also print each raw model reply as JSON
```

PowerShell:

```powershell
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python agent.py
python agent.py --resume
```

Expected output:

```text
────────────────────────── coding agent ──────────────────────────
  /sessions  /rewind  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> what is in this folder?

  ┌ late injection ──────────────────────────────┐
  │ <env>                                        │
  │ time: 2026-09-18 14:02                       │
  │ git branch: main                             │
  │ </env>                                       │
  └──────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────┐
  │ bash ls                                      │
  │ ──────────────────────────────────────────── │
  │ agent.py  commands.py  context.py ...        │
  └──────────────────────────────────────────────┘

  agent

  Eight Python files and a README: the stage 8 agent.

  1,204 prompt · 31 completion

> /rewind

  rewind to before
    0  1    what is in this folder?
  number> 0

────────────────────────── coding agent ──────────────────────────
  rewound · 1 messages · 0 turns

> /exit
```

Then `python agent.py --resume` prints `resumed · N messages · T turns`,
replays the chat, and waits for your next line.

## Error handling

- A bad tool call (unknown name, broken JSON, a tool that raises) becomes
  an `Error:` tool message, as in stage 7, and is saved like any other.
- ctrl-c mid-turn: every unanswered tool call gets
  `(interrupted before this tool ran)`, the transcript is saved, and you
  are back at the prompt.
- A dead model call (`openai.APIError`, or an empty reply) prints
  `model call failed: ...`; your message is already on disk and you can
  send it again.
- A kill between a saved reply and its tool results: `--resume` and
  `/sessions` repair the log on load (section 3) and write the repair
  back, so the chat opens and the next request is valid. A reply whose
  arguments were not JSON replays as the raw string instead of crashing.
- A half-written last line (killed mid-save) is skipped on load.
- `/rewind` as the very first command works: the chat is saved before the
  marker is written, so the system prompt is on disk.
- Leaving: `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or
  ctrl-c at the prompt. An empty line does nothing.

## Gotchas

- Everything starting with `/` is a command. To send the model a line
  that begins with a slash, start it with a space or a word.
- `--resume` opens the newest file in the folder for *this* project
  directory; run the agent from the same folder to find the same chats.
  Two agents started in the same second in the same folder share a file.
- Rewinding does not undo files on disk. The transcript goes back; the
  edits the agent made stay. `SEEN` is not rewound either, so the agent
  still knows what it has read.
- The `seen` hashes cover files the agent read or wrote through the
  tools. A file it only touched through `bash` is not watched, same as in
  stage 7.
- `/sessions` lists titles by loading every file in the folder; with
  hundreds of long chats this takes a moment.
- The platform notes from earlier stages hold: the tool named `bash` runs
  through `cmd.exe` on Windows, and there is no sandbox on any platform.

## Files

```text
step_08_sessions_rewind/
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── agent.py         the stage 7 loop plus session.save, --resume, --debug and slash commands
├── commands.py      slash commands: /rewind (user rows only), /sessions, help
├── context.py       SEEN holds content hashes; git supplies the label
├── llm.py           call_llm and entry, unchanged
├── session.py       append-only JSONL log, seen entries, rewind markers, load() with repair
├── skills.py        skill discovery, unchanged from stage 4
├── tools.py         tools, unchanged from stage 7
├── ui.py            replay, session picker, late block and debug panels
├── test_step.py     offline tests: save, rewind, repair on load, seen across a restart, the loop
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## Test

`python -m pytest test_step.py` (from this directory) uses a temp session
folder and a temp git repository: saving is append-only and reloads;
`/rewind` offers only user rows, cuts before the pick, and works as the
first command of a fresh chat; a log that ends in an unanswered tool call
is repaired on load and the repair is written back; broken JSON arguments
replay without crashing; the agent's own writes are quiet while an outside
edit, a revert and a delete are reported and `SEEN` comes back on
`open_session`; and a run through `agent.py` saves every message and
gives a bad tool call its `Error:` result.

## Diff from stage 7

```bash
diff ../step_07_file_freshness/agent.py agent.py
diff ../step_07_file_freshness/context.py context.py
cat session.py commands.py
```

## What the next step adds

Stage 9 packages the agent as an installable command (`pip install -e .`)
so it runs from any project folder, where these session files live per
project.
