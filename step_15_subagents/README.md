# Stage 15 - Exploration subagents (video 41:57 - 45:37)

> "There's just one more thing left to do before we say this coding agent is
> quite minimal but also feature-rich: the concept of a sub agent."

New file `harness/subagent.py`; a `task` tool; `execute()` in `tools.py`
so the main loop and the subagent share one permission-checked executor.

```
main transcript                        subagent transcript (thrown away)
──────────────                         ─────────────────────────────────
user: explore this repo                system: you are an exploration agent...
assistant: task("What is this ...")    user: What is this project? ...
                                       assistant: bash(ls)  / read_file(...)  / bash(rg ...)
                                       tool: ...   (89 lines)
                                       assistant: "This project is ..."
tool: "This project is ..."     ◀───── only this crosses back
assistant: (summary for you)
```

## The four rules, in the video's words

1. **Own context.** "None of the chat context with the user that the user
   had with the main agent is ever shared with the sub agent. The sub
   agent truly is its own thing."
2. **Fewer tools.** "Every tool in the tool schema minus the ones we are
   withholding: task, write_todos, str_replace and write. We don't let it
   launch its own sub agents so that it's not a recursive thing. We just
   keep it to one sub agent depth."
3. **Same loop.** "We just do the call_llm function because it receives a
   list of messages and outputs a response, and also inputs the tool set."
   `task()` is the stage 2.4 loop pointed at a fresh list.
4. **Only the answer returns.** "The final thing that gets returned is the
   message.content. None of the tool calls of the sub agent ever get
   returned to the main agent."

Plus a turn cap: after twelve turns it returns whatever it last said,
marked partial.

`execute()` moves the permission check out of `agent.py` so the subagent
goes through exactly the same allow / ask / deny rules and the same
sandbox. "It's very easily extendable to parallel or multi-subagent
paradigms", but the video, and this stage, stop at one.

## Run it

```bash
harness
> use a sub agent to explore this repo and tell me what you find
```

The question the model writes for the subagent appears in a blue panel,
its tool calls indented under it, and then the main agent's summary.

## Diff from stage 14

```bash
diff -r ../step_14_compaction/harness harness
```

That is the end of the video: "We literally took a single API call, that's
where we began, and we built the entire thing."
