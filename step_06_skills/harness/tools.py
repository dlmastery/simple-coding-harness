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


def schema(tool, description, **params):
    """Build a function-tool schema. Every parameter is a required string."""
    return {
        "type": "function",
        "function": {
            "name": tool,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {p: {"type": "string", "description": d} for p, d in params.items()},
                "required": list(params),
            },
        },
    }


TOOLS = {
    "bash": (bash, schema("bash", bash.__doc__, command="The command to run")),
    "read_file": (read_file, schema("read_file", read_file.__doc__, path="Path to the file")),
    "read_skill": (read_skill, schema("read_skill", read_skill.__doc__, name="Name of the skill")),
}
TOOL_SCHEMAS = [s for _, s in TOOLS.values()]


def execute(call):
    """Turn a tool call from the model into (args, result string)."""
    fn, _ = TOOLS[call.function.name]
    args = json.loads(call.function.arguments)
    return args, fn(**args)
