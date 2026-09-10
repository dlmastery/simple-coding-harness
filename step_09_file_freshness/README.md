# Step 9 - File freshness reminders

**New in this step:** when a file changes between model calls, the late
block tells the model to re-read it before editing.

```
<env>
time: 2026-09-10 14:02
git branch: main
</env>
<system-reminder>
These files changed since your last turn. Read them again before editing:
modified: harness/tools.py
</system-reminder>
```

## The bug this prevents

The model's picture of a file is whatever it last read. Then you fix a typo
in your editor, or a formatter runs, or a test writes a fixture. The model
does not know. Its next `str_replace` fails ("old_str not found"), or
worse, succeeds against text that is now wrong. Every real coding agent
has some version of this reminder; Claude Code's is the `<system-reminder>`
block this one is modelled on.

## How it works

`context.git_state()` takes a snapshot: for every path in
`git status --porcelain`, the status code *and an MD5 of the contents*.
The hash matters - a file that is already "modified" and gets modified
again looks identical to `git status` alone. Between calls the two
snapshots are diffed, and only paths whose entry moved are reported.
Reported once, then the baseline advances, so the model is not nagged.

It rides in the same late-injected block as step 8, for the same reason:
it changes every call and must not disturb the cached prefix.

## Run it

```bash
python -m harness
you> read harness/tools.py and wait
# ...now edit tools.py in your editor...
you> add a comment to the top of tools.py
```

The reminder appears in the dim panel, and the model re-reads before it
edits.

## Diff from step 8

```bash
diff ../step_08_late_injection/harness/context.py harness/context.py
```

Only `context.py` changed.
