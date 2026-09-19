"""Step 33 - hooks, with a built-in list. BUILTIN holds the hooks the
harness registers itself; they run before every hook from the config
files, for the same events and in the same shape. The checkpoint capture
of step 33 is no longer one of them: it runs inside tools.run(), after the
approval, so a call the user declines captures nothing. The rest is step 27.

A hook is configured, not coded into the harness. Two files are read,
`~/.simple-harness/hooks.json` and `./.agents/hooks.json`, and their lists
are merged per event:

    {"PreToolUse": [{"matcher": "bash|write_*", "command": "python check.py"}],
     "PostToolUse": [...], "UserPromptSubmit": [...], "PreCompact": [...],
     "SessionStart": [...], "SessionEnd": [...]}

A hook is either a `command` (a shell line; the JSON event arrives on
stdin) or a `python` entry (`"module:function"`, imported and called with
the event dict). Both answer the same way: nothing, to let the loop
continue; `{"block": "reason"}` to stop the action; `{"result": ...}` to
replace a tool result; `{"context": ...}` to add text to the late block. A
command may also block by exiting with code 2, with stderr as the reason.

A hook that crashes, times out or prints something that is not JSON is
reported with a note and ignored. The loop never dies because of a hook.
The PostToolUse event carries `ok`, false when the result starts with
Error:, so a hook can react to a failed call.
"""

import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

from . import sandbox

EVENTS = ("PreToolUse", "PostToolUse", "UserPromptSubmit", "PreCompact", "SessionStart", "SessionEnd")

CONFIG_PATHS = [
    Path.home() / ".simple-harness" / "hooks.json",
    Path.cwd() / ".agents" / "hooks.json",
]

TIMEOUT = 30  # seconds a command hook may take before it is killed and ignored

BLOCK_EXIT_CODE = 2  # a command hook exits with this to block; stderr is the reason

EVENT_KEYS = ("event", "tool_name", "tool_input", "tool_result", "ok", "prompt", "cwd")

SESSION_CONTEXT = []  # what the SessionStart hooks asked to add to every late block

BUILTIN = {}  # the harness's own hooks; same shape as a config entry, run first (none since the capture moved into tools.run)

CACHE = {}  # config path -> (mtime, parsed): a hooks.json is read once per change, not once per tool call


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
            stamp = path.stat().st_mtime_ns
            if path in CACHE and CACHE[path][0] == stamp:
                data = CACHE[path][1]
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
                CACHE[path] = (stamp, data)
        except (OSError, ValueError) as failed:
            _note(f"hook config {path} skipped: {failed}")
            continue
        if not isinstance(data, dict):
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
    return any(fnmatchcase(tool_name, part.strip()) for part in pattern.split("|") if part.strip())


def describe(hook):
    """A short name for a hook, for notes."""
    return hook.get("command") or hook.get("python") or "(empty hook)"


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
    process = subprocess.Popen(
        resolve_python(command),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        cwd=event.get("cwd") or None,
        **sandbox.NEW_GROUP,  # its own process group, so a timeout kills what it started too
    )
    try:
        stdout, stderr = process.communicate(json.dumps(event), timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        sandbox.kill_tree(process.pid)
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
        _note(f"hook without command or python skipped: {hook}")
    except subprocess.TimeoutExpired:
        _note(f"hook `{describe(hook)}` took more than {TIMEOUT}s and was ignored")
    except Exception as failed:  # noqa: BLE001 - a broken hook must not take the loop down
        _note(f"hook `{describe(hook)}` failed and was ignored: {type(failed).__name__}: {failed}")
    return None


def run_hooks(event_name, event=None):
    """Run every hook registered for the event, built-in first, then config order.

    Returns a HookOutcome. The first hook that blocks ends the run.
    Otherwise the last `result` wins and every `context` is kept, one per
    line.
    """
    event = {key: None for key in EVENT_KEYS} | (event or {})
    event["event"] = event_name
    event["cwd"] = event["cwd"] or os.getcwd()

    outcome = HookOutcome()
    for hook in BUILTIN.get(event_name, []) + load_config().get(event_name, []):
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


def _note(text):
    from .ui import ui  # here, not at the top: ui imports todos, tools imports hooks

    ui.note(text)
