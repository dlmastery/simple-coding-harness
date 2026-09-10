"""Tools: what the model can ask us to do, and the code that does it."""

import json
import subprocess

from . import history, sandbox
from .permissions import check
from .skills import read_skill
from .subagent import TASK_SCHEMA, task
from .todos import TODO_SCHEMA, write_todos


def bash(command: str) -> str:
    """Run a shell command and return its stdout and stderr."""
    try:
        result = sandbox.run(command)
    except subprocess.TimeoutExpired as expired:
        # A slow command is the model's problem to work around, not a reason
        # to take the session down. Hand it back as a result.
        return f"Timed out after {expired.timeout}s and was killed. Narrow the command down."
    return history.cap((result.stdout + result.stderr) or "(no output)")


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path, encoding="utf-8") as f:
        return history.cap(f.read())


def write_file(path: str, content: str) -> str:
    """Create a file with the given content, overwriting it if it exists."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {path}"


def str_replace(path: str, old_str: str, new_str: str, allow_multi: bool = False) -> str:
    """Replace exact text in a file. old_str must appear exactly once unless allow_multi."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}. Read the file again and copy the text exactly."
    if count > 1 and not allow_multi:
        return (
            f"Error: old_str matches {count} times in {path}. Include surrounding "
            "lines to make it unique, or set allow_multi to replace them all."
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} occurrence(s) in {path}"


def schema(tool, description, required=None, **params):
    """Build a function-tool schema.

    A parameter given as a string is a required string with that description.
    A parameter given as a dict is used as-is (for booleans, enums, ...).
    `required` lists the required names; by default every parameter is.
    """
    properties = {
        p: ({"type": "string", "description": spec} if isinstance(spec, str) else spec)
        for p, spec in params.items()
    }
    return {
        "type": "function",
        "function": {
            "name": tool,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(params) if required is None else list(required),
            },
        },
    }


TOOLS = {
    "bash": (bash, schema("bash", bash.__doc__, command="The command to run")),
    "read_file": (read_file, schema("read_file", read_file.__doc__, path="Path to the file")),
    "read_skill": (read_skill, schema("read_skill", read_skill.__doc__, name="Name of the skill")),
    "write_file": (
        write_file,
        schema("write_file", write_file.__doc__, path="File to write", content="The full contents"),
    ),
    "str_replace": (
        str_replace,
        schema(
            "str_replace",
            str_replace.__doc__,
            required=["path", "old_str", "new_str"],
            path="File to edit",
            old_str="Exact text to find (include enough lines to be unique)",
            new_str="Text to put in its place",
            allow_multi={"type": "boolean", "description": "Replace every match instead of failing"},
        ),
    ),
    "write_todos": (write_todos, TODO_SCHEMA),
    "task": (task, TASK_SCHEMA),
}
TOOL_SCHEMAS = [s for _, s in TOOLS.values()]


def execute(call):
    """Turn a tool call into (args, result), through the permission layer.

    Everything in a tool call is text the model wrote: the name may not
    exist, the arguments may not be JSON, the file may not be there. Each of
    those becomes a result string the model can read and recover from.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    name = call.function.name
    try:
        args = json.loads(call.function.arguments)
    except json.JSONDecodeError as broken:
        return {}, f"Error: arguments were not valid JSON ({broken})."

    if name not in TOOLS:
        return args, f"Error: no tool named '{name}'. Available: {', '.join(TOOLS)}."

    fn, _ = TOOLS[name]
    try:
        action, reason = check(name, args)
        if action == "deny":
            return args, f"Blocked by policy: {reason}"
        if action == "ask" and not ui.approve(reason):
            return args, "The user declined this tool call."
        return args, fn(**args)
    except TypeError as mismatch:
        return args, f"Error: wrong arguments for {name} ({mismatch})."
    except Exception as failure:  # noqa: BLE001 - the model gets to see it and retry
        return args, f"Error: {name} failed - {type(failure).__name__}: {failure}"
