"""Tools: what the model can ask us to do, and the code that does it."""

import json
import subprocess

from .skills import read_skill


def bash(command: str) -> str:
    """Run a shell command and return its stdout and stderr."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return (result.stdout + result.stderr) or "(no output)"


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path, encoding="utf-8") as f:
        return f.read()


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
}
TOOL_SCHEMAS = [s for _, s in TOOLS.values()]


def execute(call):
    """Turn a tool call into (args, result). Never raises.

    Everything in a tool call is text the model wrote: the name may not exist,
    the arguments may not be JSON, the file may not be there. Each of those
    becomes a result string the model can read and recover from. A crash here
    would take the whole session down over one bad guess.
    """
    name = call.function.name
    try:
        args = json.loads(call.function.arguments)
    except json.JSONDecodeError as broken:
        return {}, f"Error: arguments were not valid JSON ({broken})."

    if name not in TOOLS:
        return args, f"Error: no tool named '{name}'. Available: {', '.join(TOOLS)}."

    fn, _ = TOOLS[name]
    try:
        return args, fn(**args)
    except TypeError as mismatch:
        return args, f"Error: wrong arguments for {name} ({mismatch})."
    except Exception as failure:  # noqa: BLE001 - the model gets to see it and retry
        return args, f"Error: {name} failed - {type(failure).__name__}: {failure}"
