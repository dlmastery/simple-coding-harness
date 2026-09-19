"""Stage 2.2 - tools live in their own file.

Two things per tool: the Python function and the schema the model sees.
TOOLS maps a name to the function; TOOL_SCHEMAS is what goes on the
request. Adding a tool means adding one of each, and nothing in llm.py
changes. run_tool is the one place a tool call is turned into a result.
"""

import json
import os
import signal
import subprocess

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
