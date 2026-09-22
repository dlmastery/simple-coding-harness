# Stage 5 - File editing tools

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 4 - Skill discovery and reading](../step_04_skills/README.md). Next: [Stage 6 - Late injection](../step_06_late_injection/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

Two more tools: a write-file tool and a string-replace tool. The
write-file tool writes a new file to disk. The string-replace tool swaps
one block of text in a file for another.

**What this stage adds:** the agent can change code. Two tools in
`tools.py`, one line in the system prompt.

## Why two tools, and why exact text

`bash("echo ... > file")` can write a file, but quoting a whole source
file through a shell is fragile and the model knows it. A tool whose
argument *is* the content has no quoting problem. For edits, the model's
idea of line numbers drifts the moment it makes one change, so
`str_replace` works on exact text: find this block, put that block in its
place. Without these two tools the agent reads code and talks about it;
with them it is a coding agent.

## The code, piece by piece

### 1. `write_file`

`tools.py`:

```python
def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)  # a new file in a new folder is one call
    with open(path, "w", encoding="utf-8", newline="") as f:  # written as given: no newline translation
        f.write(content)
    return f"Wrote {path}"
```

`write_file` takes a path and a content string and calls `f.write`.
Missing parent folders are created, so "put a test in `tests/unit/`" is
one call. Note what it returns: a short confirmation, not the content.
Tool results go into the model's context, so a tool should say what
happened, not echo what it was given.

### 2. `str_replace`

`tools.py`:

```python
def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    if not old_str:
        return "Error: old_str is empty"
    if not os.path.isfile(path):
        return f"Error: {path} does not exist"
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Add surrounding lines to make it unique, "
            "or set allow_multi_edit to replace them all."
        )

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {path}"
```

`str_replace` takes a path, the old string to replace, and the new
string. If the old string is found, the tool calls `content.replace` and
writes the result back to the file.

The `Error:` branches are the important design choice. Zero matches
means the model is editing from memory rather than from the file. Two
matches means the edit is ambiguous. An empty `old_str` would match
between every character. A missing file is named. All of them come back
as the tool's *result string*, so the model reads the error, re-reads
the file and tries a more specific `old_str`. Nothing is raised here,
and anything that still is (a permission error, a path that is a
directory) becomes `Error: PermissionError: ...` through `run_tool`. The
session never dies over a bad edit. `allow_multi_edit` covers the
replace-all case, where every `hello world` becomes `goodbye`.

### 3. Encoding and line endings

Both tools open files with `encoding="utf-8"` and `newline=""`. The first
means a file with `é` or `✓` in it is written and read as UTF-8 on every
platform; Python's default on Windows is the console code page, which
raises `UnicodeEncodeError` on the first non-Latin character the model
writes. The second means no newline translation: a file with CRLF line
endings keeps them, and a one-line `str_replace` does not turn into a
whole-file diff because every line ending was rewritten.

### 4. The prompt tells the model how to edit

`llm.py`:

```python
Use write_file to create files and str_replace to edit them.
```

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
> write a new file called hello.txt with five hello worlds

  ┌──────────────────────────────────────────────┐
  │ write_file {"path": "hello.txt", "content": "hello world\nhello world\n..."}
  │ ──────────────────────────────────────────── │
  │ Wrote hello.txt                              │
  └──────────────────────────────────────────────┘

  agent

  Created hello.txt with five lines.

> replace every hello world with goodbye

  ┌──────────────────────────────────────────────┐
  │ read_file hello.txt                          │
  └──────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────┐
  │ str_replace {"path": "hello.txt", "old_str": "hello world", "new_str": "goodbye", "allow_multi_edit": true}
  │ ──────────────────────────────────────────── │
  │ Replaced 5 match(es) in hello.txt            │
  └──────────────────────────────────────────────┘
```

The second request uses replace-all, so every match is swapped. The model
reads the file, then calls `str_replace`. The new file contains five
`goodbye` lines. The harness is now a coding agent that can write files.

## Error handling

- `old_str` not in the file: `Error: old_str was not found in <path>`; the model re-reads and retries.
- `old_str` more than once without `allow_multi_edit`: `Error: old_str matches N times in <path>. ...`.
- Empty `old_str`: `Error: old_str is empty`. Missing file: `Error: <path> does not exist`.
- A directory, a read-only file: `Error: PermissionError: ...` (from `run_tool`).
- Everything from stage 3 (bad tool calls, ctrl-c, dead model calls, `/exit`) is unchanged.

## Gotchas

- No path is off limits. The agent can write anywhere you can. Stage 11
  asks before writes outside the project.
- `write_file` overwrites without asking and without a backup. Stage 33
  adds checkpoints.
- Bytes that are not valid UTF-8 in a file `str_replace` edits are
  replaced when read and therefore rewritten; do not edit binary files
  with it.
- `str_replace` with `old_str == new_str` reports a replacement and
  changes nothing.

## Files

```text
step_05_file_editing/
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── agent.py         the loop, unchanged
├── llm.py           the system prompt tells the model how to edit
├── skills.py        skill discovery, unchanged from stage 4
├── tools.py         the registry gains write_file and str_replace
├── ui.py            the presentation layer, unchanged
├── test_step.py     offline tests: write then replace; edits never raise; UTF-8 and CRLF; five tools
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## Test

`python -m pytest test_step.py` writes and edits temp files: the
ambiguous and replace-all cases, the empty `old_str`, missing file and
missing folder cases, a UTF-8 round trip with CRLF line endings through
`write_file`, `str_replace`, `read_file` and `bash`, and the registry.

## Diff from stage 4

```bash
diff ../step_04_skills/tools.py tools.py
diff ../step_04_skills/llm.py llm.py
```

## What the next step adds

Stage 6 attaches a fresh block of facts (date, git branch) to every
request without storing it in the transcript.

<!-- harness-learning-check -->
## Check your understanding

A replacement pattern matches twice. Why can applying it blindly be wrong?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

The intended edit may concern only one location. Inspect match rules, ambiguity handling and the resulting diff before accepting the change.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
