# Step 27 - Hooks

**What this step adds:** hooks. A hook is a small program the user
configures in `hooks.json`, and the harness runs it at a fixed point in
the loop: before and after every tool call, when a prompt is submitted,
before compaction, and at session start and end. A hook can block a tool
call, replace its result, or add text to the late block. Two example hooks
ship in `.agents/`: one refuses edits to `.env` files, one logs every tool
name to a file.

## Why hooks

Every rule in the harness so far is code. The permission table in
`permissions.py` decides which commands ask. The sandbox decides which
paths a command may touch. To add a rule, the user edits the harness.

Most rules a team wants are small and local. Never write to this file.
Run the formatter after every edit. Log every tool call for an audit.
Remind the model of the branch policy on every prompt. None of these
belong in the harness, because the next project wants different ones.

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

Two files, one for the user and one for the project, and both are read
on every event. The lists are merged per event, so the user file runs
first and the project file after it. Each entry is a hook: an optional
`matcher`, and either a `command` or a `python` string.

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
    return any(fnmatch(tool_name, part.strip()) for part in pattern.split("|") if part.strip())
```

### 2. Running a command hook

`harness/hooks.py`:

```python
def run_command(command, event):
    """Run a shell hook with the event on stdin. Returns a reply dict or None.

    shell=True so `python .agents/check.py` works the same on Windows and
    elsewhere. Exit 0 with JSON on stdout is a reply; exit 2 blocks with
    stderr as the reason; anything else is reported and ignored.
    """
    completed = subprocess.run(
        resolve_python(command),
        shell=True,
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        cwd=event.get("cwd") or None,
    )
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
keys: `event`, `tool_name`, `tool_input`, `tool_result`, `prompt` and
`cwd`, with `null` for the ones that do not apply. The answer comes back
in two channels. The exit code says whether to continue: `0` continues,
`2` blocks, and stderr is the reason. Stdout, when not empty, is a JSON
reply: `{"result": ...}` replaces a tool result, `{"context": ...}` adds
text to the late block, and `{"block": "reason"}` blocks too.

The subprocess runs with `shell=True`, so the command is one string, as
the user wrote it. A command that starts with `python` runs under the
harness's own interpreter. The shipped hooks depend on that: they are
Python scripts, so they run on every operating system, and the harness
already knows one Python that works.

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
    args = json.loads(tool_call.function.arguments)
    action, reason = check(tool_call.function.name, args)
    if action == "deny":
        return args, action, reason
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": tool_call.function.name, "tool_input": args})
    if outcome.blocked:
        return args, "blocked", outcome.reason
    return args, action, reason
```

`decide()` gains a fourth verdict. After the permission rules rate the
call, the `PreToolUse` hooks see its name and arguments. A block becomes
the verdict `blocked`, and `settle()` turns that into the tool result
`Blocked by hook: <reason>`. The tool never runs, and the model reads the
reason. A call the rules already denied is not offered to the hooks.

The hook runs before the `allow? (y/n)` prompt, not after. A hook that
blocks saves the user a question. A hook that lets the call through
leaves the question where it was.

`harness/tools.py`:

```python
def run(tool_call, args):
    """Run the tool with already-parsed arguments, then the PostToolUse hooks.

    No permission check here. A hook that answers with a result replaces
    what the tool returned; the model sees the hook's version.
    """
    result = TOOLS[tool_call.function.name](**args)
    outcome = hooks.run_hooks("PostToolUse", {"tool_name": tool_call.function.name, "tool_input": args, "tool_result": result})
    if outcome.result is not None:
        return outcome.result if isinstance(outcome.result, str) else json.dumps(outcome.result)
    return result
```

`run()` calls the tool and then the `PostToolUse` hooks, with the result
in the event. A hook that answers with `result` replaces it. Both hook
points sit on the shared path: `execute()`, `execute_all()`, and the
subagent loop all go through `decide()` and `run()`, so a subagent and a
parallel batch are hooked the same way as a single call on the main
thread.

### 6. The turn and the session

`harness/agent.py`:

```python
    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    messages.append({"role": "user", "content": user_input})

    while True:
        injection = reminder(hook_context=submitted.context)
```

The `UserPromptSubmit` hooks see the prompt before it joins the history.
Their context is handed to `reminder()`, which puts it in a `<hooks>` tag
in the late block for every model call of that turn. The next turn starts
clean.

`harness/context.py`:

```python
def hooks_note(turn_context=""):
    """Text the hooks asked to add: the session's, then this turn's."""
    text = "\n".join(part for part in SESSION_CONTEXT + [turn_context] if part).strip()
    return f"\n<hooks>\n{text}\n</hooks>" if text else ""
```

`SessionStart` runs once, before the first prompt, and its context is
kept in `SESSION_CONTEXT` for the whole session. `SessionEnd` runs on
the way out, after the browser and the MCP servers are closed.
`PreCompact` runs at the top of `commands.compact()`, and a block keeps
the transcript as it is.

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
`str_replace`, so a `read_file` of the same path is not affected.

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

```bash
harness
> /hooks
```

The list shows the two shipped hooks, their event and their matcher. Ask
for something the first one refuses:

```bash
> create a .env file with API_KEY=test
```

The tool panel for `write_file` shows `Blocked by hook: .env holds
secrets; edit it by hand, not through the agent`, and the model tells you
so instead of retrying. Ask for anything else and then look at the log:

```bash
> list the python files here
> /hooks
```

```bash
cat .agents/tool_log.txt
```

One line per tool call, with the time and the name.

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

## Diff from step 26

```bash
diff -r ../step_26_mcp_client/harness harness
```

Added: `hooks.py` (`load_config`, `matches`, `run_command`, `run_python`,
`run_hook`, `run_hooks`, `session_start`, `HookOutcome`). Changed:
`tools.py` (`decide` runs `PreToolUse` and can answer `blocked`; `run`
runs `PostToolUse` and can replace the result; `settle` knows the new
verdict), `agent.py` (`UserPromptSubmit` in `turn`, `SessionStart` and
`SessionEnd` in `main`), `context.py` (`hooks_note`, the `<hooks>` tag,
`reminder(hook_context)`), `commands.py` (`PreCompact` in `compact`, the
`/hooks` command), `llm.py` (system prompt). Added in `.agents/`:
`hooks.json`, `block_env_writes.py`, `log_tool_use.py`.
