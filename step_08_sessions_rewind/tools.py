"""Stage 8 - tools, unchanged from stage 7.

The file tools still call note_seen; context.py now records a content hash
there instead of an mtime, and session.py keeps SEEN with the chat.
"""

import json
import os
import signal
import subprocess

from context import note_seen
from skills import read_skill

TIMEOUT = 60
# no pagers, no credential prompts: the command has no terminal to answer on
BASH_ENV = {**os.environ, "PAGER": "cat", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"}
# the command starts its own process group, so a timeout can kill all of it
NEW_GROUP = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}


def kill_tree(pid):
    """Kill a process and everything it started."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        os.killpg(pid, signal.SIGKILL)


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    proc = subprocess.Popen(
        command, shell=True, stdin=subprocess.DEVNULL,  # no stdin: an interactive command ends, it does not wait
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",             # never a UnicodeDecodeError on odd output
        env=BASH_ENV, **NEW_GROUP,
    )
    try:
        out, err = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        proc.communicate()
        return f"Error: command timed out after {TIMEOUT}s"
    return (out + err) or "(no output)"


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    # utf-8 whatever the console code page; newline="" keeps CRLF and LF as they are
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        content = f.read()
    note_seen(path)
    return content


def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)  # a new file in a new folder is one call
    with open(path, "w", encoding="utf-8", newline="") as f:  # written as given: no newline translation
        f.write(content)
    note_seen(path)
    return f"Wrote {path}"


def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    if not old_str:
        return "Error: old_str is empty"
    if not os.path.isfile(path):
        return f"Error: {path} does not exist"
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
    note_seen(path)
    return f"Replaced {count} match(es) in {path}"


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
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": "Open a skill by name and return its full instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the skill to open"},
                },
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
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "read_skill": read_skill,
}


def run_tool(tool_call):
    """Turn one tool call into (args, result). Never raises: whatever goes
    wrong becomes the result string, so the model reads it and tries again."""
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:  # the model wrote broken JSON
        return {}, f"Error: the arguments of {name} are not a JSON object: {e}"
    if name not in TOOLS:  # a name that is not in the table
        return args, f"Error: no tool named {name!r}."
    try:
        result = TOOLS[name](**args)  # name -> function, JSON -> kwargs
    except Exception as e:  # wrong arguments, missing file, anything the tool raises
        return args, f"Error: {type(e).__name__}: {e}"
    if not isinstance(result, str):  # a tool message must be text
        result = "(no output)" if result is None else json.dumps(result, default=str)
    return args, result
