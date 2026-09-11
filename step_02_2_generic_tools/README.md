# Stage 2.2 - Generic tools (video 09:53 - 10:57)

> "In the next few commits, you'll see the power of just having a separate
> tools.py file."

The tool moves out of `llm.py` into `tools.py`, with two tables:

```python
TOOL_SCHEMAS = [ {...bash schema...} ]   # what the model sees
TOOLS = {"bash": bash}                   # what we run
```

and dispatch becomes one line:

```python
result = TOOLS[tool_call.function.name](**args)
```

The model's function name is a dictionary key; its JSON arguments are
keyword arguments. Nothing in `llm.py` knows which tools exist any more.

## Why this matters

"Tools are basically what gives agents capabilities. System prompts
instruct the model on how to do things; tools help the agent do more
outside its network weights." Every later stage that adds a capability -
read, write, edit, skills, todos, subagents - is one function and one
schema in this file.

## Diff from stage 2.1

```bash
diff ../step_02_1_bash_tool/llm.py llm.py
```
