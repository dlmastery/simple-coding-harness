# Stage 13 - Readable todos and a real input line

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Keep actions within limits**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 12 - An OS sandbox for bash](../step_12_sandbox/README.md). Next: [Stage 14 - Compaction and context overflow](../step_14_compaction/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

A presentation stage between the sandbox and compaction. There is no
change to the loop, the tools or the context.

**What this stage adds:** the plan is drawn as a checklist instead of raw
tool output, and typing goes through prompt_toolkit instead of `input()`.

## Why: you cannot read the raw plan, and you cannot edit a long line

Stage 10 prints a `write_todos` call as any other tool: the JSON arguments
in the header and `[x] ... [~] ...` as the result. After the third
update nobody reads it. And `input()` cannot edit a line that has wrapped
past the screen width - the terminal owns the wrapping and readline
cannot see it - so a two-line request has to be retyped after one typo.
Both are the harness getting in the way of the person using it.

## Files

```text
step_13_readable_todos_input_line/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop, unchanged from stage 12
│   ├── commands.py      slash commands, unchanged
│   ├── config.py        settings from the env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged
│   ├── llm.py           call_llm, unchanged
│   ├── permissions.py   the rule table, unchanged
│   ├── prompt.py        the input line: prompt_toolkit read() with history
│   ├── sandbox.py       the OS sandbox, unchanged
│   ├── session.py       transcripts on disk, unchanged
│   ├── skills.py        skills, unchanged
│   ├── todos.py         the plan, unchanged
│   ├── tools.py         tools, unchanged
│   └── ui.py            todos render as a checklist; input via prompt.read()
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: the checklist; a refused plan; the input line; an empty line
├── pyproject.toml       package metadata; version 0.13.0, adds prompt-toolkit
└── README.md            this file
```

## The code, piece by piece

### 1. The checklist panel

`harness/ui.py`:

```python
    def tool(self, name, args, result):
        # the one place the UI knows a tool by name - and only when the plan was accepted
        if name == "write_todos" and args.get("todos") and not result.startswith("Error"):
            return self.todos(args["todos"])
```

```python
    def todos(self, todos):
        """The plan as a checklist. The raw tool output is never worth showing."""
        done = sum(1 for t in todos if t.get("status") == "completed")
        rows = Table.grid(padding=(0, 1))
        rows.add_column(no_wrap=True)
        rows.add_column(overflow="fold")
        for todo in todos:
            style = TODO_STYLES.get(todo.get("status"), MUTED)
            rows.add_row(Text(MARKS.get(todo.get("status"), "[?]"), style=style), Text(str(todo.get("content", "")), style=style))
```

This is the one place the UI knows a tool by name. A `write_todos` call
renders as `[x]` done (struck through), `[~]` in progress (bold), `[ ]`
pending, under a `todos 1/3` title.

The check on `result` matters: `write_todos` refuses a bad list with an
`Error: item 0 ...` string (stage 10), and the panel must not then show
the refused plan as if it had been accepted. On an error the ordinary tool
panel is drawn, error text and all, so you see what the model saw. The
`.get(..., "[?]")` lookups are the same idea one level down: a status the
table does not know is drawn as `[?]`, never raised.

### 2. The input line

`harness/prompt.py`:

```python
def read(prompt="> "):
    """Read one message. Raises EOFError on ctrl-d, like input() does.

    Without a real terminal (piped stdin, a plain Windows pipe, tests) the
    editor cannot start, so fall back to input() rather than refuse to run.
    """
    global SESSION
    if not sys.stdin.isatty():
        return input(prompt)
    if SESSION is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        try:
            SESSION = PromptSession(history=FileHistory(str(HISTORY)), key_bindings=bindings, style=STYLE)
        except Exception:  # noqa: BLE001 - e.g. NoConsoleScreenBufferError on Windows
            SESSION = False
    if not SESSION:
        return input(prompt)
    return SESSION.prompt(HTML(f"<prompt>{html.escape(prompt)}</prompt>"))
```

`input()` cannot edit a line that has wrapped past the screen width: the
terminal owns the wrapping. prompt_toolkit redraws the line itself, keeps
a history file across sessions (`~/.simple-harness/history`), and
`alt-enter` inserts a newline:

```python
@bindings.add("escape", "enter")
def _newline(event):
    """alt/option-enter starts a new line instead of sending the message."""
    event.current_buffer.insert_text("\n")
```

The fallback to `input()` lets `harness < script.txt` and the offline
tests run where there is no console.

`ui.ask`, `ui.pick` and `ui.approve` all go through `prompt.read()`, so
every place you type behaves the same. `ui.ask` returns `None` when you
leave (ctrl-d, ctrl-c) and `""` for an empty line; the loop leaves on the
first and ignores the second, so an accidental Enter on an empty line -
easy to do once alt-enter exists - does not end the chat.

## Run it

bash / PowerShell:

```bash
harness
> create a todo list with three things: write hello.txt with five hello
  worlds, write a Python file that prints a star pattern, and write another
  with the Fibonacci series. then do them.
```

Type the first line, press alt-enter (option-enter on a Mac) for the next
ones, enter to send. Press up at the prompt to get it back next session.

### Expected output

```text
  ┌─ todos 0/3 ────────────────────────────────────────────┐
  │ [~] Write hello.txt with five hello worlds              │
  │ [ ] Write a Python file that prints a star pattern      │
  │ [ ] Write a Python file with the Fibonacci series       │
  └─────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────┐
  │ write_file hello.txt                                     │
  │ ──────────────────────────────────────────────────────── │
  │ Wrote hello.txt                                          │
  └──────────────────────────────────────────────────────────┘

  ┌─ todos 1/3 ────────────────────────────────────────────┐
  │ [x] Write hello.txt with five hello worlds              │
  │ [~] Write a Python file that prints a star pattern      │
  │ [ ] Write a Python file with the Fibonacci series       │
  └─────────────────────────────────────────────────────────┘
```

## Error handling

- A refused `write_todos` (bad status, missing field) is shown as a normal
  tool panel with the `Error: item 0 ...` text, not as a checklist.
- Everything from stage 12 still holds: `Error:` results for bad calls,
  the sandbox and the timeout for `bash`, ctrl-c ends the turn.
- To leave: `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at
  the prompt. An empty line does nothing.

## Gotchas / What this is not

- Under Git Bash's mintty on Windows, and under any pipe, `stdin.isatty()`
  is false and the line editor is not used: you get plain `input()`,
  no history, no alt-enter. Windows Terminal, PowerShell and cmd.exe give
  the full editor.
- With the `input()` fallback on Windows, ctrl-d does nothing; ctrl-z
  then enter is end-of-file there.
- History is one file for every project, `~/.simple-harness/history`.

## What the next stage adds

Stage 14 keeps the transcript inside the context window: tool output is
capped and stripped, and a compaction agent summarises the past when the
prompt grows past 85% of the window.

## Diff from stage 12

```bash
diff -r ../step_12_sandbox/harness harness
```

New: `prompt.py`. Changed: `ui.py`, `pyproject.toml` (prompt-toolkit).
