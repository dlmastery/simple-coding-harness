# Step 12 - Permissions and an OS sandbox

**New in this step:** every tool call passes through a rule table before it
runs, `bash` executes inside an OS sandbox where one exists, and commands
have a hard timeout.

```
tool call ──▶ check(name, args) ──▶ allow ──▶ run
                                ──▶ ask   ──▶ "allow? (y/n)" ──▶ run / "declined"
                                ──▶ deny  ──▶ "Blocked by policy"
```

## Two layers, two jobs

| Layer | Question it answers | Enforced by |
|-------|---------------------|-------------|
| `permissions.py` | is this worth interrupting the human? | our Python |
| `sandbox.py` | what can this process physically touch? | the kernel |

They are deliberately separate. Rules are fast and readable but they only
see the command *text* - a clever `python -c` can do anything. The sandbox
does not care what the text says: writes outside the project fail, the
network is off, `.git` is read-only. On macOS that is `sandbox-exec`
(Seatbelt, built in); on Linux it is bubblewrap if installed; on Windows
there is no equivalent here, and the banner says `sandbox: none` so you
know the rules are the only line of defence.

## Reading the rules

`BASH_RULES` is a dict of glob → verdict, catch-all first, **last match
wins**. Read-only commands are `allow`, destructive or network commands are
`deny`, everything else falls through to `ask`.

A compound command is split on `|`, `;`, `&&` (respecting quotes - see
`split_command`) and every piece is rated; the **strictest verdict wins**.
So `cat f; rm -rf /` is denied even though `cat` is fine, and
`ls | some-unknown-thing` asks.

`deny` is not overridable at the prompt. That is the point: the rules
encode what you decided while calm, so you are not asked to decide while
an agent is waiting.

## Errors, again

A timeout (`subprocess.TimeoutExpired`) becomes a tool result: "Timed out
after 60s and was killed. Narrow the command down." The model reads it and
tries a narrower command. Nothing here can end the session.

## Run it

```bash
python -m harness
you> delete the __pycache__ folders
```

The model reaches for `rm -rf`, gets "Blocked by policy", and should
either explain or find another way. Ask it to run `python -c "print(1)"`
and you will get the `allow?` prompt.

## Diff from step 11

```bash
diff -r ../step_11_todos_and_install/harness harness
```

New: `permissions.py`, `sandbox.py`. Changed: `tools.py` (`bash` uses the
sandbox and handles timeouts; `execute` calls `check`), `ui.py`
(`approve`, sandbox name in banner), `agent.py`, `commands.py`.
