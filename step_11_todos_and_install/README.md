# Step 11 - A plan the model cannot lose, and an installable command

**New in this step:** a `write_todos` tool whose list is re-injected into
every call, a checklist panel in the terminal, and a `pyproject.toml` so
`harness` runs from any directory.

```
<env>...</env>
<todos>
[x] Read the file
[~] Add the test
[ ] Run it
</todos>
```

## Why a todo tool

Long tasks drift. After twenty tool calls the plan the model wrote in turn
one is buried, and it starts improvising. Two decisions fix that:

1. **The list lives in a variable, not in the transcript.** `todos.TODOS`
   is module state. The tool *replaces* it wholesale each call, so there
   is exactly one current plan and no history of stale ones to confuse the
   model.
2. **It is injected in the late block on every call.** The same trick as
   the `<env>` block: the plan is the last thing the model reads before
   it acts, every time. The system prompt says so explicitly: "that block,
   not your memory of the transcript, is the truth about where you are."

The "exactly one `in_progress`" rule is enforced in code and returns an
error string, not a crash - the step 7 habit again. The in-progress item's
`active` form ("Adding the test") becomes the spinner label, so the
terminal tells you what the agent thinks it is doing.

## The UI intercepts one tool

`ui.tool()` now routes `write_todos` to a checklist panel instead of a raw
result box. It is the one place the UI knows a tool by name. Raw JSON of a
plan is never worth a person's eyes.

## Installable

```bash
pip install -e .        # or: uv pip install -e .
cd ~/some/other/project
harness
```

`[project.scripts] harness = "harness.agent:main"` is all it takes. Skills,
sessions and the git snapshot all key off the *current* directory, so the
same install serves every project.

## Run it

```bash
harness
you> add a --version flag to harness, with a test, and run the tests
```

The first tool call should be `write_todos`, and the panel updates as
items complete.

## Diff from step 10

```bash
diff -r ../step_10_sessions_and_rewind/harness harness
```

New: `todos.py`, `pyproject.toml`. Changed: `tools.py` (registry line),
`context.py` (todos in the late block), `prompts.py`, `agent.py` (spinner
label), `ui.py` (checklist panel).
