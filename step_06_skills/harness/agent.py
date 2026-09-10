"""The agent loop. Same two loops as step 4, now with the UI factored out."""

from . import llm
from .prompts import SYSTEM_PROMPT
from .tools import execute
from .ui import ui


def as_dict(message):
    """The assistant message as the dict we send back on the next call."""
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
        with ui.working():
            message, usage = llm.complete(messages)
        messages.append(as_dict(message))
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            return message.content

        for call in message.tool_calls:
            args, result = execute(call)
            ui.tool(call.function.name, args, result)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})


def main():
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        user_input = ui.ask()
        if not user_input:
            break
        turn(messages, user_input)
    ui.summary()


if __name__ == "__main__":
    main()
