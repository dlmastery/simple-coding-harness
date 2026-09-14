# Stage 7 - File freshness reminders

The harness can alert the agent when a file has changed since the agent
last read it, and prompt the agent to read the file again before editing
it.

**What this stage adds:** the harness remembers the modification time of
every file the agent touched, and warns the agent, through the late block,
when one of them changes underneath it.

```text
read_file / write_file / str_replace ──▶ SEEN[path] = mtime
next call: reminder() ──▶ any path whose mtime moved ──▶ <system-reminder> in the late block
```

## Files

```text
step_07_file_freshness/
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── agent.py         the loop, unchanged from stage 6
├── context.py       SEEN mtimes, note_seen() and the stale-file note
├── llm.py           call_llm, unchanged
├── skills.py        skill discovery, unchanged from stage 4
├── tools.py         the file tools call note_seen on every touch
├── ui.py            the presentation layer, unchanged
├── test_step.py     offline tests: a changed file is reported once
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## The code, piece by piece

### 1. Remembering what the agent saw

`context.py`:

```python
SEEN = {}  # path -> mtime when the agent last read or wrote it


def note_seen(path):
    """Called by the read and write tools: remember the file as the agent saw it."""
    if os.path.exists(path):
        SEEN[path] = os.path.getmtime(path)


def stale_files():
    """Files whose mtime on disk no longer matches what the agent saw."""
    return [p for p, mtime in SEEN.items() if not os.path.exists(p) or os.path.getmtime(p) != mtime]
```

A global dictionary called `SEEN` records the mtime whenever the agent
reads or writes a file. On the next call, the harness checks whether any
recorded file has a newer mtime.

### 2. The tools report what they touch

`tools.py`:

```python
def read_file(path: str) -> str:
    """Read a file and return its contents."""
    note_seen(path)
    with open(path) as f:
        return f.read()
```

One line in `tools.py` updates the mtime whenever the read tool is used.
The same line extends to the write and string-replace tools. Here all
three call `note_seen`, so the agent's own edits do not trigger warnings.

### 3. The warning rides in the late block

`context.py`:

```python
def stale_note():
    """Warn about files that changed on disk since the agent read them."""
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed on disk since you read them. Read them again "
        "before editing:\n" + "\n".join(changed) + "\n</system-reminder>"
    )
```

```python
            "</env>" + stale_note()
```

The stale note arrives as a system reminder. It says that these files
changed on disk since the agent read them, and it lists every file that
changed since the agent last saw it.

## The bug this prevents

The model's picture of a file is whatever it last read. You fix a typo in
your editor, a formatter runs, a test writes a fixture. The model does not
know. Its next `str_replace` fails with "old_str was not found", or worse,
lands on text that is now wrong. With the note it re-reads first.

The note is part of the injected message from stage 6, so it costs
nothing in the cached prefix. It disappears by itself once the file is
re-read, because re-reading updates `SEEN`.

## Run it

```bash
python agent.py
> read hello.txt and wait
# ... edit hello.txt in your editor ...
> change the first line to something else
```

The reminder appears and the model reads the file again before editing.

## Diff from stage 6

```bash
diff ../step_06_late_injection/context.py context.py
diff ../step_06_late_injection/tools.py tools.py   # three note_seen() calls
```
