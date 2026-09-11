"""Stage 2.4 - tools, unchanged from 2.3.

"All that I have done here is just this def read_file which opens a path
and reads it and returns it back to the agent."
"""

import subprocess


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
    return (result.stdout + result.stderr) or "(no output)"


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path) as f:
        return f.read()


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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
]

TOOLS = {"bash": bash, "read_file": read_file}
