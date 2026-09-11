# Stage 15 - Exploration subagents

One feature remains before this coding agent counts as minimal but
feature-rich: the subagent.

**What this stage adds:** a `task` tool that runs a fresh agent, with its
own context window and fewer tools, on one question and returns only its
answer. And `execute()`, so the main loop and the subagent share one
permission-checked path to the tools.

```text
main transcript                        subagent transcript (thrown away)
──────────────                         ─────────────────────────────────
user: explore this repo                system: you are an exploration agent...
assistant: task("What is this ...")    user: What is this project? ...
                                       assistant: bash(ls) / read_file(...) / bash(rg ...)
                                       tool: ...   (89 lines)
                                       assistant: "This project is ..."
tool: "This project is ..."     ◀───── only this crosses back
assistant: (summary for you)
```

## The code, piece by piece

### 1. Rule 2: which tools the subagent gets

`harness/subagent.py`:

```python
WITHHELD = {"task", "write_todos", "str_replace", "write_file"}
```

```python
def toolset():
    """Every tool schema except the withheld ones."""
    from .tools import TOOL_SCHEMAS

    return [s for s in TOOL_SCHEMAS if s["function"]["name"] not in WITHHELD]
```

The subagent's tool set is every tool in the tool schema minus the
withheld ones: task, write_todos, str_replace and write_file. It cannot
launch its own subagents, so there is no recursion. The harness stays one
subagent deep. Because those schemas are simply absent from the list it is offered, "cannot edit"
and "cannot recurse" are structural facts, not requests.

### 2. Rules 1, 3 and 4: the loop, pointed at a fresh list

`harness/subagent.py`:

```python
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
```

```python
    for _ in range(MAX_TURNS):
        fit(messages)  # its context can overflow too, and nobody compacts it

        with ui.working("subagent exploring"):
            message, usage = call_llm(messages, tools=toolset())  # rule 2
        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)
        report = message.content or report

        # rule 4: no tool calls means it has stopped looking and started answering
        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"

        for tool_call in message.tool_calls:
            # the same executor as the main loop: same permissions, same sandbox
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

- Rule 1: None of the chat context the user had with the main agent is
  shared with the subagent. Two messages, born here.
- Rule 3: The subagent reuses `call_llm`. It takes a list of messages and
  a tool set and returns one response. Compare with `agent.py`: call,
  append, execute, append. Same loop.
- Rule 4: Only the final `message.content` returns. None of the subagent's
  tool calls ever reach the main agent. `messages` goes out of scope at
  the `return`.

`MAX_TURNS` caps a runaway explorer; after twelve turns it returns what
it last said, marked partial.

### 3. One executor for both loops

`harness/tools.py`:

```python
def execute(tool_call):
    """Run one tool call through the permission layer. Returns (args, result).

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    args = json.loads(tool_call.function.arguments)
    action, reason = check(tool_call.function.name, args)
    if action == "deny":
        return args, f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return args, "The user denied this tool call."
    return args, TOOLS[tool_call.function.name](**args)
```

The permission block moves out of `agent.py` into this function, and the
main loop becomes:

`harness/agent.py`:

```python
            for tool_call in message.tool_calls:
                args, result = execute(tool_call)
                ui.tool(tool_call.function.name, args, result)
```

### 4. The tool the main agent sees

`harness/subagent.py`:

```python
        "name": "task",
        "description": (
            "Hand a self-contained exploration question to a fresh agent that "
            "has its own context window, and get back its findings. Use this "
```

The system prompt in `llm.py` tells the model when to use it. The model
should send a task subagent instead of grepping through the repo itself.
The subagent cannot see the conversation, so the question must stand
alone. The main agent does all editing itself.

## Run it

```bash
harness
> use a sub agent to explore this repo and tell me what you find
```

The main agent writes a description for the subagent: what the project
is, what the directory structure is, which technologies are used. The
subagent runs its tool calls and answers. The main agent then writes a
short summary from that answer. The question shows in a blue panel, the
subagent's tool calls indented beneath it, then the main agent's answer.

## Diff from stage 14

```bash
diff -r ../step_14_compaction/harness harness
```

New: `subagent.py`. Changed: `tools.py` (`task`, `execute`), `agent.py`,
`llm.py`, `ui.py` (`subagent` panel, nested indent).

The series began with a single API call. Fifteen stages later it is a
complete coding agent.
