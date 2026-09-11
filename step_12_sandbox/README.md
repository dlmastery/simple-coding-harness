# Stage 12 - An OS sandbox for bash

A sandbox asks a different question: is a specific operation allowed at
all? Even if the agent writes a Python file that removes something outside
its workspace, the call fails with an error, because the profile stops it.

**What this stage adds:** `bash` runs inside a kernel-enforced sandbox
where the OS provides one, and every command has a timeout.

| | Permissions (stage 11) | Sandbox (stage 12) |
|---|---|---|
| question | is this worth interrupting the human? | can this process physically do that? |
| sees | the command text | every file and network operation |
| enforced by | the harness, in Python | the kernel |
| beaten by | `python -c "shutil.rmtree(...)"` | nothing the process can do |

## The code, piece by piece

### 1. One policy, written as a macOS Seatbelt profile

`harness/sandbox.py`:

```python
PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""
```

The macOS profile is the shape used by the OpenAI Codex CLI (Apache-2.0).
It denies everything by default, allows file reads, denies all network
access, and allows file writes inside the project's root folder. The
project's root folder is wherever the command was invoked. The `.git`
directory is excluded so the agent cannot rewrite history.

### 2. One mechanism per OS

`harness/sandbox.py`:

```python
def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        profile = Path(tempfile.gettempdir()) / "simple-harness.sb"
        profile.write_text(PROFILE)
        return ["sandbox-exec", "-f", str(profile), "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
            "--dev", "/dev", "--proc", "/proc",
            "--unshare-net", "--die-with-parent",
            "/bin/sh", "-c", command,
        ]

    return None  # Windows, or Linux without bubblewrap
```

macOS has `sandbox-exec` built in. On Linux the same shape is expressed
with bubblewrap: the whole filesystem read-only, the project bound
read-write, no network. Windows needs a different mechanism. Nothing is
done for it here, and the banner shows `sandbox: none` so the user knows
the stage 11 rules are the only guard.

### 3. Running through it, with a timeout

`harness/sandbox.py`:

```python
def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
```

`harness/tools.py`:

```python
def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    try:
        result = sandbox.run(command)
    except subprocess.TimeoutExpired as expired:
        # A slow command is the model's problem to work around, not a reason
        # to take the session down. Hand the failure back as a result.
        return f"Timed out after {expired.timeout}s and was killed. Narrow it down."
    return (result.stdout + result.stderr) or "(no output)"
```

A hung command becomes a tool result the model can read, not an exception
that ends the chat.

## Permissions versus the sandbox

Ask the agent to remove a file outside the project directory. Even after
the user answers yes at the prompt, the command fails with "operation not
permitted", because the file is outside the sandbox's write area.
Permissions let the user decide. The sandbox decides regardless.

## Diff from stage 11

```bash
diff -r ../step_11_permissions/harness harness
```

New: `sandbox.py`. Changed: `tools.py` (`bash`), `agent.py` and
`commands.py` (banner), `ui.py`.
