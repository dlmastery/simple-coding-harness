"""Stage 2.1 - chat with a simple bash tool.

The model can now ask the harness to run a shell command. The tool is
described as JSON and passed in `tools=`. If the reply carries a tool call,
the harness runs it. The result is printed for the user, not sent back to
the model - that is 2.4.

Run:   python llm.py
Needs: BASE_URL, API_KEY (and optionally MODEL) in the environment.
"""

import json
import os
import signal
import subprocess
import sys

import openai
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)

MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

try:
    user_input = input("Enter your prompt> ")
except (EOFError, KeyboardInterrupt):
    sys.exit("\nno prompt given")

SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Answer back to the user once exploration is done.
"""

# "It's basically a JSON that sort of explains what the tool shape is going
# to be." The description is what the model reads to decide when to call it.
BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command and return its output.",
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


def bash(command):
    """The Python behind the schema. A subprocess executes what the model chose."""
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


try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        tools=[BASH_TOOL],  # the only change to the request
    )
except openai.APIError as e:
    sys.exit(f"model call failed: {e}")

if not response.choices:
    sys.exit(f"empty reply: {getattr(response, 'error', None)}")

message = response.choices[0].message
output = message.content

u = response.usage
usage = {
    "prompt_tokens": getattr(u, "prompt_tokens", None),
    "completion_tokens": getattr(u, "completion_tokens", None),
    "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
    "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
}
print("\nAgent: ", output, "\n")

# content is None and tool_calls is set: the model answered with a call,
# a function name plus JSON arguments. We parse it and run the function.
# This stage runs the first call only; 2.4 runs them all.
if message.tool_calls:
    tool_call = message.tool_calls[0]
    try:
        command = json.loads(tool_call.function.arguments)["command"]
    except (ValueError, KeyError, TypeError) as e:  # the model can produce broken JSON
        sys.exit(f"Error: the arguments of bash are not a JSON object: {e}")
    print("Tool: bash", command)
    print(bash(command), "\n")

print(usage)
