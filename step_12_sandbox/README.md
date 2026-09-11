# Stage 12 - An OS sandbox for bash (video 33:02 - 36:44)

> "Sandboxes ask a completely different question: if a specific operation
> is allowed or not. Even if the agent tries to write a Python file that
> removes some file outside its workspace, it's still going to get an
> error because the profile stops it."

New file `harness/sandbox.py`; `tools.bash` runs commands through it; the
banner shows which sandbox is active.

| | Permissions (stage 11) | Sandbox (stage 12) |
|---|---|---|
| question | is this worth interrupting the human? | can this process physically do that? |
| sees | the command text | every file and network operation |
| enforced by | our Python | the kernel |
| beaten by | `python -c "shutil.rmtree(...)"` | nothing the process can do |

## The policy and the mechanisms

One policy: read anything, write only inside the project, no network. The
video takes the macOS profile from the Codex CLI ("Codex is open source
and Apache 2 licensed, so you can use their code to bring their sandboxes
in"): deny by default, allow file reads, deny network, allow writes under
the project root. Linux uses bubblewrap with the same shape. "The project's
root folder is wherever you have invoked the command."

The video's demo: ask it to remove a file outside the project, say yes at
the prompt, and the agent still gets *operation not permitted*.

Windows has no equivalent here; the banner reads `sandbox: none` so you
know the rules are the only guard. A timed-out command comes back as a
result ("Timed out after 60s and was killed") rather than a crash.

## Diff from stage 11

```bash
diff -r ../step_11_permissions/harness harness
```
