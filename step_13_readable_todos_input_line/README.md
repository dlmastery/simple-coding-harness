# Stage 13 - Readable todos and a real input line

A presentation stage from the reference commits, between the sandbox and
compaction.

- **Todos as a checklist.** `ui.tool()` now routes `write_todos` to a
  panel: `[x]` done, `[~]` in progress, `[ ]` pending, with a `todos 1/3`
  title. The raw tool output ("[x] Write hello.txt ...") was never worth a
  person's eyes.
- **A real input line.** `harness/prompt.py` replaces `input()` with
  prompt_toolkit. `input()` cannot edit a line that has wrapped past the
  screen width; prompts to a coding agent wrap. You also get persistent
  history across sessions and alt-enter for a newline. `ui.ask`,
  `ui.pick` and `ui.approve` all go through `prompt.read()`.

No change to the loop, the tools or the context.

## Diff from stage 12

```bash
diff -r ../step_12_sandbox/harness harness
```
