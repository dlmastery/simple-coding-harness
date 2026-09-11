# Stage 13 - Readable todos and a real input line

A presentation stage between the sandbox and compaction. There is no
change to the loop, the tools or the context.

**What this stage adds:** the plan is drawn as a checklist instead of raw
tool output, and typing goes through prompt_toolkit instead of `input()`.

## The code, piece by piece

### 1. The checklist panel

`harness/ui.py`:

```python
    def tool(self, name, args, result):
        if name == "write_todos" and args.get("todos"):
            return self.todos(args["todos"])
```

```python
    def todos(self, todos):
        """The plan as a checklist. The raw tool output is never worth showing."""
        done = sum(1 for t in todos if t["status"] == "completed")
        rows = Table.grid(padding=(0, 1))
        rows.add_column(no_wrap=True)
        rows.add_column(overflow="fold")
        for todo in todos:
            style = TODO_STYLES[todo["status"]]
            rows.add_row(Text(MARKS[todo["status"]], style=style), Text(todo["content"], style=style))
```

This is the one place the UI knows a tool by name. A `write_todos` call
renders as `[x]` done (struck through), `[~]` in progress (bold), `[ ]`
pending, under a `todos 1/3` title.

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
    return SESSION.prompt(HTML(f"<prompt>{prompt}</prompt>"))
```

`input()` cannot edit a line that has wrapped past the screen width: the
terminal owns the wrapping. prompt_toolkit redraws the line itself, keeps
a history file across sessions, and `alt-enter` inserts a newline:

```python
@bindings.add("escape", "enter")
def _newline(event):
    """alt/option-enter starts a new line instead of sending the message."""
    event.current_buffer.insert_text("\n")
```

The fallback to `input()` lets `harness < script.txt` and the offline
tests run where there is no console.

`ui.ask`, `ui.pick` and `ui.approve` all go through `prompt.read()`, so
every place you type behaves the same.

## Diff from stage 12

```bash
diff -r ../step_12_sandbox/harness harness
```

New: `prompt.py`. Changed: `ui.py`, `pyproject.toml` (prompt-toolkit).
