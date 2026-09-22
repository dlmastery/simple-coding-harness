# Stage 11 - Tool permissions

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Keep actions within limits**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 10 - Todos](../step_10_todos/README.md). Next: [Stage 12 - An OS sandbox for bash](../step_12_sandbox/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

An agent that runs shell commands can delete a file, or a whole operating
system, by mistake. The next step is proper permission checking.

**What this stage adds:** a rule table consulted before every tool call.
Commands we are happy to run unasked run silently, risky ones stop and ask
the user, a few are refused outright. Anything the rules cannot read - a
`$(...)` inside a command, a redirection into a file - asks.

```text
tool call ──▶ check(name, args) ──▶ allow ──▶ run
                                ──▶ ask   ──▶ "allow? (y/n)" ──▶ run, or "The user denied this tool call."
                                ──▶ deny  ──▶ "Blocked by policy: ..."
```

## Why: the model will try `rm -rf`

Ask the stage 10 agent to "clean up the __pycache__ folders" and it runs
`rm -rf` on the first try - usually on the right directory. Usually. It
will also happily `git push`, `curl | sh` and overwrite files with `>`
because those are the commands that appear in its training data. Nothing
in the loop knows a destructive command from `ls`. A rule table in front
of the tool call is the cheapest possible guard: the model is told "no" or
the human is asked, and either answer becomes the tool's result.

## Files

```text
step_11_permissions/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop, unchanged: run_tool() now asks permissions.check() first
│   ├── commands.py      slash commands, unchanged
│   ├── config.py        settings from the env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged
│   ├── llm.py           call_llm, unchanged
│   ├── permissions.py   BASH_RULES, split_command(), decide() and check(): allow / ask / deny
│   ├── session.py       transcripts on disk, unchanged
│   ├── skills.py        skills, unchanged
│   ├── todos.py         the plan, unchanged
│   ├── tools.py         run_tool() consults check() before running anything
│   └── ui.py            gains approve(), the allow? (y/n) prompt
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: verdicts; what the rules cannot read; the loop denies, asks, allows
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
    # env prints every variable, API_KEY included, straight into the transcript
    "env": "ask",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
```

An allow list names the commands the agent can run on its own: ls, pwd,
echo and other commands it uses to find things out. Every other command
is treated as risky and must ask. If the user approves, the tool call
runs. The allow / ask design comes from OpenCode. A third verdict,
`deny`, covers the few commands that no answer at the prompt should
unlock: rm, sudo, chmod, chown, curl and the like. The catch-all
`"*": "ask"` goes first because the last matching rule wins (a dict keeps
insertion order).

`env` is not on the allow list on purpose: `config.py` loads `API_KEY`
into the environment, and `env` would print it into the transcript and
the session file on disk.

### 2. Compound commands: the strictest part wins

`harness/permissions.py`:

```python
def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    if UNREADABLE.search(command):
        return "ask"  # we cannot see what runs inside, so a human has to
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        if action == "allow" and WRITES.search(unquoted(part)):
            action = "ask"  # `cat a > b` is a write, whatever the verb
        verdicts.append(action)
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"
```

`cat f; rm -rf /` is not saved by the `cat`. `split_command` cuts on
`|`, `;`, `&`, `&&`, `||` and newlines but not inside quotes, so
`grep "a|b" f` stays one command and a two-line command is two commands.
`2>&1` is a redirection, not a separator, so `cat f 2>&1` stays whole.

### 3. What the rules cannot read

The rules match the first word of a command. Three things hide another
command behind a harmless first word, and the table cannot see them:

```python
# The rules match a command's first word; these hide another command inside it.
UNREADABLE = re.compile(r"\$\(|`|<\(|>\(")
# An allowed command that writes: a redirection into a file, tee, or find that deletes / runs things.
WRITES = re.compile(r"(?<![0-9&<])>>?(?!&)|\btee\b|\bfind\b.*\s-(delete|exec|execdir|ok|okdir)\b")
```

- `echo $(rm -rf /)` and ``ls `rm -rf ~` `` start with an allowed word.
  Any `$(`, backtick or process substitution makes the whole command ask.
- `echo secret > ~/.bashrc`, `cat /dev/null > important.py` and
  `ls | tee out` are writes with an allowed verb. A `>` outside quotes, or
  `tee`, downgrades an `allow` to `ask`. `grep '>' f` is still allowed:
  quoted text is blanked before the check.
- `find . -delete` and `find . -exec rm {} +` are `rm` with a different
  first word. `find` with `-delete`, `-exec`, `-execdir`, `-ok` or `-okdir`
  asks.

### 4. Edits outside the project, or into .git, ask

`harness/permissions.py`:

```python
def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if name == "bash":
        command = args.get("command", "")
        if not command:
            return "deny", "bash: missing argument 'command'"
        return decide(command), f"run: {command}"

    if name in ("write_file", "str_replace"):
        path = args.get("path", "")
        if not path:
            return "deny", f"{name}: missing argument 'path'"
        if not inside_project(path):
            return "ask", f"{name} outside {PROJECT}: {path}"
        if in_git_dir(path):
            return "ask", f"{name} inside .git: {path}"

    return "allow", None
```

`inside_project` resolves the path first, so a symlink inside the project
that points outside counts as outside. `.git` is inside the project but a
hook written there runs on the next `git` command, so it asks too. A call
with the argument missing is refused with a reason the model can act on,
instead of a `KeyError`.

### 5. The tool runner consults the rules

`harness/tools.py`:

```python
    action, reason = check(name, args)
    if action == "deny":
        return args, f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return args, "The user denied this tool call."
```

The verdict becomes the tool's *result*. The model reads "Blocked by
policy" or "The user denied this tool call" and adapts, instead of the
session dying. `ui.approve` is a one-line `allow? (y/n)` prompt; ctrl-d or
ctrl-c at that prompt counts as "no".

## Run it

bash / PowerShell:

```bash
harness
> delete the __pycache__ folders
```

### Expected output

```text
> delete the __pycache__ folders

  ┌──────────────────────────────────────────────────────────────┐
  │ bash find . -name __pycache__ -type d -exec rm -rf {} +      │
  │ ──────────────────────────────────────────────────────────── │
  │ The user denied this tool call.                              │
  └──────────────────────────────────────────────────────────────┘
```

before that panel, the prompt:

```text
  run: find . -name __pycache__ -type d -exec rm -rf {} +
  allow? (y/n)> n
```

The model reaches for `rm -rf`, gets "Blocked by policy", and reaches for
`find -exec rm`, which asks. Answer `y` and it runs. Ask it to run
`python -c "print(1)"` and you get the prompt too.

## Error handling

- `Blocked by policy: run: ...` and `The user denied this tool call.` are
  tool results; the model reads them and tries something else or explains.
- A `bash` call without a `command` is `Blocked by policy: bash: missing
  argument 'command'`; a `write_file` without a `path` likewise.
- Everything from stage 9 still holds: bad JSON, an unknown tool or an
  exception inside a tool is an `Error:` result; ctrl-c ends the turn;
  `/exit` or ctrl-d (ctrl-z then enter on Windows) leaves.
- `harness < script.txt` works, but the next line of the script is read
  as the answer to an `allow? (y/n)` prompt; end of file counts as "no".

## Gotchas / What this is not

This is not real security. The rules only see the command text:

- `python -c "import shutil; shutil.rmtree('x')"` asks, and if you say
  yes the file is gone. So does `sh -c 'rm -rf /'`, `xargs rm` and
  `/bin/rm`. `deny` is a convenience for the obvious cases; `ask` is the
  real floor.
- `read_file` may read anything on the machine, `~/.ssh/id_rsa` included.
  Only writes are checked.
- On Windows the tool named `bash` runs `cmd.exe`, where the destructive
  verbs are `del`, `rd /s /q` and `Remove-Item`. They fall to the catch-all
  and ask, but so do `dir` and `type`.

Stage 12 is the kernel-level answer.

## What the next stage adds

Stage 12 wraps `bash` in an OS sandbox, so even a command you approved
cannot write outside the project or reach the network.

## Diff from stage 10

```bash
diff -r ../step_10_todos/harness harness
```

New: `permissions.py`. Changed: `tools.py` (`run_tool` consults `check`),
`ui.py` (`approve`).

<!-- harness-learning-check -->
## Check your understanding

Can a permitted command still be incorrect?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

Yes. Permission determines whether an action may proceed. Correctness requires a separate check of its behavior and output.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
