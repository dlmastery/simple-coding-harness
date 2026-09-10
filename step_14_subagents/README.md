# Step 14 - Exploration subagents

**New in this step:** a `task` tool. The agent hands a question to a fresh
agent with its own context window and gets back only the answer.

```
main transcript                     subagent transcript (thrown away)
──────────────                      ─────────────────────────────────
user: where is auth checked?        system: you are an explorer...
assistant: task("find where...")    user: find where auth is checked
                                    assistant: bash(rg "auth")        ← 4k tokens of grep
                                    tool: ...
                                    assistant: read_file(...)         ← 6k tokens of file
                                    tool: ...
                                    assistant: "auth.py:41, called from api.py:12"
tool: "auth.py:41, called from..."  ◀── only this crosses back
assistant: (edits auth.py)
```

## Why this is the last step

Step 13 was about throwing context away *after* it has been spent. A
subagent spends it somewhere that is thrown away *by design*. Exploring a
codebase costs tens of thousands of tokens of tool output to produce a
hundred-word answer; with a subagent the main transcript pays for the
hundred words. That is the difference between an agent that can work in a
large repo and one that compacts every three turns.

## The four rules

`subagent.py` is short because it is only these:

1. **Starts empty.** Two messages: its own system prompt and the question.
   Not a copy of the caller's history - it cannot see the conversation, so
   the main agent is told to write questions that stand alone.
2. **Holds every tool but four.** `task` (no recursion), `write_todos`
   (the plan belongs to the main agent), `write_file` and `str_replace`
   (read-only is a *structural* fact, not a polite request). These tools
   are simply absent from the schema list it is offered.
3. **Runs the same loop.** Compare `task()` with `turn()` in `agent.py`:
   call, append, execute, append, repeat. It even goes through the same
   `execute()`, so the same permission rules and sandbox apply. A subagent
   is a second caller, not a privileged one.
4. **Only the last message comes back.** `messages` goes out of scope at
   the `return`. One string survives.

Plus a turn cap: a runaway explorer is worse than a missing answer, so
after 12 turns it returns whatever it last said, marked as partial.

## In the terminal

The subagent's question shows in a blue-bordered panel and its tool calls
are indented under it, so you can see the exploration happen even though
the main agent never will.

## Run it

```bash
python -m harness
you> how does a tool call get from the model to the permission check? then add a log line at that point
```

The model should dispatch a `task`, watch it grep and read in the indented
panels, receive a short report, and then do the edit itself.

## Diff from step 13

```bash
diff -r ../step_13_context_management/harness harness
```

New: `subagent.py`. Changed: `tools.py` (one registry line), `ui.py`
(`subagent` panel, `nested=` indent), `prompts.py`.

## Where to go from here

You now have every mechanism a production coding agent is built from. The
ones this series leaves out are engineering, not ideas: streaming output,
parallel tool calls, an MCP client for external tools, hooks that run
before and after tools, and a `--print` mode for scripting. Each is a
small diff on the files you already know.
