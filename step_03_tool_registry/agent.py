"""Step 3 - a tool registry.

Two tools instead of one, and a small structure so the third costs nothing:
a table from tool name to (function, schema). The model's tool call names
the function; we look it up and call it with the JSON arguments as kwargs.

Run:   python agent.py
Needs: BASE_URL, API_KEY and (optionally) MODEL in the environment.
"""

import json
import os
import subprocess

from openai import OpenAI

SYSTEM_PROMPT = (
    "You are a coding agent. Help the user with programming tasks. "
    "Use bash to explore and read_file to read whole files."
)


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


# name -> (implementation, what the model sees). Adding a tool is one line.
TOOLS = {
    "bash": (bash, schema("bash", bash.__doc__, command="The command to run")),
    "read_file": (read_file, schema("read_file", read_file.__doc__, path="Path to the file")),
}
TOOL_SCHEMAS = [s for _, s in TOOLS.values()]


def execute(call):
    """Turn a tool call from the model into a result string."""
    fn, _ = TOOLS[call.function.name]
    args = json.loads(call.function.arguments)
    return args, fn(**args)


def complete(messages):
    client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "gpt-4.1-mini"),
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    return response.choices[0].message


def main():
    user_input = input("you> ")
    message = complete([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])

    if message.content:
        print(f"\nagent> {message.content}")

    for call in message.tool_calls or []:
        args, result = execute(call)
        print(f"\ntool> {call.function.name} {args}")
        print(result)


if __name__ == "__main__":
    main()
