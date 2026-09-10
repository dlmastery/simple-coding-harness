"""Step 2 - the first tool.

The model can now *ask* us to run a shell command. We describe the tool with a
JSON schema, the model replies with a tool call instead of prose, and we run
it. The result is printed for you - but NOT sent back to the model yet. That
is step 4.

Run:   python agent.py
Needs: BASE_URL, API_KEY and (optionally) MODEL in the environment.
"""

import json
import os
import subprocess

from openai import OpenAI

SYSTEM_PROMPT = (
    "You are a coding agent. Help the user with programming tasks. "
    "Use the bash tool to look at files and run commands."
)

# The schema is what the model sees. The description is a prompt: it decides
# when the model reaches for the tool, so write it like one.
BASH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command and return its stdout and stderr.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run"},
            },
            "required": ["command"],
        },
    },
}


def bash(command: str) -> str:
    """The implementation behind the schema. The model never sees this code."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return (result.stdout + result.stderr) or "(no output)"


def complete(messages, tools):
    client = OpenAI(base_url=os.environ["BASE_URL"], api_key=os.environ["API_KEY"])
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "gpt-4.1-mini"),
        messages=messages,
        tools=tools,
    )
    return response.choices[0].message


def main():
    user_input = input("you> ")
    message = complete(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        tools=[BASH_SCHEMA],
    )

    if message.content:
        print(f"\nagent> {message.content}")

    # A tool call is the model's answer taking a different shape: instead of
    # text it hands back a function name and JSON arguments, and stops.
    for call in message.tool_calls or []:
        args = json.loads(call.function.arguments)
        print(f"\ntool> bash {args['command']}")
        print(bash(args["command"]))


if __name__ == "__main__":
    main()
