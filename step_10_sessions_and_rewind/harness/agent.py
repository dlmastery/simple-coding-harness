"""The agent loop, now saving every message and handling slash commands."""

import argparse

from . import commands, llm, session
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
    session.save(messages)

    while True:
        injection = reminder()
        ui.injection(injection["content"])

        with ui.working():
            message, usage = llm.complete(messages + [injection])
        messages.append(as_dict(message))
        session.save(messages)
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            return message.content

        for call in message.tool_calls:
            args, result = execute(call)
            ui.tool(call.function.name, args, result)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            session.save(messages)  # after every message, so a crash loses nothing


def main():
    parser = argparse.ArgumentParser(prog="harness")
    parser.add_argument("--resume", action="store_true", help="continue the most recent chat")
    cli = parser.parse_args()

    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            ui.resumed(messages)
            ui.replay(messages)

    while True:
        user_input = ui.ask()
        if not user_input:
            break
        if user_input.startswith("/"):
            messages = commands.handle(user_input, messages)
            continue
        turn(messages, user_input)
    ui.summary()


if __name__ == "__main__":
    main()
