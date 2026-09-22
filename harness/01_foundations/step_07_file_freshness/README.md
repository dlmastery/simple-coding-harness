# Stage 7 - File freshness reminders

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 6 - Late injection](../step_06_late_injection/README.md). Next: [Stage 8 - Sessions, slash commands and rewind](../step_08_sessions_rewind/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

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

## The bug this prevents

The model's picture of a file is whatever it last read. You fix a typo in
your editor, a formatter runs, a test writes a fixture. The model does not
know. Its next `str_replace` fails with `old_str was not found`, or worse,
lands on text that is now wrong. With the note it re-reads first.

## The code, piece by piece

### 1. Remembering what the agent saw

`context.py`:

```python
SEEN = {}  # absolute path -> mtime when the agent last read or wrote it


def note_seen(path):
    """Called by the read and write tools: remember the file as the agent saw it."""
    path = os.path.abspath(path)  # "a.txt", "./a.txt" and the full path are one file
    if os.path.exists(path):
        SEEN[path] = os.path.getmtime(path)


def stale_files():
    """Files whose mtime on disk no longer matches what the agent saw. A deleted
    file is reported once and then forgotten: there is nothing left to re-read."""
    stale = []
    for path, mtime in list(SEEN.items()):
        if not os.path.exists(path):
            stale.append(f"{path} (deleted)")
            del SEEN[path]
        elif os.path.getmtime(path) != mtime:
            stale.append(path)
    return stale
```

A global dictionary called `SEEN` records the mtime whenever the agent
reads or writes a file. Paths are stored absolute, so the model reading
`a.txt` and then editing `./a.txt` touches one entry, not two. On the
next call, the harness checks whether any recorded file has a newer
mtime. A file that has disappeared is reported once as deleted and then
dropped; telling the model to re-read it forever would not help.

### 2. The tools report what they touch

`tools.py`:

```python
def read_file(path: str) -> str:
    """Read a file and return its contents."""
    # utf-8 whatever the console code page; newline="" keeps CRLF and LF as they are
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        content = f.read()
    note_seen(path)
    return content
```

One line in `tools.py` updates the mtime whenever the read tool is used,
after the read so that the recorded time is the time of the content the
model got. The same line extends to the write and string-replace tools,
after their write. All three call `note_seen`, so the agent's own edits
do not trigger warnings.

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

The note is part of the injected message from stage 6, so it costs
nothing in the cached prefix. It repeats on every call until the file is
re-read, because re-reading updates `SEEN`; it does not nag about a file
the agent has already re-read.

## Run it

bash:

```bash
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python agent.py
```

PowerShell:

```powershell
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python agent.py
```

Expected output:

```text
> read hello.txt and wait

  ┌──────────────────────────────────────────────┐
  │ read_file hello.txt                          │
  └──────────────────────────────────────────────┘

  agent

  Read it. Waiting.

# ... edit hello.txt in your editor ...

> change the first line to something else

  ┌──────────────────────────────────────────────┐
  │ read_file hello.txt                          │
  └──────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────┐
  │ str_replace {"path": "hello.txt", "old_str": "...", "new_str": "..."}
  │ ──────────────────────────────────────────── │
  │ Replaced 1 match(es) in hello.txt            │
  └──────────────────────────────────────────────┘
```

The reminder appears in the late block of the second turn and the model
reads the file again before editing.

## Error handling

- A watched file that is deleted: listed once as `<path> (deleted)`, then
  forgotten.
- A tool that fails (missing file, bad edit) returns an `Error:` string
  before `note_seen` runs, so nothing wrong is recorded.
- Everything from stage 6 (bad tool calls, ctrl-c, dead model calls,
  `/exit`) is unchanged.

## Gotchas

- Files changed through `bash` (`sed -i`, `git checkout`, a formatter the
  agent runs) are reported as changed too, because `bash` does not call
  `note_seen`. That is correct - the model has not seen the new content -
  but it means the model re-reads after its own shell edits.
- mtime is what the filesystem gives: on some filesystems it has one- or
  two-second resolution, so an edit within the same second as the read
  is missed. Stage 8 compares content hashes instead.
- `SEEN` lives in the process. Leave the agent and it is gone; stage 8
  saves it with the session.

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
├── test_step.py     offline tests: a changed file is reported until re-read; one name per file; deleted once
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## Test

`python -m pytest test_step.py` writes, reads and externally edits temp
files: the note appears after an outside edit and stays until the file
is re-read, three spellings of one path make one `SEEN` entry, and a
deleted file is reported once.

## Diff from stage 6

```bash
diff ../step_06_late_injection/context.py context.py
diff ../step_06_late_injection/tools.py tools.py   # three note_seen() calls
```

## What the next step adds

Stage 8 saves every message to disk, adds `/rewind` and `/sessions`, and
keeps `SEEN` with the session so a resumed chat still knows what it read.
