"""The agent loop, now sending a late-injected context block with each call."""

from . import llm
from .context import reminder
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
        injection = reminder()
        ui.injection(injection["content"])

        with ui.working():
            # `messages + [injection]` builds a new list for the request only.
            # The injection is never appended to `messages`, so the stored
            # transcript - and the cached prefix - stay untouched.
            message, usage = llm.complete(messages + [injection])
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
