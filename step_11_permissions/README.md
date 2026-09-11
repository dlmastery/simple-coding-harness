# Stage 11 - Tool permissions (video 31:44 - 33:02)

> "Every time I run this, I'm worried that it will go delete some file or
> delete my entire operating system. So the next step is proper permission
> checking."

New file `harness/permissions.py`; the loop in `agent.py` consults it
before every tool call; `ui.py` gains the `allow? (y/n)` prompt.

```
tool call ──▶ check(name, args) ──▶ allow ──▶ run silently
                                ──▶ ask   ──▶ "allow? (y/n)" ──▶ run, or "The user denied this tool call."
                                ──▶ deny  ──▶ "Blocked by policy: ..."
```

## The rules

"An allow list of commands that the agent can just run - ls, pwd, echo,
generally read-only commands it may need to find out some information.
However, to run stuff that is risky like rm, any kind of sudo command,
changing ownership or permissions, or curl some random website - the agent
must ask for permission, and if I approve then that tool call gets
executed." The video credits the allow / ask design to OpenCode.

`BASH_RULES` is a dict of glob → verdict, catch-all first, last match
wins. A compound command is split on `|`, `;`, `&&` (respecting quotes)
and the strictest verdict of its parts wins, so `cat f; rm -rf /` is not
saved by the `cat`. A third verdict, `deny`, covers the few commands no
answer at the prompt should unlock. Edits outside the project directory
ask.

The verdict becomes the tool *result* - "Blocked by policy: ..." or "The
user denied this tool call." - so the model reads it and adapts.

## What this is not

"This is not real security because a file can still be removed using
Python." The rules only see the command text. That is stage 12's job.

## Diff from stage 10

```bash
diff -r ../step_10_todos/harness harness
```
