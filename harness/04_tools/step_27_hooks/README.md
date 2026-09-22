# Step 27 - Hooks

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 26 - MCP client](../step_26_mcp_client/README.md). Next: [Step 28 - Plan mode and structured output](../step_28_plan_mode/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** hooks. A hook is a small program the user
configures in `hooks.json`, and the harness runs it at a fixed point in
the loop: before and after every tool call, when a prompt is submitted,
before compaction, and at session start and end. A hook can block a tool
call, reject or replace its result, or add text to the late block. Two
example hooks ship in `.agents/`: one refuses edits to `.env` files, one
logs every tool name to a file.

## Why hooks, and what breaks without them

Every rule in the harness so far is code. The permission table in
`permissions.py` decides which commands ask. The sandbox decides which
paths a command may touch. To add a rule, the user edits the harness.

Most rules a team wants are small and local. Never write to this file.
Run the formatter after every edit. Log every tool call for an audit.
Remind the model of the branch policy on every prompt. None of these
belong in the harness, because the next project wants different ones.
Without hooks, the team that wants "never touch `.env`" forks
`permissions.py`, and the fork drifts from every later step.

A hook is the answer. The harness names a few events. The user writes a
script for any of them, in any language, and lists it in a JSON file. The
harness sends the script the event as JSON on stdin and reads its answer.
The harness does not know what the script does. The script does not know
how the harness works. The JSON in between is the whole contract.

There are two kinds. A `command` hook is a shell line, run as a
subprocess. A `python` hook is a `module:function` string, imported and
called in-process. The command kind works for any language and any tool.
The python kind skips the subprocess and can hold state.

## The code, piece by piece

### 1. The configuration

`harness/hooks.py`:

```python
CONFIG_PATHS = [
    Path.home() / ".simple-harness" / "hooks.json",
    Path.cwd() / ".agents" / "hooks.json",
]
```

Two files, one for the user and one for the project. The lists are
merged per event, so the user file runs first and the project file after
it. Each entry is a hook: an optional `matcher`, and either a `command`
or a `python` string. Both files are consulted on every event, but read
from disk only when their modification time changed:

`harness/hooks.py`:

```python
def read_config(path):
    """One hooks.json, parsed; cached by its mtime, so every event does not re-read it.

    A broken file is noted once, when it changed, not on every tool call.
    """
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}
    if path in _cache and _cache[path][0] == mtime:
        return _cache[path][1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("the top level is not an object")
    except (OSError, ValueError) as failed:
        _note(f"hook config {path} skipped: {failed}")
        data = {}
    _cache[path] = (mtime, data)
    return data
```

So editing `hooks.json` mid-session takes effect on the next event, and
a file with a syntax error is reported once and treated as empty until
it is fixed.

`.agents/hooks.json`:

```text
{
  "PreToolUse": [
    {"matcher": "write_file|str_replace", "command": "python .agents/block_env_writes.py"}
  ],
  "PostToolUse": [
    {"matcher": "*", "command": "python .agents/log_tool_use.py"}
  ]
}
```

The matcher is a glob on the tool name. A `|` joins several globs. A
missing matcher, or `*`, matches every tool. Events without a tool, such
as `SessionStart`, run every hook listed for them.

`harness/hooks.py`:

```python
def matches(hook, tool_name):
    """Does this hook apply to the tool? The matcher is `glob|glob`; `*` or none means all."""
    pattern = str(hook.get("matcher") or "*")
    if tool_name is None:  # an event without a tool: every hook of that event runs
        return True
    return any(fnmatchcase(tool_name, part.strip()) for part in pattern.split("|") if part.strip())  # case matters on every OS
```

`fnmatchcase`, not `fnmatch`: the plain one is case-insensitive on
Windows, so a matcher of `Bash` would match `bash` on one OS and not the
other.

### 2. Running a command hook

`harness/hooks.py`:

```python
def run_command(command, event):
    """Run a shell hook with the event on stdin. Returns a reply dict or None.

    shell=True so `python .agents/check.py` works the same on Windows and
    elsewhere. Exit 0 with JSON on stdout is a reply; exit 2 blocks with
    stderr as the reason; anything else is reported and ignored. The hook
    gets a process group of its own, so a timeout kills the script and not
    just the shell that started it (the same plumbing as bash in sandbox.py).
    """
    group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(
        resolve_python(command),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        cwd=event.get("cwd") or None,
        **group,
    )
    try:
        stdout, stderr = process.communicate(json.dumps(event), timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        sandbox.kill_tree(process)
        process.communicate()
        raise
    completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if completed.returncode == BLOCK_EXIT_CODE:
        return {"block": completed.stderr.strip() or "blocked by hook"}
    if completed.returncode != 0:
        _note(f"hook `{command}` exited {completed.returncode} and was ignored: {completed.stderr.strip()[:200]}")
        return None
    output = completed.stdout.strip()
    if not output:
        return None
    reply = json.loads(output)
    return reply if isinstance(reply, dict) else None
```

The event goes in as one JSON object on stdin. It always has the same
keys: `event`, `tool_name`, `tool_input`, `tool_result`, `ok`, `prompt`
and `cwd`, with `null` for the ones that do not apply. The answer comes
back in two channels. The exit code says whether to continue: `0`
continues, `2` blocks, and stderr is the reason. Stdout, when not empty,
is a JSON reply: `{"result": ...}` replaces a tool result, `{"context":
...}` adds text, and `{"block": "reason"}` blocks too.

The subprocess runs with `shell=True`, so the command is one string, as
the user wrote it. A command that starts with `python` runs under the
harness's own interpreter. The shipped hooks depend on that: they are
Python scripts, so they run on every operating system, and the harness
already knows one Python that works.

The timeout is real on every OS. With `shell=True` the hook is a
grandchild of the harness (`cmd.exe` or `sh` in between), and killing
the shell alone would leave the script running and holding the pipes, so
the harness would wait on it anyway. The hook gets a process group of
its own and `kill_tree` ends the whole group: `taskkill /T` on Windows,
`SIGKILL` to the session elsewhere. Its output is decoded as UTF-8 so a
non-ASCII reason from a hook is not itself an error.

### 3. Running a python hook

`harness/hooks.py`:

```python
def run_python(target, event):
    """Import `module:function` and call it with the event. Returns its reply."""
    module_name, _, function_name = target.partition(":")
    if not module_name or not function_name:
        raise ValueError(f"python hook must be 'module:function', got {target!r}")
    for extra in (Path.cwd(), Path.cwd() / ".agents"):
        if str(extra) not in sys.path:
            sys.path.append(str(extra))
    module = importlib.import_module(module_name)
    reply = getattr(module, function_name)(event)
    return reply if isinstance(reply, dict) else None
```

The same event dict, passed as an argument instead of stdin. The function
returns the same reply shape, or `None`. The project directory and its
`.agents` folder are added to the import path, so a hook module can live
next to the config.

### 4. A hook cannot take the loop down

`harness/hooks.py`:

```python
def run_hook(hook, event):
    """Run one hook of either kind. A failure becomes a note, never an exception."""
    try:
        if hook.get("command"):
            return run_command(hook["command"], event)
        if hook.get("python"):
            return run_python(hook["python"], event)
        _note(f"hook without command or python skipped: {hook}")
    except subprocess.TimeoutExpired:
        _note(f"hook `{describe(hook)}` took more than {TIMEOUT}s and was ignored")
    except Exception as failed:  # noqa: BLE001 - a broken hook must not take the loop down
        _note(f"hook `{describe(hook)}` failed and was ignored: {type(failed).__name__}: {failed}")
    return None
```

A hook is user code, and user code breaks. A script that crashes, prints
something that is not JSON, imports a module that is not there, or hangs
past the 30 second timeout is reported with one dim note and treated as
if it had said nothing. The tool call runs, the prompt goes through, the
session continues. Only an explicit block stops anything.

`harness/hooks.py`:

```python
def run_hooks(event_name, event=None):
    """Run every hook registered for the event, in config order. Returns a HookOutcome.

    The first hook that blocks ends the run. Otherwise the last `result`
    wins and every `context` is kept, one per line.
    """
    event = {key: None for key in EVENT_KEYS} | (event or {})
    event["event"] = event_name
    event["cwd"] = event["cwd"] or os.getcwd()

    outcome = HookOutcome()
    for hook in load_config().get(event_name, []):
        if not matches(hook, event.get("tool_name")):
            continue
        reply = run_hook(hook, event)
        if not reply:
            continue
        if reply.get("block") is not None:
            outcome.blocked = True
            outcome.reason = str(reply["block"]) or "blocked by hook"
            return outcome
        if reply.get("result") is not None:
            outcome.result = reply["result"]
        if reply.get("context"):
            outcome.context = (outcome.context + "\n" + str(reply["context"])).strip()
    return outcome
```

`run_hooks` is the one entry point the rest of the harness calls. It
fills in the event keys, runs every matching hook in order, and folds the
replies into one `HookOutcome` with four fields: `blocked`, `reason`,
`result` and `context`. A block ends the run at once. Several results
keep the last. Several contexts are joined.

### 5. The tool hooks

`harness/tools.py`:

```python
    action, reason = check(name, args)
    if action == "deny":
        return args, action, reason
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": name, "tool_input": args})
    if outcome.blocked:
        return args, "blocked", outcome.reason
    if outcome.context:
        PRE_CONTEXT[tool_call.id] = outcome.context
    return args, action, reason
```

`decide()` gains a fourth verdict. After the permission rules rate the
call, the `PreToolUse` hooks see its name and arguments. A block becomes
the verdict `blocked`, and `settle()` turns that into the tool result
`Blocked by hook: <reason>`. The tool never runs, and the model reads the
reason. A call the rules already denied, or one whose arguments were not
a JSON object, is not offered to the hooks. Context from a `PreToolUse`
hook is kept per call id and joins the result once the tool has run.

The order of one call is: rules → `PreToolUse` → the `allow? (y/n)`
prompt → the tool → `PostToolUse`. The hook runs before the prompt, not
after, so a hook that blocks saves the user a question, and a hook that
lets the call through leaves the question where it was. It also means an
audit hook on `PreToolUse` sees calls the user then declines; the event
does not say what the user answered. `PostToolUse` runs only for a tool
that actually ran: never after a deny, a block, a decline, or broken
arguments.

`harness/tools.py`:

```python
def run(tool_call, args):
    """Run the tool with already-parsed arguments, then the PostToolUse hooks.

    No permission check here. The event says whether the tool succeeded
    (`ok`: the result is not an Error:). A hook that answers with a result
    replaces what the tool returned; one that blocks cannot undo the tool,
    so the model is told the hook rejected the outcome; any context, from
    the hooks before or after the call, rides along in a <hook> block.
    """
    result = call(tool_call, args)
    event = {"tool_name": tool_call.function.name, "tool_input": args, "tool_result": result, "ok": not result.startswith("Error")}
    outcome = hooks.run_hooks("PostToolUse", event)
    if outcome.blocked:
        result = f"Blocked by hook: {outcome.reason}"
    elif outcome.result is not None:
        result = as_text(outcome.result)
    context = "\n".join(c for c in (PRE_CONTEXT.pop(tool_call.id, ""), outcome.context) if c)
    if context:
        result += f"\n<hook>\n{context}\n</hook>"
    return result
```

`run()` calls the tool through `call()`, the plain call split out of
step 22's `run()`: it turns an unknown name or an exception inside the
tool into an `Error:` string and makes any other result text with
`as_text()`, which a hook's replacement result goes through too. Then
come the `PostToolUse` hooks, with the result in the event and `ok`
saying whether it is an `Error:`. That prefix is
the harness's convention for every failed tool (a missing file, a bad
argument, a server that said no); a `bash` command that exited non-zero
is still `ok`, its exit code is in the text. A hook that answers with
`result` replaces it. A hook that blocks after the tool ran cannot undo
the write or the command; the model gets `Blocked by hook: <reason>`
instead of the result, which is the hook's way to say "do not build on
this". Both hook points sit on the shared path: `execute()`,
`execute_all()`, and the subagent loop all go through `decide()` and
`run()`, so a subagent and a parallel batch are hooked the same way as a
single call on the main thread.

What each event honours:

| event              | `block`                              | `result`             | `context`                        |
|--------------------|--------------------------------------|----------------------|----------------------------------|
| `PreToolUse`       | the tool does not run                | ignored              | appended to the tool result      |
| `PostToolUse`      | the result becomes `Blocked by hook` | replaces the result  | appended to the tool result      |
| `UserPromptSubmit` | the prompt is dropped, with a note   | ignored              | in `<hooks>` for that turn       |
| `PreCompact`       | the transcript is kept               | ignored              | ignored                          |
| `SessionStart`     | ignored                              | ignored              | in `<hooks>` for the session     |
| `SessionEnd`       | ignored                              | ignored              | ignored                          |

### 6. The turn and the session

`harness/agent.py`:

```python
    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    messages.append({"role": "user", "content": user_input})
```

The `UserPromptSubmit` hooks see the prompt before it joins the history;
a blocked prompt never enters the transcript. Their context is handed
to `reminder()`, which puts it in a `<hooks>` tag in the late block for
every model call of that turn. The next turn starts clean.

`harness/context.py`:

```python
def hooks_note(turn_context=""):
    """Text the hooks asked to add: the session's, then this turn's."""
    text = "\n".join(part for part in SESSION_CONTEXT + [turn_context] if part).strip()
    return f"\n<hooks>\n{text}\n</hooks>" if text else ""
```

`SessionStart` runs once, before the first prompt, and its context is
kept in `SESSION_CONTEXT` for the whole session. `SessionEnd` runs on
the way out, after the browser and the MCP servers are closed, whether
the chat ended at the prompt or on an exception.
`PreCompact` runs at the top of `commands.compact()`, and a block keeps
the transcript as it is. That function is also what the loop calls for
*automatic* compaction, so a hook that always blocks `PreCompact` turns
compaction off for the session; the context then grows until `fit()`
starts discarding old tool results wholesale.

### 7. The shipped hooks

`.agents/block_env_writes.py`:

```python
event = json.load(sys.stdin)
path = str((event.get("tool_input") or {}).get("path") or "")
name = PurePath(path).name

if name == ".env" or name.startswith(".env."):
    print(f"{name} holds secrets; edit it by hand, not through the agent", file=sys.stderr)
    sys.exit(2)
```

A few lines. Read the event, look at the path, exit `2` with a reason
when the file is a `.env`. The config runs it only for `write_file` and
`str_replace`, so a `read_file` of the same path is not affected. It
guards two tools, not the file: `bash` with `echo KEY=1 > .env` is a
different tool, and the rules, not this hook, are what ask about that
redirection.

`.agents/log_tool_use.py`:

```python
event = json.load(sys.stdin)
log = Path(event.get("cwd") or ".") / ".agents" / "tool_log.txt"
log.parent.mkdir(parents=True, exist_ok=True)
with log.open("a", encoding="utf-8") as f:
    f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {event.get('tool_name')}\n")
```

The second one appends a timestamp and the tool name to
`.agents/tool_log.txt` after every call. It prints nothing and exits `0`,
so the real result stands.

## Run it

Prerequisites are those of step 26: Python 3.11+, `API_KEY` in the
environment or `~/.simple-harness/env`, and `pip install -e .` from this
directory (add `".[mcp]"` for the echo server). Start from this directory
so `.agents/hooks.json` is found.

bash:

```bash
cd harness/04_tools/step_27_hooks
pip install -e .
harness
```

PowerShell:

```powershell
cd harness/04_tools/step_27_hooks
pip install -e .
harness
```

### Expected output

```text
> /hooks

  PreToolUse    write_file|str_replace   python .agents/block_env_writes.py
  PostToolUse   *                        python .agents/log_tool_use.py

> create a .env file with API_KEY=test

  ╭──────────────────────────────────────────────────────────────────╮
  │ write_file {"path": ".env", "content": "API_KEY=test\n"}         │
  │ ──────────────────────────────────────────────────────────────── │
  │ Blocked by hook: .env holds secrets; edit it by hand, not        │
  │ through the agent                                                │
  ╰──────────────────────────────────────────────────────────────────╯

  A hook refuses writes to .env files, so I have not created it. Add the
  line by hand: API_KEY=test

> list the python files here

  ╭──────────────────────────────────────────────────────────────────╮
  │ bash {"command": "ls harness/*.py"}                              │
  │ ──────────────────────────────────────────────────────────────── │
  │ harness/agent.py                                                 │
  │ harness/browse.py                                                │
  │ ...                                                              │
  ╰──────────────────────────────────────────────────────────────────╯
```

Then `cat .agents/tool_log.txt` (`Get-Content .agents\tool_log.txt` in
PowerShell) shows one line per call that ran, with the time and the
name: `2026-09-18 21:40:12 bash`. The blocked `write_file` is not in it,
because `PostToolUse` never ran for it.

Write a hook of your own. Save this as `.agents/remind.py`:

```text
import json, sys
json.load(sys.stdin)
print(json.dumps({"context": "Run pytest before you say a task is done."}))
```

Add it to `.agents/hooks.json` under `"UserPromptSubmit"` as
`{"command": "python .agents/remind.py"}`. On the next prompt the late
injection panel shows the sentence inside `<hooks>` tags.

Run the offline tests from the repository root:

```bash
python run_tests.py 27
```

## Error handling

- **A hook that crashes, exits non-zero (other than 2), prints something
  that is not JSON, or names a missing module** prints one dim note
  (`hook `python x.py` failed and was ignored: ...`) and counts as
  silent. The tool runs, the prompt goes through.
- **A hook that hangs** is killed after `TIMEOUT` (30s), whole process
  tree included, and noted: `hook `...` took more than 30s and was
  ignored`.
- **A broken `hooks.json`** is noted once (`hook config ... skipped`) and
  treated as empty until its mtime changes.
- **A tool call with broken arguments** (not a JSON object) never reaches
  the hooks; its result is `Error: the arguments of <tool> are not a JSON
  object: ...`. An unknown tool name gives `Error: no tool named '...'.`,
  a tool that raises gives `Error: <Type>: <message>`; the `PostToolUse`
  hooks see those with `ok: false`.
- **A failing command** returns its output and exit code as the result;
  past 60s it is killed with its tree: `Timed out after 60s and was
  killed. Output so far: ...`.
- **A dead model call** ends the turn with the note `model call failed:
  ...`; the user message stays and the transcript is valid.
- **ctrl-c mid-turn** answers the unfinished tool calls with
  `(interrupted before this tool ran)` and returns to the prompt; a
  command hook that was running is killed with the tool it wrapped.
- **A blocked prompt in `-p` mode** prints the reason on stderr, nothing
  on stdout, and exits 1, like any empty reply.
- **A turn of more than 40 model calls** is stopped with a note; say
  `continue` to go on.

To leave: `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or
ctrl-c at the prompt. The usage summary prints, then `main()` closes the
browser, stops the MCP servers, and runs `SessionEnd` last.

## Gotchas / What this is not

- **A project `hooks.json` is code you run.** Starting the harness in a
  checkout runs that checkout's hooks with your permissions, on every
  tool call. Read `.agents/hooks.json` in a repository you did not write
  before you start the harness there.
- **Python hooks are imported once.** Editing `.agents/x.py` mid-session
  changes nothing until the harness restarts; `hooks.json` itself is
  re-read when it changes. The `.agents` folder goes at the *end* of
  `sys.path`, so a hook module named like a standard or installed module
  (`test`, `json`) resolves to the wrong one; pick a distinctive name.
- **`PreToolUse` fires for calls the user then declines**, and the event
  has no field for the user's answer.
- **`PostToolUse` cannot undo.** A block after the tool ran tells the
  model the result was rejected; the file is still written, the command
  has still run.
- **`ok` is a prefix test.** It is `false` when the result starts with
  `Error`, the harness's convention for a failed tool; a non-zero `bash`
  exit is `ok: true` with the exit code in the text.
- **The `.env` hook guards `write_file` and `str_replace` only.** Writes
  through `bash` are the permission rules' business.
- **`PreCompact` also gates automatic compaction.**
- **Matchers are case-sensitive** (`fnmatchcase`), on Windows too, and
  `[...]` is a character class, not literal brackets.
- **One subprocess per hook per event.** The shipped log hook costs a
  Python start-up on every tool call; a long run with parallel subagents
  multiplies that.
- **Not a sandbox and not a security boundary.** A hook sees what the
  harness sends it; a command the rules allow, or a model that names a
  tool differently, is a different event.
- **Windows:** the tool called `bash` is `cmd.exe`, `sandbox: none`, and
  command hooks run under `cmd.exe /c` too; `python` at the start of a
  hook command is rewritten to the running interpreter.

## What to notice

- The contract is JSON on stdin and JSON on stdout, plus an exit code.
  Any language that can read stdin can be a hook. The harness has no
  hook API to learn.
- Blocked is a tool result, not an exception. The model sees `Blocked by
  hook: <reason>` in the same place it would see the tool's output, and
  the system prompt tells it not to retry. Nothing in the loop changes
  shape.
- A hook failure is a note. A crash, a timeout, a bad config file: each
  one prints a dim line and the loop carries on. Only an exit code of
  `2`, or an explicit `block` reply, stops anything.
- The hook points are on the shared path. `decide()` and `run()` are
  what subagents and parallel batches call, so one hook covers every
  tool call in the process. A `PostToolUse` hook may run from a pool
  thread; keep it free of shared state or make it safe.
- Every `PostToolUse` hook is one more subprocess per tool call. The
  shipped log hook costs a Python start-up each time. That is fine for a
  chat and worth knowing for a long run.

## Files

```text
step_27_hooks/
├── harness/
│   ├── llm.py                        the model call; the system prompt explains a hook's verdict
│   ├── tools.py                      the registry; PreToolUse and PostToolUse around every call
│   ├── agent.py                      the loop; UserPromptSubmit, SessionStart and SessionEnd hooks
│   ├── hooks.py                      hooks: reads hooks.json, runs commands and functions per event
│   ├── context.py                    the late injection block, with a <hooks> tag
│   ├── commands.py                   slash commands; PreCompact runs first, /hooks lists the config
│   ├── mcp_client.py                 MCP client: starts each server over stdio, registers its tools
│   ├── permissions.py                allow / ask / deny per tool call, MCP tools included
│   ├── memory.py                     persistent memory: markdown files with front matter
│   ├── compact.py                    the compaction agent; its handoff note is kept
│   ├── history.py                    transcript trimming: cap, strip, fit, image messages
│   ├── subagent.py                   the subagent loop shared by task and browse
│   ├── browse.py                     the browser subagent
│   ├── browser.py                    browser tools: one Chromium page through Playwright
│   ├── computer.py                   computer use: screen size, screenshot, act
│   ├── todos.py                      the plan: write_todos and the todo list
│   ├── skills.py                     skills: SKILL.md discovery and index
│   ├── session.py                    append-only JSONL log, load() with repair, /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash, and the process-group plumbing
│   ├── config.py                     settings: environment first, ~/.simple-harness/env fills gaps
│   ├── prompt.py                     the input line, through prompt_toolkit
│   ├── ui.py                         rich panels; streams the reply, headless() sends panels to stderr
│   └── __init__.py                   package marker
├── .agents/
│   ├── hooks.json                    hook config: block .env writes, log every tool name
│   ├── block_env_writes.py           example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: appends every tool name to a log
│   ├── .gitignore                    ignores tool_log.txt, the log hook's output
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.27.0
└── README.md                         this file
```

## What the next step adds

Step 28 adds plan mode: a `/plan` command that offers the model only
read-only tools plus `submit_plan`, shows you the plan, and switches
back to act mode only once you approve it.

## Diff from step 26

```bash
diff -r ../step_26_mcp_client/harness harness
```

Added: `hooks.py` (`read_config`, `load_config`, `matches`,
`run_command`, `run_python`, `run_hook`, `run_hooks`, `session_start`,
`HookOutcome`). Changed: `tools.py` (`decide` runs `PreToolUse` and can
answer `blocked`; `run` runs `PostToolUse` and can replace or reject the
result and append hook context; `settle` knows the new verdict),
`agent.py` (`UserPromptSubmit` in `turn`, `SessionStart` and `SessionEnd`
in `main`), `context.py` (`hooks_note`, the `<hooks>` tag,
`reminder(hook_context)`), `commands.py` (`PreCompact` in `compact`, the
`/hooks` command), `llm.py` (system prompt). Added in `.agents/`:
`hooks.json`, `block_env_writes.py`, `log_tool_use.py`.

<!-- harness-learning-check -->
## Check your understanding

A hook file exists. What establishes that it affected the operation?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

Find the relevant lifecycle invocation and its observed effect. File presence alone does not prove execution.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
