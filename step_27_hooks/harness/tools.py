"""Step 27 - two hook points around every tool call. decide() runs the
PreToolUse hooks after the permission check, and a hook can block the call.
run() runs the PostToolUse hooks after the tool, and a hook can replace the
result. Both hook points sit on the shared path, so subagents and parallel
calls go through them too.

TOOLS is what can run; TOOL_SCHEMAS is what the main agent is offered. The
browser tools are in the first and not the second: only the browse subagent
is offered them. The computer tools and the memory tools are in both, and
the MCP tools join both when their servers start.
"""

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import browser, computer, history, hooks, memory, sandbox
from .browse import BROWSE_SCHEMA, browse
from .permissions import check
from .skills import read_skill
from .subagent import TASK_SCHEMA, task
from .todos import TODO_SCHEMA, write_todos


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    try:
        result = sandbox.run(command)
    except subprocess.TimeoutExpired as expired:
        # A slow command is the model's problem to work around, not a reason
        # to take the session down. Hand the failure back as a result.
        partial = (expired.output or "") + (expired.stderr or "")
        return history.cap(f"Timed out after {expired.timeout}s and was killed. Output so far:\n{partial}")
    return history.cap((result.stdout + result.stderr) or "(no output)")


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return history.cap(f.read())


def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return f"Wrote {path}"


def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    if not old_str:
        return "Error: old_str is empty; give the exact text to replace"
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Add surrounding lines to make it unique, "
            "or set allow_multi_edit to replace them all."
        )

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {path}"


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The shell command to run"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path to the file to read"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": "Open a skill by name and return its full instructions.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name of the skill to open"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a file, or overwrite it if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to write"},
                    "content": {"type": "string", "description": "The full contents"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace exact text in a file. old_str must appear exactly once, "
                "so include surrounding lines if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to edit"},
                    "old_str": {"type": "string", "description": "Exact text to find"},
                    "new_str": {"type": "string", "description": "Text to put in its place"},
                    "allow_multi_edit": {"type": "boolean", "description": "Replace every match instead of failing"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    TODO_SCHEMA,
    TASK_SCHEMA,
    BROWSE_SCHEMA,
    *computer.COMPUTER_SCHEMAS,
    *memory.MEMORY_SCHEMAS,
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "read_skill": read_skill,
    "write_todos": write_todos,
    "task": task,
    "browse": browse,
    **browser.TOOLS,  # runnable, but offered only to the browse subagent
    **computer.COMPUTER_TOOLS,
    **memory.MEMORY_TOOLS,
}


MAX_WORKERS = 4  # tool calls of one reply that may run at the same time

DENIED = "The user denied this tool call."

# tools that must run one at a time on the calling thread: they prompt the
# user, or drive a browser or desktop whose call order matters
SERIAL = {"task", "browse", "submit_plan", "ask_user", "handoff_to", "finish"}


def serial(name):
    return name in SERIAL or name.startswith(("browser_", "computer_"))


def decide(tool_call, allowed=None):
    """Parse the arguments and rate the call. Returns (args, action, reason).

    Nothing runs here. This is the half of execute() that must stay on the
    main thread, because an `ask` verdict turns into a prompt. Arguments
    that are not a JSON object are the verdict `error`: the call never runs
    and the reason becomes its result. `allowed`, when given, is the set of
    tool names this caller was offered; anything else is denied. The verdict
    is allow, ask or deny from the rules, or `blocked` from a PreToolUse
    hook. A denied call is not offered to the hooks: the rules said no first.
    """
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError(f"got {type(args).__name__}")
    except ValueError as failed:
        return {}, "error", f"Error: the arguments of {name} are not a JSON object: {failed}"
    if allowed is not None and name not in allowed:
        return args, "deny", f"{name} is not available to this agent"
    action, reason = check(name, args)
    if action == "deny":
        return args, action, reason
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": tool_call.function.name, "tool_input": args})
    if outcome.blocked:
        return args, "blocked", outcome.reason
    return args, action, reason


def call(name, args):
    """Call the tool function itself. Returns a string, whatever happens.

    A tool that raises does not take the loop down: the exception becomes an
    Error: result the model can read, the way a failed command does.
    """
    tool = TOOLS.get(name)
    if tool is None:
        return f"Error: no tool named {name!r}."
    try:
        result = tool(**args)
    except Exception as failed:  # noqa: BLE001 - a missing file or a wrong argument is the model's problem to fix
        return f"Error: {type(failed).__name__}: {failed}"
    if not isinstance(result, str):
        result = "(no output)" if result is None else json.dumps(result, default=str)
    return result


def run(tool_call, args):
    """Run the tool with already-parsed arguments, then the PostToolUse hooks.

    No permission check here. A hook that answers with a result replaces
    what the tool returned; the model sees the hook's version.
    """
    result = call(tool_call.function.name, args)
    outcome = hooks.run_hooks("PostToolUse", {"tool_name": tool_call.function.name, "tool_input": args, "tool_result": result})
    if outcome.result is not None:
        return outcome.result if isinstance(outcome.result, str) else json.dumps(outcome.result)
    return result


def settle(action, reason):
    """Turn a verdict into a result string, or None when the call may run.

    An `error` is a call that could not be parsed; its reason is the result.
    A `deny` never runs, and neither does a call a hook `blocked`. An `ask`
    prompts the user and runs only on yes.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if action == "error":
        return reason
    if action == "deny":
        return f"Blocked by policy: {reason}"
    if action == "blocked":
        return f"Blocked by hook: {reason}"
    if action == "ask" and not ui.approve(reason):
        return DENIED
    return None


def execute(tool_call, allowed=None):
    """Run one tool call through the permission layer. Returns (args, result).

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. This is decide,
    settle and run in one step, for callers that want the direct path.
    """
    args, action, reason = decide(tool_call, allowed)
    result = settle(action, reason)
    if result is not None:
        return args, result
    return args, run(tool_call, args)


def execute_all(tool_calls, allowed=None):
    """Run every tool call of one reply. Returns [(args, result)] in the same order.

    One call takes the direct path. Several calls are decided first, one at a
    time on this thread, so the prompts appear in order. Then the allowed
    ones run together in a thread pool. A denied or declined call gets its
    message as the result and never runs. A batch that holds a SERIAL tool
    runs one call after another on this thread instead: those tools prompt
    the user or drive one browser, and neither works from a pool.
    """
    if len(tool_calls) == 1 or any(serial(c.function.name) for c in tool_calls):
        return [execute(tool_call, allowed) for tool_call in tool_calls]

    outcomes = []  # (args, result) per call; result is None until it has run
    for tool_call in tool_calls:
        args, action, reason = decide(tool_call, allowed)
        outcomes.append((args, settle(action, reason)))

    pending = [i for i, (_, result) in enumerate(outcomes) if result is None]
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    try:
        futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
        for i, future in futures.items():
            outcomes[i] = (outcomes[i][0], future.result())
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # queued calls never start
        raise
    pool.shutdown(wait=True)
    return outcomes
