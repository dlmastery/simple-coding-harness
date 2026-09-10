# Step 7 - Editing tools, and errors the model can read

**New in this step:** `write_file`, `str_replace`, and an `execute()` that
never raises. The agent can now change code, not just read it.

## The edit tool

`str_replace(path, old_str, new_str)` swaps one exact string for another.
It is the workhorse edit primitive in every serious coding agent, and it
has one rule that does most of the work: **`old_str` must match exactly
once.** Zero matches means the model is editing from memory rather than
from the file. Two matches means the edit is ambiguous. Both come back as
an error string that tells the model what to do instead.

Why not a line-number tool? Because the model's idea of line numbers drifts
the moment it makes one edit. Exact text does not drift.

## Errors as results

Until now a bad tool call crashed the program. Look at `execute()`: every
way a call can go wrong now returns a *string* that goes back to the model
as the tool result:

| The model... | It gets back |
|--------------|--------------|
| sends broken JSON | `Error: arguments were not valid JSON (...)` |
| invents a tool name | `Error: no tool named 'x'. Available: ...` |
| passes the wrong arguments | `Error: wrong arguments for read_file (...)` |
| reads a missing file | `Error: read_file failed - FileNotFoundError: ...` |

The model reads the error, corrects itself, and tries again. This is the
single biggest robustness win in the series and it is fifteen lines.

## The schema helper grows up

`str_replace` has an optional boolean, so `schema()` now accepts a dict for
a parameter spec and a `required=` list. Everything from steps 3 to 6 still
uses the short string form.

## Run it

```bash
python -m harness
you> add a docstring to every function in harness/tools.py that lacks one
```

Watch it `read_file`, then a series of `str_replace` calls. Then
`git diff` to see the result. If it makes a mistake, tell it - the loop
carries the conversation, so "undo that last edit" works.

## Diff from step 6

```bash
diff -r ../step_06_skills/harness harness
```

Changed: `tools.py` (two tools, richer `schema()`, defensive `execute()`),
`prompts.py` (tells the model how to edit).
