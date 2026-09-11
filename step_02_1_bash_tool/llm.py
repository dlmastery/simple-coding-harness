"""Stage 2.1 - chat with a simple bash tool (video 02:54).

The model can now ask us to run a shell command. We describe the tool as
JSON, pass it in `tools=`, and if the reply carries a tool call we run it.
The result is printed for you, not sent back to the model - that is 2.4.

Run:   python llm.py
Needs: BASE_URL, API_KEY (and optionally MODEL) in the environment.
"""

import json
import os
import subprocess

from openai import OpenAI

client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)

MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

user_input = input("Enter your prompt> ")

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


def bash(command):
    """The Python behind the schema. subprocess.run executes what the model chose."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
    tools=[BASH_TOOL],  # the only change to the request
)

message = response.choices[0].message
output = message.content

completion_details = response.usage.completion_tokens_details
prompt_details = response.usage.prompt_tokens_details

usage = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
    "cached_tokens": getattr(prompt_details, "cached_tokens", None),
}
print("\nAgent: ", output, "\n")

# content is None and tool_calls is set: the model answered with a call,
# a function name plus JSON arguments. We parse it and run the function.
if message.tool_calls:
    tool_call = message.tool_calls[0]
    command = json.loads(tool_call.function.arguments)["command"]
    print("Tool: bash", command)
    print(bash(command), "\n")

print(usage)
