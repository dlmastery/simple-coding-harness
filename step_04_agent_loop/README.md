# Step 4 - The agent loop

**New in this step:** tool results go *back to the model*, and the
conversation persists across turns. This is the step where it becomes an
agent.

```
              ┌──────────────────────────────────────────────┐
              │                                              │
you ──▶ messages ──▶ model ──▶ tool calls? ──yes──▶ run tools, append results
                                   │
                                   no
                                   ▼
                                answer
```

## The two loops

- **Outer loop** - one iteration per thing you type. `messages` is never
  reset, so the model remembers the conversation.
- **Inner loop** - one iteration per model call. If the reply contains tool
  calls, each one is executed and its result appended as a message with
  `role: "tool"`, then the model is called again. When a reply has no tool
  calls, the turn is over.

Everything in the rest of this series - permissions, sandboxing, compaction,
subagents - is a modification of these ~15 lines. The subagent in step 14 is
literally this inner loop pointed at a different list.

## Two details that matter

1. **The assistant message with tool calls must be stored** (`as_dict`). The
   API rejects a `tool` message that does not follow the assistant message
   that requested it. Drop it and you get a 400.
2. **Results are tied to calls by id.** With several tool calls in one
   reply, the ids are how the model knows which output belongs to which call.

## Run it

```bash
python agent.py
you> what does the biggest .py file in this folder do?
```

Watch it run `ls`, then `read_file`, then answer - several model calls for
one question. That is the loop working.

## What is still rough

Tool output floods the screen, there is no spinner, no token count, and a
tool error crashes the whole program. Step 5 is about the terminal; step 7
makes errors survivable.

## Diff from step 3

```bash
diff ../step_03_tool_registry/agent.py agent.py
```
