"""Step 43 - hooks are an extension. apply(ctx) registers the harness's
own hooks from BUILTIN through ctx.hook, and the /hooks command through
ctx.command. run_hooks runs the registered hooks first - the built-in
ones and every hook an extension added - then the hooks from the config
files, in the same shape as before. A registered hook is a function
called with the event dict; it answers like a python hook.
The rest is step 41: the Stop event joins the list. Its hooks run when a turn is
about to end, with the answer and every tool call of the turn in the
event; a hook that exits 2 blocks the stop and its stderr goes back to
the agent as a user message (see stop.py). The rest is step 33: hooks
with a built-in list. BUILTIN holds the hooks the
harness registers itself; they run before every hook from the config
files, for the same events and in the same shape. Step 33 adds one: the
checkpoint capture on PreToolUse. The rest is step 27.

A hook is configured, not coded into the harness. Two files are read,
`~/.simple-harness/hooks.json` and `./.agents/hooks.json`, and their lists
are merged per event:

    {"PreToolUse": [{"matcher": "bash|write_*", "command": "python check.py"}],
     "PostToolUse": [...], "UserPromptSubmit": [...], "PreCompact": [...],
     "SessionStart": [...], "SessionEnd": [...], "Stop": [...]}

A hook is either a `command` (a shell line; the JSON event arrives on
stdin) or a `python` entry (`"module:function"`, imported and called with
the event dict). Both answer the same way: nothing, to let the loop
continue; `{"block": "reason"}` to stop the action; `{"result": ...}` to
replace a tool result; `{"context": ...}` to add text to the late block. A
command may also block by exiting with code 2, with stderr as the reason.

A hook that crashes, times out or prints something that is not JSON is
reported with a note and ignored. The loop never dies because of a hook.
"""

import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from . import extensions

EVENTS = ("PreToolUse", "PostToolUse", "UserPromptSubmit", "PreCompact", "SessionStart", "SessionEnd", "Stop")

CONFIG_PATHS = [
    Path.home() / ".simple-harness" / "hooks.json",
    Path.cwd() / ".agents" / "hooks.json",
]

TIMEOUT = 30  # seconds a command hook may take before it is killed and ignored

BLOCK_EXIT_CODE = 2  # a command hook exits with this to block; stderr is the reason

EVENT_KEYS = ("event", "tool_name", "tool_input", "tool_result", "prompt", "cwd", "answer", "calls", "blocks", "ended_by")  # the last four: Stop

SESSION_CONTEXT = []  # what the SessionStart hooks asked to add to every late block

BUILTIN = {  # the harness's own hooks; same shape as a config entry, registered by apply() and run first
    "PreToolUse": [{"matcher": "write_file|str_replace", "python": "harness.checkpoint:pre_tool_use"}],
}


def apply(ctx):
    """The hooks extension: the harness's own hooks, and the /hooks command."""
    for event, found in BUILTIN.items():
        for hook in found:
            ctx.hook(event, python_hook(hook["python"]), hook.get("matcher") or "*")
    ctx.command("/hooks", "list the hooks configured for each event", list_command)


def python_hook(target):
    """A function hook that imports `module:function` on its first call, named after the target."""

    def hook(event):
        return run_python(target, event)

    hook.__name__ = target
    return hook


@dataclass
class HookOutcome:
    """What the hooks of one event decided, merged."""

    blocked: bool = False
    reason: str = ""
    result: object = None  # a replacement tool result, or None to keep the real one
    context: str = ""      # text for the late block, empty when no hook added any


def load_config(paths=None):
    """Merge every hooks.json that exists. Returns {event name: [hook, ...]}."""
    merged = {event: [] for event in EVENTS}
    for path in paths if paths is not None else CONFIG_PATHS:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as failed:
            _note(f"hook config {path} skipped: {failed}")
            continue
        for event, hooks in data.items():
            if event in merged and isinstance(hooks, list):
                merged[event] += [h for h in hooks if isinstance(h, dict)]
    return merged


def matches(hook, tool_name):
    """Does this hook apply to the tool? The matcher is `glob|glob`; `*` or none means all."""
    pattern = str(hook.get("matcher") or "*")
    if tool_name is None:  # an event without a tool: every hook of that event runs
        return True
    return any(fnmatch(tool_name, part.strip()) for part in pattern.split("|") if part.strip())


def describe(hook):
    """A short name for a hook, for notes: its command, its python target, or its function's name."""
    function = hook.get("function")
    return hook.get("command") or hook.get("python") or getattr(function, "__name__", None) or "(empty hook)"


def resolve_python(command):
    """A command that starts with `python` runs under this interpreter.

    The shipped hooks are Python scripts. On a machine where `python` is not
    on PATH, or means another install, the harness's own interpreter is the
    one that is known to exist.
    """
    word, _, rest = command.strip().partition(" ")
    if word in ("python", "python3"):
        return f'"{sys.executable}" {rest}'.strip()
    return command


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


def run_hook(hook, event):
    """Run one hook of either kind. A failure becomes a note, never an exception."""
    try:
        if hook.get("command"):
            return run_command(hook["command"], event)
        if hook.get("python"):
            return run_python(hook["python"], event)
        if hook.get("function"):
            reply = hook["function"](event)
            return reply if isinstance(reply, dict) else None
        _note(f"hook without command or python skipped: {hook}")
    except subprocess.TimeoutExpired:
        _note(f"hook `{describe(hook)}` took more than {TIMEOUT}s and was ignored")
    except Exception as failed:  # noqa: BLE001 - a broken hook must not take the loop down
        _note(f"hook `{describe(hook)}` failed and was ignored: {type(failed).__name__}: {failed}")
    return None


def run_hooks(event_name, event=None):
    """Run every hook of the event: the registered ones first, then the config files' in order.

    The registered hooks are the harness's own from BUILTIN and every hook
    an extension added, in registration order. Returns a HookOutcome. The
    first hook that blocks ends the run. Otherwise the last `result` wins
    and every `context` is kept, one per line.
    """
    event = {key: None for key in EVENT_KEYS} | (event or {})
    event["event"] = event_name
    event["cwd"] = event["cwd"] or os.getcwd()

    outcome = HookOutcome()
    for hook in extensions.hooks_for(event_name) + load_config().get(event_name, []):
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


def session_start():
    """Run the SessionStart hooks and keep their context for the whole session."""
    outcome = run_hooks("SessionStart")
    if outcome.context:
        SESSION_CONTEXT.append(outcome.context)
    return outcome


def list_command(messages, arg=""):
    """/hooks: every hook grouped by event, the registered ones with their source, then the config files'."""
    from .ui import ui  # here, not at the top: ui imports todos, tools imports hooks

    rows = [f"{event:<18} {hook.get('matcher') or '*':<24} {describe(hook)}  ({extensions.label(hook['source'])})" for event in EVENTS for hook in extensions.hooks_for(event)]
    rows += [f"{event:<18} {hook.get('matcher') or '*':<24} {describe(hook)}" for event, found in load_config().items() for hook in found]
    ui.note("\n".join(rows) if rows else "no hooks configured (see .agents/hooks.json)")
    return messages


def _note(text):
    from .ui import ui  # here, not at the top: ui imports todos, tools imports hooks

    ui.note(text)
