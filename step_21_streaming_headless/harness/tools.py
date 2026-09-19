"""Stage 15 - tools gain the task subagent and execute(), the one permission-checked
entry point the main loop and the subagent both use.

execute() never raises. Bad arguments, an unknown tool name and an exception
inside a tool all come back as an "Error: ..." string, so every tool call
the model makes gets exactly one tool message - the API rejects a transcript
where one is missing.
"""

import json
import os
import subprocess

from . import history, sandbox
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
        partial = (expired.stdout or "") + (expired.stderr or "")
        return history.cap(f"Timed out after {expired.timeout}s and was killed. Output so far:\n{partial}")
    return history.cap((result.stdout + result.stderr) or "(no output)")


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    if not os.path.isfile(path):
        return f"Error: {path} is not a file."
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return history.cap(f.read())


def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return f"Wrote {path}"


def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    if not old_str:
        return "Error: old_str is empty."
    if not os.path.isfile(path):
        return f"Error: {path} is not a file."
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
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "read_skill": read_skill,
    "write_todos": write_todos,
    "task": task,
}


def parse_args(tool_call):
    """The arguments as a dict, or (partial dict, error string) when they are not one."""
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError as bad:
        return {}, f"Error: the arguments of {name} are not a JSON object: {bad}"
    if not isinstance(args, dict):
        return {}, f"Error: the arguments of {name} are not a JSON object: got {type(args).__name__}"
    return args, None


def as_text(result):
    """Tool results are strings. Anything else is made into one."""
    if isinstance(result, str):
        return result
    return "(no output)" if result is None else json.dumps(result, default=str)


def execute(tool_call, allowed=None):
    """Run one tool call through the permission layer. Returns (args, result).

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. `allowed` is the
    set of tool names the caller offered; anything else is refused, so a
    subagent cannot run a tool by naming it.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    name = tool_call.function.name
    args, problem = parse_args(tool_call)
    if problem:
        return args, problem
    if allowed is not None and name not in allowed:
        return args, f"Blocked by policy: {name} is not available to this agent"
    action, reason = check(name, args)
    if action == "deny":
        return args, f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return args, "The user denied this tool call."
    tool = TOOLS.get(name)
    if tool is None:
        return args, f"Error: no tool named {name!r}."
    try:
        return args, as_text(tool(**args))
    except Exception as failed:  # noqa: BLE001 - a broken tool is a result, not a crash
        return args, f"Error: {type(failed).__name__}: {failed}"
