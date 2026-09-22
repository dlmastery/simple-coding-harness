# Stage 12 - An OS sandbox for bash

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Keep actions within limits**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 11 - Tool permissions](../step_11_permissions/README.md). Next: [Stage 13 - Readable todos and a real input line](../step_13_readable_todos_input_line/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

A sandbox asks a different question: is a specific operation allowed at
all? Even if the agent writes a Python file that removes something outside
its workspace, running it fails with an error, because the profile stops
the process.

**What this stage adds:** the `bash` tool runs inside a kernel-enforced
sandbox where the OS provides one, and the command runner - timeout,
process group, no stdin - moves from `tools.py` into `sandbox.py`.

| | Permissions (stage 11) | Sandbox (stage 12) |
|---|---|---|
| question | is this worth interrupting the human? | can this process physically do that? |
| sees | the command text | every file and network operation of the `bash` process |
| enforced by | the harness, in Python | the kernel |
| beaten by | `python -c "shutil.rmtree(...)"` after a "y" | nothing the `bash` process can do |
| covers | every tool | `bash` only; `write_file` runs in the harness process |

## Why: the rules only see text

Stage 11 asks before `python -c "..."`. Say yes to one that looks
harmless and it can still `shutil.rmtree` your home directory, `curl` a
key out to the network or rewrite `.git`. The rule table cannot know what
a script does. The kernel can: it sees every `open()`, every `connect()`,
and refuses the ones the profile does not allow. That is a different
layer, and both are needed - permissions decide what is worth asking,
the sandbox decides what is possible regardless of the answer.

## Files

```text
step_12_sandbox/
├── harness/
│   ├── __init__.py      marks the package
│   ├── agent.py         the loop, with the sandbox name in the banner
│   ├── commands.py      redraw() shows the sandbox name in the banner
│   ├── config.py        settings from the env or ~/.simple-harness/env
│   ├── context.py       the late block, unchanged
│   ├── llm.py           call_llm, unchanged
│   ├── permissions.py   the rule table, unchanged from stage 11
│   ├── sandbox.py       wrap(), name(), kill_tree() and run(): the OS sandbox and the timeout
│   ├── session.py       transcripts on disk, unchanged
│   ├── skills.py        skills, unchanged
│   ├── todos.py         the plan, unchanged
│   ├── tools.py         bash runs through sandbox.run()
│   └── ui.py            the banner shows which OS sandbox is active
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py         offline tests: sandbox name and run; a timeout is a result and kills the tree; no stdin
├── pyproject.toml       package metadata; version 0.12.0
└── README.md            this file
```

## The code, piece by piece

### 1. One policy, written as a macOS Seatbelt profile

`harness/sandbox.py`:

```python
PROFILE = """(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{project}") (literal "/dev/null"))
(deny file-write* (subpath "{project}/.git"))
"""
```

The macOS profile is the shape used by the OpenAI Codex CLI (Apache-2.0).
It denies everything by default, allows file reads, denies all network
access, and allows file writes inside the project's root folder. The
project's root folder is wherever the command was invoked. The `.git`
directory is excluded so the agent cannot rewrite history from a shell
command.

### 2. One mechanism per OS

`harness/sandbox.py`:

```python
def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        # one profile file per call: several tool calls may run at the same time
        with tempfile.NamedTemporaryFile("w", prefix="simple-harness-", suffix=".sb", delete=False) as profile:
            profile.write(PROFILE.format(project=PROJECT))
        return ["sandbox-exec", "-f", profile.name, "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        git_dir = PROJECT / ".git"
        return [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
            # the same two exceptions as the macOS profile: history is read-only,
            # and /tmp is writable because pytest, pip and tempfile need it
            *(["--ro-bind", str(git_dir), str(git_dir)] if git_dir.is_dir() else []),
            "--tmpfs", "/tmp",
            "--dev", "/dev", "--proc", "/proc",
            "--unshare-net", "--die-with-parent",
            "/bin/sh", "-c", command,
        ]

    return None  # Windows, or Linux without bubblewrap
```

macOS has `sandbox-exec` built in. On Linux the same shape is expressed
with bubblewrap: the whole filesystem read-only, the project bound
read-write with `.git` read-only again, a private `/tmp`, no network.
Windows needs a different mechanism. Nothing is done for it here, and the
banner shows `sandbox: none` so the user knows the stage 11 rules are the
only guard.

### 3. Running through it, with a timeout

`harness/sandbox.py`:

```python
def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us. Raises TimeoutExpired with the partial output.

    The command gets its own process group so a timeout can kill the whole
    tree: killing only the shell leaves a child holding the output pipe,
    and the call would block until that child exits on its own.
    """
    sandboxed = wrap(command)
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(
        sandboxed or command,
        shell=sandboxed is None,
        stdin=subprocess.DEVNULL,  # a command that waits for input would hang the turn
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        env=ENV,
        **group,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(process)
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
```

Three details carry over from the stage 9 `bash` and matter more once the
command is wrapped: the command runs in its own process group, so
`kill_tree` can kill everything it started (a `subprocess.run(timeout=)`
alone kills the shell and then waits for a child that still holds the
output pipe - a dev server started in the background would hang the turn
for good); stdin is `/dev/null`, so `python` or `cat` with no arguments
exits instead of waiting for a key nobody can press; and `PAGER=cat`,
`GIT_PAGER=cat` and `GIT_TERMINAL_PROMPT=0` keep git from paging or asking
for a password. Output is decoded as UTF-8 with replacement, so a stray
byte never raises.

`harness/tools.py`:

```python
def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    try:
        result = sandbox.run(command)
    except subprocess.TimeoutExpired as expired:
        # A slow command is the model's problem to work around, not a reason
        # to take the session down. Hand the failure back as a result.
        partial = (expired.stdout or "") + (expired.stderr or "")
        return f"Timed out after {expired.timeout}s and was killed. Output so far:\n{partial}"
    return (result.stdout + result.stderr) or "(no output)"
```

A hung command becomes a tool result the model can read - with whatever it
printed before it was killed - not an exception that ends the chat.

## Permissions versus the sandbox

Ask the agent to remove a file outside the project directory with a shell
command. Even after the user answers yes at the prompt, the command fails
with "operation not permitted", because the file is outside the sandbox's
write area. Permissions let the user decide. The sandbox decides
regardless.

## Run it

bash:

```bash
harness
> create a file called probe.txt in my home directory using a shell command
```

PowerShell: the same command; on Windows the banner says `sandbox: none`
and the write goes through once you answer `y`.

### Expected output (macOS or Linux with bubblewrap)

```text
─────────────────────────── coding agent ───────────────────────────
  sandbox: seatbelt  ·  /sessions  /rewind  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> create a file called probe.txt in my home directory using a shell command

  run: touch ~/probe.txt
  allow? (y/n)> y

  ┌──────────────────────────────────────────────────────────────┐
  │ bash touch ~/probe.txt                                       │
  │ ──────────────────────────────────────────────────────────── │
  │ touch: /Users/you/probe.txt: Operation not permitted         │
  └──────────────────────────────────────────────────────────────┘

  agent

  The sandbox does not allow writes outside the project. I can create
  it inside the project instead.
```

## Error handling

- A command that runs past 60 s is killed together with every process it
  started; the model reads `Timed out after 60s and was killed. Output so far:`.
- A command that needs a key press gets end-of-file on stdin and ends.
- A sandbox refusal is ordinary command output (`Operation not permitted`,
  `Read-only file system`), so it is a tool result like any other.
- Everything from stage 11 still holds: rules first, `Error:` results for
  bad calls, ctrl-c ends the turn, `/exit` or ctrl-d (ctrl-z then enter on
  Windows) leaves.

## Gotchas / What this is not

- Only `bash` is sandboxed. `read_file`, `write_file` and `str_replace`
  run in the harness process under the stage 11 rules; a `write_file`
  outside the project asks, and if you say yes it happens. `.git` writes
  through `write_file` ask too.
- On Windows there is no sandbox. The tool named `bash` runs `cmd.exe`
  through `shell=True`; the stage 11 rules are the only guard.
- Inside the box the network is off and everything outside the project
  and `/tmp` is read-only. `pip install`, `npm install` and anything that
  writes to `~/.cache` fail there - by design. Run those yourself.
- The macOS profile is the minimal shape; some programs need Mach services
  (`mach-lookup`) the profile does not grant and fail with an obscure
  error. The bubblewrap variant is only used when `bwrap` is on the PATH;
  without it the banner says `sandbox: none`.
- The environment, `API_KEY` included, is inherited by the command. The
  rules make `env` ask (stage 11); a script can still read
  `os.environ`. A stricter setup passes a scrubbed environment.

## What the next stage adds

Stage 13 is presentation: the plan is drawn as a checklist, and typing
goes through prompt_toolkit so a long line can be edited.

## Diff from stage 11

```bash
diff -r ../step_11_permissions/harness harness
```

New: `sandbox.py`. Changed: `tools.py` (`bash`), `agent.py` and
`commands.py` (banner), `ui.py`.

<!-- harness-learning-check -->
## Check your understanding

Why is a refusal prompt weaker evidence than a refused boundary-crossing operation?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

A prompt states intended behavior. The actual execution mechanism and its tested refusal establish what the boundary enforces in that case.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
