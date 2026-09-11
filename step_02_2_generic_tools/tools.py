"""Stage 2.2 - tools live in their own file.

Two things per tool: the Python function and the schema the model sees.
TOOLS maps a name to the function; TOOL_SCHEMAS is what goes on the
request. Adding a tool means adding one of each, and nothing in llm.py
changes.
"""

import subprocess


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
    return (result.stdout + result.stderr) or "(no output)"


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run",
                    }
                },
                "required": ["command"],
            },
        },
    }
]

TOOLS = {"bash": bash}
