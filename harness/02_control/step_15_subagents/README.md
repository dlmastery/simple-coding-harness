# Stage 15 - Exploration subagents

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Keep actions within limits**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 14 - Compaction and context overflow](../step_14_compaction/README.md). Next: [Step 16 - The same harness on the Claude Agent SDK](../../03_adapters/step_16_claude_agent_sdk/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

One feature remains before this coding agent counts as minimal but
feature-rich: the subagent.

**What this stage adds:** a `task` tool that runs a fresh agent, with its
own context window and fewer tools, on one question and returns only its
answer. And `execute()`, the one permission-checked path to the tools,
which the main loop and the subagent share.

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

## Why: exploring is expensive, and the answer is small

"Where is the retry logic?" costs the main agent ten to twenty tool calls -
`rg`, `ls`, three `cat`s - and every one of those results sits in the
transcript for the rest of the session, stripped to a stub after the turn
(stage 14) but never gone. Ten such questions and the context is half
noise, most of it about files the model looked at once and rejected. The
finding itself is three lines. A subagent spends those tool calls in a
context window that is thrown away, and the main transcript gains one tool
result of about 150 words. The main agent keeps its context for the work.

## Files

```text
step_15_subagents/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop hands every tool call to tools.execute()
│   ├── commands.py      slash commands, unchanged
│   ├── compact.py       the compaction agent, unchanged
│   ├── config.py        settings from the env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged
│   ├── history.py       tool output caps, unchanged
│   ├── llm.py           the system prompt explains when to delegate a task
│   ├── permissions.py   the rule table, unchanged
│   ├── prompt.py        the input line, unchanged
│   ├── sandbox.py       the OS sandbox, unchanged
│   ├── session.py       transcripts on disk, unchanged
│   ├── skills.py        skills, unchanged
│   ├── subagent.py      task(): a fresh agent with toolset() and MAX_TURNS
│   ├── todos.py         the plan, unchanged
│   ├── tools.py         gains the task tool; run_tool becomes execute(tool_call, allowed)
│   └── ui.py            the subagent() panel and nested tool panels
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: toolset, isolation, the allowed set, failures inside the subagent, cutoff, bad tool calls
├── pyproject.toml       package metadata; version 0.15.0
└── README.md            this file
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
subagent deep.

Withholding a schema is not enough on its own: a model can call a tool it
was never shown, just by naming it, and the OpenAI-style API passes that
call through. So the names of the offered schemas are also handed to the
executor as the `allowed` set (section 3), and a call outside it is
denied. With both, "cannot recurse" and "cannot use the write tools" are
enforced by the harness, not requested of the model.

### 2. Rules 1, 3 and 4: the loop, pointed at a fresh list

`harness/subagent.py`:

```python
    offered = toolset()
    allowed = {s["function"]["name"] for s in offered}  # what it may run == what it was shown

    # rule 1: two messages, born here, dead at the return
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
```

```python
    for _ in range(MAX_TURNS):
        fit(messages)  # its context can overflow too, and nobody compacts it

        try:
            with ui.working("subagent exploring"):
                message, usage = call_llm(messages, tools=offered)  # rule 2
        except (openai.APIError, RuntimeError) as failure:
            # its failure is a result for the main agent, never a crash of the session
            report = f"(the subagent's model call failed: {failure})" + (f"\n\nPartial findings:\n\n{report}" if report else "")
            return report
        messages.append(entry(message))
        ui.usage(usage)
        report = message.content or report

        # rule 4: no tool calls means it has stopped looking and started answering
        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"

        for tool_call in message.tool_calls:
            # the same executor as the main loop: same permissions, same sandbox
            args, result = execute(tool_call, allowed)
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

- Rule 1: None of the chat context the user had with the main agent is
  shared with the subagent. Two messages, born here.
- Rule 3: The subagent reuses `call_llm`. It takes a list of messages and
  a tool set and returns one response. Compare with `agent.py`: call,
  append (`entry()`, so provider extras are not echoed back), execute,
  append. Same loop.
- Rule 4: Only the final `message.content` returns. None of the subagent's
  tool calls ever reach the main agent. `messages` goes out of scope at
  the `return`.

`MAX_TURNS` caps a runaway explorer; after twelve turns it returns what
it last said, marked partial. A model call that fails inside the subagent
(a rate limit, an empty reply) also comes back as text, with whatever it
had found so far - `task` is a tool, and a tool returns a string.

### 3. One executor for both loops

Stage 14's `run_tool` becomes `execute`, with one new parameter:

`harness/tools.py`:

```python
def execute(tool_call, allowed=None):
    """Turn one tool call into (args, result). Never raises: whatever goes
    wrong becomes the result string, so the model reads it and tries again.

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. `allowed` is the
    set of tool names the caller offered; a call outside it is denied, so a
    subagent cannot run a withheld tool just by naming it.
    """
```

```python
    if allowed is not None and name not in allowed:  # offered set == executable set
        action, reason = "deny", f"{name} is not available to this agent"
    elif name not in TOOLS:  # a name that is not in the table
        return args, f"Error: no tool named {name!r}."
    else:
        action, reason = check(name, args)
    if action == "deny":
        return args, f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return args, "The user denied this tool call."
```

The main loop passes no `allowed` (it may use every tool in `TOOLS`) and
becomes:

`harness/agent.py`:

```python
                for tool_call in message.tool_calls:
                    args, result = execute(tool_call)
                    ui.tool(tool_call.function.name, args, result)
```

Everything `execute` does for the main agent it does for the subagent:
the JSON guard, the rule table, the approval prompt, the sandbox around
`bash`, the `Error:` result for a tool that raises. A subagent is fenced
in by exactly the same rules; it is not a way around them.

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

bash / PowerShell:

```bash
harness
> use a sub agent to explore this repo and tell me what you find
```

The main agent writes a description for the subagent: what the project
is, what the directory structure is, which technologies are used. The
subagent runs its tool calls and answers. The main agent then writes a
short summary from that answer.

### Expected output

```text
  ┌─ subagent · own context ────────────────────────────────────┐
  │ Explore the repository in the current directory. Report:    │
  │ what the project is, the directory layout, the languages    │
  │ and frameworks used, and how to run it. Cite file paths.    │
  └─────────────────────────────────────────────────────────────┘

      ┌────────────────────────────────────────────────────────┐
      │ bash ls -la && cat pyproject.toml                      │
      │ ────────────────────────────────────────────────────── │
      │ harness/  test_step.py  pyproject.toml  README.md ...  │
      └────────────────────────────────────────────────────────┘

      ┌────────────────────────────────────────────────────────┐
      │ read_file harness/agent.py                             │
      │ ────────────────────────────────────────────────────── │
      │ """Stage 15 - the loop hands every tool call to ...    │
      └────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │ task Explore the repository in the current directory...     │
  │ ─────────────────────────────────────────────────────────── │
  │ A Python package `harness` (pyproject.toml:1) exposing a    │
  │ `harness` command. Entry point harness/agent.py:main ...    │
  └─────────────────────────────────────────────────────────────┘

  agent
  This is stage 15 of a coding-agent series: a Python package ...
```

The question shows in a blue panel, the subagent's tool calls indented
beneath it, then the `task` result as an ordinary tool panel, then the
main agent's answer. The muted `prompt · completion` line under each
call, and the totals printed when you leave, include the subagent's
calls - they are real cost, just not context the main agent carries.

## Error handling

- A subagent tool call that fails - a missing file, broken JSON arguments,
  a command that times out - is an `Error:` result inside the subagent's
  own transcript; it reads it and carries on, and the main agent never
  sees it.
- A subagent that names a withheld tool gets
  `Blocked by policy: write_file is not available to this agent`.
- A model call that fails inside the subagent ends the task with
  `(the subagent's model call failed: ...)` plus any partial findings;
  the main agent reads that as the tool result and decides what to do.
- Twelve turns without a final answer: `(stopped after 12 turns, before
  finishing. Partial findings below.)`.
- ctrl-c while the subagent runs ends the main agent's turn: the pending
  `task` call is answered with `(interrupted before this tool ran)` and
  the prompt comes back.
- Everything from stage 14 still holds for the main loop: `Error:`
  results, capped output, compaction, `model call failed: ...`. To leave:
  `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at the prompt.

## Gotchas / What this is not

- "The subagent only reads" is enforced for the write tools, not for
  `bash`. It keeps `bash`, and stage 11's rules send `sed -i`,
  `python -c ...` and any allow-listed command with a redirection
  (`echo x > file`) to the approval prompt - so a write from a subagent is
  a prompt you answer, not something the harness forbids. Say no.
- Approval prompts from a subagent look like the main agent's. The
  indented tool panels above the prompt are the only hint which one is
  asking.
- The subagent shares the process: the same cwd, `ui` totals, `SPILLS`
  temp files, `TODOS` (which it cannot change) and the same sandbox. Only
  the transcript is separate - and it is not saved. `--resume` replays
  the `task` call and its report; the subagent's own tool calls are gone,
  and `--debug` never showed them.
- The subagent's context can overflow too. `fit` blanks its tool results
  when a request gets too big; nothing compacts it. A question that needs
  more than twelve turns of reading should be two questions.
- Subagents run one at a time, on the main thread. Parallel tool calls
  are stage 22.
- On Windows the tool named `bash` still runs `cmd.exe` (stage 12), for
  the subagent as for the main agent.

## What the next stage adds

The series began with a single API call. Fifteen stages later it is a
complete coding agent: tools, skills, sessions, a plan, permissions, a
sandbox, compaction and subagents. What it does not yet have is what the
following stages add: an SDK port (16-19), OpenRouter routing (20),
streaming and a headless mode (21), parallel tool calls (22), hooks and
memory later on.

## Diff from stage 14

```bash
diff -r ../step_14_compaction/harness harness
```

New: `subagent.py`. Changed: `tools.py` (`task`, `execute` with
`allowed`), `agent.py`, `llm.py`, `ui.py` (`subagent` panel, nested
indent).

<!-- harness-learning-check -->
## Check your understanding

A subagent has a separate conversation. Are shared files therefore isolated?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

No. Context separation and filesystem isolation are different properties. Inspect the allowed tools and actual workspace boundaries.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
