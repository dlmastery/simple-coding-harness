# Stage 6 - Late injection (video 26:37 - 28:24)

> "Sometimes we want to grab additional system level information right
> before we invoke the LLM call. That is injection."

New file `context.py`, and one changed line in `agent.py`:

```python
message, usage = call_llm(messages + [reminder()])
```

`reminder()` builds a small `<env>` block: the current time and the git
branch. It is appended to the *request*, at the very end, and never to
`messages`.

## Why the end, and why not stored

"We must always paste these injections at the very bottom of the messages
list because the date changes with every single message. So if you put it
at the top your prefix keeps breaking and you never hit the prefix cache
often enough to actually save money."

And: "We never touch the messages array itself. So in future turns, the
old dates and the old git statuses never get shown to the agent." One
fresh block per call, no stale copies in the transcript.

The offline test checks both: the block is the last item of every request,
and the stored prefix of request two equals request one minus its block.

## What this enables

"Now that we have built that block, we can do a lot more with it." Stage 7
adds file-change warnings to it; stage 10 adds the todo list.

## Diff from stage 5

```bash
diff ../step_05_file_editing/agent.py agent.py
cat context.py
```
