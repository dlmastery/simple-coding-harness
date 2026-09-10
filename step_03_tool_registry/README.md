# Step 3 - A tool registry

**New in this step:** `read_file`, and a table that makes the next tool a
one-liner.

```python
TOOLS = {
    "bash":      (bash,      schema(...)),
    "read_file": (read_file, schema(...)),
}
```

## Why a registry

In step 2 the tool name was hard-coded in the dispatch. With two tools you
would write an `if/elif`; with seven (where this series ends) that is a
mess. So the model's `call.function.name` becomes a dictionary key, the
JSON arguments become `**kwargs`, and `execute()` is the only place a tool
call turns into a Python call. Every later feature that needs to see every
tool call - permissions, sandboxing, subagents - hooks into that one
function.

## Why `read_file` when `cat` exists

It does the same thing, but it teaches the model something: a dedicated tool
with a clear description gets used more reliably than a shell command the
model has to remember to reach for. Tool descriptions are prompts.

## Run it

```bash
python agent.py
you> read agent.py and tell me what TOOLS contains
```

Still single-shot: the model gets one reply, and you see whichever tool it
chose. It still does not get the result back. Next step.

## Diff from step 2

```bash
diff ../step_02_first_tool/agent.py agent.py
```
