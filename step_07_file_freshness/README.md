# Stage 7 - File freshness reminders (video 28:28 - 29:20)

> "You can alert the agent if a file has changed since it last read it and
> prompt it to read the file once again before making changes to it."

`context.py` gains a global dict `SEEN`; `tools.py` records into it.

```
read_file / write_file / str_replace  ──▶  SEEN[path] = mtime
next call: reminder()                 ──▶  any path whose mtime moved
                                            ──▶ <system-reminder> in the late block
```

## In the video's words

"We record the mtime whenever the agent reads or writes to this file. Then
on the next turn, we notice if any file has an updated mtime. This way we
can easily catch if a file was updated since the agent last interacted
with it." The note "comes through as a system reminder and it says these
files changed on disk since you read them".

The bug this prevents: the model's picture of a file is whatever it last
read. You fix a typo in your editor, a formatter runs, a test writes a
fixture - the model does not know, and its next `str_replace` either fails
or lands on text that is now wrong.

It uses the stage 6 mechanism unchanged: the warning is part of the
injected block, so it costs nothing in the prefix and disappears once the
file is re-read.

## Diff from stage 6

```bash
diff ../step_06_late_injection/context.py context.py
diff ../step_06_late_injection/tools.py tools.py   # three note_seen() calls
```
