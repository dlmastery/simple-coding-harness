# Stage 10 - Todos

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Keep actions within limits**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 9 - An installable command](../step_09_installable_command/README.md). Next: [Stage 11 - Tool permissions](../step_11_permissions/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

A long task can be split into smaller subtasks. The agent then works
through them one by one.

**What this stage adds:** a `write_todos` tool, the list it writes, and a
`<todos>` block in the late injection so the plan is in front of the model
on every call. The list is validated before it is stored and rebuilt from
the transcript on `--resume`, `/sessions` and `/rewind`.

```text
<env> ... </env>
<todos>
[x] Write hello.txt with five hello worlds
[~] Write a Python file that prints a star pattern
[ ] Write a Python file with the Fibonacci series
</todos>
```

## Why: a long task loses its place

Give the stage 9 agent "write hello.txt, then a star pattern, then
fibonacci" and watch what happens after the second file: twenty tool
results later the original list is far up the transcript, and the model
either stops early ("done!") or does the star pattern twice. Every model
behaves like this once the instruction is buried. A plan that is re-shown
on every call is the fix: the model reads `[x] [~] [ ]` right before it
acts, and the harness knows what to put on the spinner.

## Files

```text
step_10_todos/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop, with the spinner showing the active todo
│   ├── commands.py      redraw() rebuilds the plan from the transcript it shows
│   ├── config.py        settings from the env or ~/.simple-harness/env
│   ├── context.py       the late block gains the <todos> list
│   ├── llm.py           the system prompt explains when to plan with write_todos
│   ├── session.py       transcripts on disk, unchanged
│   ├── skills.py        skills, unchanged
│   ├── todos.py         the plan: TODOS, validate(), write_todos(), restore()
│   ├── tools.py         the registry gains write_todos
│   └── ui.py            the presentation layer, unchanged
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: write_todos validates and restores; bad tool calls; utf-8
├── pyproject.toml       package metadata; version 0.10.0
└── README.md            this file
```

## The code, piece by piece

### 1. The list and the tool

`harness/todos.py`:

```python
MARKS = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}
FIELDS = ("content", "activeForm", "status")

TODOS = []  # [{"content": ..., "activeForm": ..., "status": ...}]
```

```python
def write_todos(todos):
    """Replace the whole list. At most one task may be in_progress.

    Checked before the assignment: a bad list is refused and the old plan
    stays, so the block injected every turn can never break.
    """
    problem = validate(todos)
    if problem:
        return problem
    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt():
    return "\n".join(f"{MARKS.get(t.get('status'), '[?]')} {t.get('content', '')}" for t in TODOS)
```

The harness keeps a list of every task the agent wants to save. Each task
carries a status: pending, in_progress or completed. Every call to the
tool overwrites the previous todos with a new list of action items.
`TODOS[:] = todos` replaces the list wholesale, so there is exactly one
current plan and no stack of stale ones.

The list is checked *before* it is stored:

```python
def validate(todos):
    """The first thing wrong with a list, as an error string, or None."""
    if not isinstance(todos, list):
        return "Error: todos must be a list."
    for i, todo in enumerate(todos):
        if not isinstance(todo, dict) or any(field not in todo for field in FIELDS):
            return f"Error: item {i} needs content, activeForm and status."
        if todo["status"] not in MARKS:
            return f"Error: item {i} has status {todo['status']!r}; use pending, in_progress or completed."
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be."
    return None
```

Order matters here. The plan is rendered into every request, so a list
with a status the marks table does not know (`"done"`) would have raised
on every call for the rest of the session. Refusing it as an error string,
the stage 5 habit, keeps the old plan in place and lets the model fix its
call. "At most one in progress" is enforced the same way.

```python
def active_form():
    """What the agent is doing right now, for the spinner."""
    for todo in TODOS:
        if todo.get("status") == "in_progress":
            return todo.get("activeForm") or "working"
    return "thinking"
```

Each item carries an `activeForm` ("Writing the star pattern") that the
loop shows as the spinner label:

`harness/agent.py`:

```python
                    with ui.working(active_form()):
```

The plan lives in a variable, not in the transcript, so a resumed or
rewound chat would start with an empty plan while the transcript talks
about one. `restore` walks the transcript back to the last `write_todos`
call and rebuilds the list from its arguments:

`harness/todos.py`:

```python
def restore(messages):
    """Rebuild the list from the last write_todos in a transcript (resume, rewind, /sessions)."""
    TODOS.clear()
    for message in reversed(messages):
        for call in message.get("tool_calls") or []:
            if call["function"]["name"] == "write_todos":
```

`agent.py` calls it on `--resume`, and `commands.redraw` - the one place
`/rewind` and `/sessions` both go through - calls it too, so the plan on
screen and the plan the model sees are always the same one.

### 2. The plan is shown through the late block

`harness/context.py`:

```python
def todos_note():
    plan = todos_prompt()
    return f"\n<todos>\n{plan}\n</todos>" if plan else ""
```

```python
            "</env>" + todos_note() + changes_note()
```

The existing todos reach the agent through the late injection. The
current list is appended to the late block, so the model has access to it
after each message. The plan lives in a variable, not in the transcript.
Twenty tool calls later it is still the last thing the model reads before
it acts.

### 3. The prompt tells the model when to plan

`harness/llm.py`:

```python
For any task that takes more than one step, call write_todos first and plan it
out. Send the whole list every time you call it - it replaces the old one.
Keep at most one task in_progress, mark it completed the moment it is finished,
and move the next one to in_progress in the same call. Skip the tool entirely
for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.
```

## Run it

bash:

```bash
harness
> create a todo list with three things: write hello.txt with five hello
  worlds, write a Python file that prints a star pattern, and write another
  with the Fibonacci series. then do them.
```

PowerShell: the same; `harness` is on the PATH once `pip install -e .` has
run from this directory.

### Expected output

```text
> create a todo list with three things: ...

  ┌─ late injection ─────────────────────────┐
  │ <env> ... </env>                          │
  └───────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │ write_todos [{"content": "Write hello.txt", ...              │
  │ ──────────────────────────────────────────────────────────── │
  │ [~] Write hello.txt with five hello worlds                   │
  │ [ ] Write a Python file that prints a star pattern           │
  │ [ ] Write a Python file with the Fibonacci series            │
  └──────────────────────────────────────────────────────────────┘

  ┌─ late injection ─────────────────────────┐
  │ <env> ... </env>                          │
  │ <todos>                                   │
  │ [~] Write hello.txt with five hello worlds│
  │ [ ] Write a Python file that prints ...   │
  │ </todos>                                  │
  └───────────────────────────────────────────┘
  ⠋ Writing hello.txt                          <- the spinner label
```

The agent creates the todos and keeps updating them as it works. Each
rewrite puts the whole list back in front of the model, so its tasks stay
close to its recent memory. Stage 13 draws the list as a checklist instead
of raw tool output.

## Error handling

- A `write_todos` call with a wrong status, a missing field or a list that
  is not a list gets `Error: item 0 ...` back and the old plan stays.
- Everything from stage 9 still holds: a bad tool call is an `Error:`
  result, a dead model call ends the turn, ctrl-c ends the turn, `/exit`
  or ctrl-d (ctrl-z then enter on Windows) leaves.

## Gotchas / What this is not

- The plan is only as good as the model's discipline: nothing forces it to
  call `write_todos` again after finishing a task. The system prompt asks;
  the injected block reminds.
- `TODOS` is process memory. It is rebuilt from the transcript when a chat
  is reopened, so a plan written in a chat that was never saved is gone.

## What the next stage adds

Stage 11 puts a permission check in front of every tool call, so `rm -rf`
is refused and `python -c` asks first.

## Diff from stage 9

```bash
diff -r ../step_09_installable_command/harness harness
```

New: `todos.py`. Changed: `context.py`, `llm.py`, `tools.py` (registry
line), `agent.py` (spinner label).

<!-- harness-learning-check -->
## Check your understanding

A todo item says done. What else establishes that the work is complete?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

The required output and its check. A todo is coordination state, not independent evidence of success.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
