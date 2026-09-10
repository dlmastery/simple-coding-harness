"""Step 4 - the agent loop.

The step that turns a chatbot with tools into an agent. Tool results go back
into the message list and the model is called again, until it answers with
plain text. Wrapped in an outer loop so the conversation keeps its history
across turns.

    while True:                       # outer: one iteration per user message
        messages.append(user)
        while True:                   # inner: one iteration per model call
            reply = model(messages)
            messages.append(reply)
            if no tool calls: break
            run each tool, append each result as a "tool" message

Run:   python agent.py
Needs: BASE_URL, API_KEY and (optionally) MODEL in the environment.
"""

import json
import os
import subprocess

from openai import OpenAI

SYSTEM_PROMPT = (
    "You are a coding agent. Help the user with programming tasks. "
    "Use bash to explore and read_file to read whole files. "
    "Keep calling tools until you have what you need, then answer."
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
}
TOOL_SCHEMAS = [s for _, s in TOOLS.values()]


def execute(call):
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


def as_dict(message):
    """The assistant message, as the dict we will send back next call.

    Tool calls must be kept: the API requires every "tool" message to follow
    the assistant message that asked for it.
    """
    entry = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        entry["tool_calls"] = [
            {
                "id": c.id,
                "type": "function",
                "function": {"name": c.function.name, "arguments": c.function.arguments},
            }
            for c in message.tool_calls
        ]
    return entry


def turn(messages, user_input):
    """One user message, as many model calls as it takes. Mutates messages."""
    messages.append({"role": "user", "content": user_input})

    while True:
        message = complete(messages)
        messages.append(as_dict(message))

        if message.content:
            print(f"\nagent> {message.content}")

        if not message.tool_calls:
            return message.content

        for call in message.tool_calls:
            args, result = execute(call)
            print(f"\ntool> {call.function.name} {args}\n{result[:800]}")
            # The result is a message too, tied to the call by id.
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            user_input = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            break
        turn(messages, user_input)


if __name__ == "__main__":
    main()
