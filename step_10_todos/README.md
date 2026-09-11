# Stage 10 - Todos (video 29:26 - 31:39)

> "When you give an agent a long task, it can split that task into smaller
> subtasks and work through them one by one."

New file `harness/todos.py`: a `write_todos` tool and the list it writes.
The list is shown to the agent through the late block from stage 6.

```
<env> ... </env>
<todos>
[x] Write hello.txt with five hello worlds
[~] Write a Python file that prints a star pattern
[ ] Write a Python file with the Fibonacci series
</todos>
```

## In the video's words

- "I keep a list of every task the agent wants to save and each task
  carries a status: in progress, completed, or pending."
- "Whenever this tool is called, the agent has to overwrite previous
  to-dos by writing a new list of action items." The tool *replaces* the
  list; there is one current plan, never a stack of stale ones. Exactly one
  item may be in progress, and its `activeForm` becomes the spinner label.
- "The way existing todos are shown to the agent is once again using our
  late injection feature." `context.py` appends a `<todos>` block after
  `<env>`, so "the LLM will always have access to it after each message".

The system prompt tells the model when to plan (multi-step tasks), when
not to (single steps: "it is noise there"), and that the injected block,
not the transcript, "is the truth about where you are".

## Run it

```bash
harness
> create a todo list with three things: write hello.txt with five hello
  worlds, write a Python file that prints a star pattern, and write another
  with the Fibonacci series. then do them.
```

"It created the to-dos and it keeps updating them as it retrieves them and
rewrites them."

## Diff from stage 9

```bash
diff -r ../step_09_installable_command/harness harness
```

New: `todos.py`. Changed: `context.py` (the `<todos>` block), `llm.py`
(the planning instructions), `tools.py` (registry), `agent.py` (spinner).
