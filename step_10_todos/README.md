# Stage 10 - Todos

A long task can be split into smaller subtasks. The agent then works
through them one by one.

**What this stage adds:** a `write_todos` tool, the list it writes, and a
`<todos>` block in the late injection so the plan is in front of the model
on every call.

```text
<env> ... </env>
<todos>
[x] Write hello.txt with five hello worlds
[~] Write a Python file that prints a star pattern
[ ] Write a Python file with the Fibonacci series
</todos>
```

## The code, piece by piece

### 1. The list and the tool

`harness/todos.py`:

```python
MARKS = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}

TODOS = []  # [{"content": ..., "activeForm": ..., "status": ...}]


def write_todos(todos):
    """Replace the whole list. Exactly one task may be in_progress."""
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be."

    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt():
    return "\n".join(f"{MARKS[t['status']]} {t['content']}" for t in TODOS)
```

The harness keeps a list of every task the agent wants to save. Each task
carries a status: pending, in_progress or completed. Every call to the
tool overwrites the previous todos with a new list of action items.
`TODOS[:] = todos` replaces the list wholesale, so there is exactly one
current plan and no stack of stale ones. The rule "exactly
one in progress" is enforced in code and returned as an error string, the
stage 5 habit.

```python
def active_form():
    """What the agent is doing right now, for the spinner."""
    for todo in TODOS:
        if todo["status"] == "in_progress":
            return todo["activeForm"]
    return "thinking"
```

Each item carries an `activeForm` ("Writing the star pattern") that the
loop shows as the spinner label:

`harness/agent.py`:

```python
            with ui.working(active_form()):
```

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
Keep exactly one task in_progress, mark it completed the moment it is finished,
and move the next one to in_progress in the same call. Skip the tool entirely
for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.
```

## Run it

```bash
harness
> create a todo list with three things: write hello.txt with five hello
  worlds, write a Python file that prints a star pattern, and write another
  with the Fibonacci series. then do them.
```

The agent creates the todos and keeps updating them as it works. Each
rewrite puts the whole list back in front of the model, so its tasks stay
close to its recent memory.

## Diff from stage 9

```bash
diff -r ../step_09_installable_command/harness harness
```

New: `todos.py`. Changed: `context.py`, `llm.py`, `tools.py` (registry
line), `agent.py` (spinner label).
