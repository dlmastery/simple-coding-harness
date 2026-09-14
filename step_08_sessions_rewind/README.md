# Stage 8 - Sessions, slash commands and rewind

This stage is the plumbing behind the features that follow: `--resume`,
`/sessions`, `/rewind`, and the installed command of stage 9.

**What this stage adds:** every message is written to disk as it happens,
a chat can be reopened in a new process, and you can jump back to an
earlier point. The file-change check moves from the in-memory `SEEN` dict
to `git status`, because a dict does not survive a restart.

```text
~/.simple-harness/sessions/<project>/20260910-140212.jsonl
{"role": "system", "content": "..."}
{"role": "user", "content": "add a test"}
{"role": "assistant", "content": null, "tool_calls": [...]}
{"role": "tool", "tool_call_id": "c1", "content": "..."}
{"rewind_to": 2}                     ← a rewind is an entry, not a delete
{"role": "user", "content": "actually, do it differently"}
```

## Files

```text
step_08_sessions_rewind/
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── agent.py         the loop; reads --resume, --debug and slash commands
├── commands.py      slash commands: /rewind, /sessions
├── context.py       the late block, now watching git status for changes
├── llm.py           call_llm, unchanged
├── session.py       append-only JSONL log, load(), /rewind markers
├── skills.py        skill discovery, unchanged from stage 4
├── tools.py         tools; note_seen is gone, git watches files now
├── ui.py            replay, session picker, late block and debug panels
├── test_step.py     offline tests: save, rewind, git reminder, commands
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## The code, piece by piece

### 1. Append-only saving

`session.py`:

```python
def save(messages):
    """Append what is new. Never rewrite what is already on disk."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
    WRITTEN = len(messages)
```

`WRITTEN` counts how many messages are already in the file, so each call
appends only the new tail. The loop calls `session.save(messages)` after
every single message, including each tool result, so a crash mid-turn
loses nothing.

### 2. Rewind as an entry

`session.py`:

```python
def rewind_to(count):
    """Record a rewind as an entry, so the old messages stay in the file."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count
```

```python
def load(session_id):
    """Replay the log: messages accumulate, rewinds cut them back."""
    messages = []
    for line in path_for(session_id).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # a half-written last line from a kill mid-save
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        else:
            messages.append(entry)
    return messages
```

A rewind appends a marker; loading replays the file from the top and
applies markers as it meets them. You get undo with the full history kept,
in a format you can inspect with `cat`.

### 3. Slash commands never reach the model

`agent.py`:

```python
    if user_input.startswith("/"):
        messages = commands.handle(user_input, messages)
        session.save(messages)
        continue
```

`commands.py`:

```python
def rewind(messages):
    rows = [f"{m['role']:<9} {preview(m)}" for m in messages]
    choice = ui.pick("rewind to", rows)
    if choice is None:
        return messages
    session.rewind_to(choice + 1)
    return redraw(messages[: choice + 1], "rewound")
```

The contract is one function: take the list, return the list to continue
with. `/rewind` returns a shorter one, `/sessions` a different one. After
either, `redraw` clears the screen and replays the transcript through the
same `ui.agent` / `ui.tool` calls the live loop uses, so a reopened chat
looks exactly as it did.

### 4. Freshness moves to git

`context.py`:

```python
def git_status():
    """path -> status code, straight from git."""
    return {line[3:]: line[:2].strip() for line in git("status --porcelain").splitlines()}


LAST_STATUS = git_status()


def file_changes():
    """What git sees as different since the previous call."""
    global LAST_STATUS
    now = git_status()
    changed = {p: c for p, c in now.items() if LAST_STATUS.get(p) != c}
    LAST_STATUS = now
    return changed
```

Stage 7's `SEEN` dict lives in the process. Once a chat can be resumed in
a new process that memory is gone, so the check moves onto
`git status --porcelain`, which git remembers on its own. Same
`<system-reminder>`, different source of truth; `note_seen` leaves
`tools.py`.

## Run it

```bash
python agent.py
> what is in this folder?
> /rewind          # pick 1 to go back to just after your first message
> /sessions        # or reopen any earlier chat
python agent.py --resume
```

`--debug` prints the raw model reply as JSON after each call.

## Diff from stage 7

```bash
diff ../step_07_file_freshness/agent.py agent.py
diff ../step_07_file_freshness/context.py context.py
cat session.py commands.py
```
