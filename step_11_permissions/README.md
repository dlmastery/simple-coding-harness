# Stage 11 - Tool permissions

An agent that runs shell commands can delete a file, or a whole operating
system, by mistake. The next step is proper permission checking.

**What this stage adds:** a rule table consulted before every tool call.
Read-only commands run silently, risky ones stop and ask the user, a few
are refused outright.

```text
tool call ──▶ check(name, args) ──▶ allow ──▶ run
                                ──▶ ask   ──▶ "allow? (y/n)" ──▶ run, or "The user denied this tool call."
                                ──▶ deny  ──▶ "Blocked by policy: ..."
```

## Files

```text
step_11_permissions/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop asks permissions.check() before every tool
│   ├── commands.py      slash commands, unchanged
│   ├── config.py        settings from the env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged
│   ├── llm.py           call_llm, unchanged
│   ├── permissions.py   BASH_RULES, decide() and check(): allow / ask / deny
│   ├── session.py       transcripts on disk, unchanged
│   ├── skills.py        skills, unchanged
│   ├── todos.py         the plan, unchanged
│   ├── tools.py         tools, unchanged
│   └── ui.py            gains approve(), the allow? (y/n) prompt
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: verdicts; the loop denies, asks, allows
├── pyproject.toml       package metadata; version 0.11.0
└── README.md            this file
```

## The code, piece by piece

### 1. The rules

`harness/permissions.py`:

```python
BASH_RULES = {
    "*": "ask",
    # read-only: let them through
    "ls*": "allow", "pwd": "allow", "cd *": "allow", "echo *": "allow",
```

```python
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
```

An allow list names the commands the agent can run on its own: ls, pwd,
echo and other read-only commands it uses to find things out. Every other
command is treated as risky and must ask. If the user approves, the tool
call runs. The allow / ask design comes from OpenCode. A third verdict,
`deny`, covers the few commands that no answer at the prompt should
unlock: rm, sudo, chmod, chown, curl and the like. The catch-all
`"*": "ask"` goes first because the last matching rule wins.

### 2. Compound commands: the strictest part wins

`harness/permissions.py`:

```python
def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        verdicts.append(action)
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"
```

`cat f; rm -rf /` is not saved by the `cat`. `split_command` cuts on
`|`, `;`, `&&` but not inside quotes, so `grep "a|b" f` stays one command.

### 3. Edits outside the project ask

`harness/permissions.py`:

```python
def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if name == "bash":
        return decide(args["command"]), f"run: {args['command']}"

    if name in ("write_file", "str_replace") and not inside_project(args["path"]):
        return "ask", f"{name} outside {PROJECT}: {args['path']}"

    return "allow", None
```

### 4. The loop consults the rules

`harness/agent.py`:

```python
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                action, reason = check(tool_call.function.name, args)
                if action == "deny":
                    result = f"Blocked by policy: {reason}"
                elif action == "ask" and not ui.approve(reason):
                    result = "The user denied this tool call."
                else:
                    result = TOOLS[tool_call.function.name](**args)
```

The verdict becomes the tool's *result*. The model reads "Blocked by
policy" or "The user denied this tool call" and adapts, instead of the
session dying. `ui.approve` is a one-line `allow? (y/n)` prompt.

## What this is not

This is not real security. A file can still be removed through Python:
the model can call `shutil.rmtree` from a script and the file disappears.
The rules only see the command text. Stage 12 is the kernel-level answer.

## Run it

```bash
harness
> delete the __pycache__ folders
```

The model reaches for `rm -rf`, gets "Blocked by policy", and finds
another way or explains. Ask it to run `python -c "print(1)"` and you get
the prompt.

## Diff from stage 10

```bash
diff -r ../step_10_todos/harness harness
```

New: `permissions.py`. Changed: `agent.py`, `ui.py` (`approve`).
