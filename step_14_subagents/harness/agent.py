"""The agent loop, now keeping the transcript inside the context window."""

import argparse

from . import commands, compact, history, llm, sandbox, session
from .context import reminder
from .prompts import SYSTEM_PROMPT
from .todos import active_form
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
    """One user message, as many model calls as it takes.

    Returns the message list to continue with - usually the same object,
    but a different one if the turn ended in compaction.
    """
    messages.append({"role": "user", "content": user_input})
    session.save(messages)

    while True:
        injection = reminder()
        ui.injection(injection["content"])

        if history.fit(messages):
            ui.note("dropped old tool output to make this request fit")

        with ui.working(active_form()):
            message, usage = llm.complete(messages + [injection])
        messages.append(as_dict(message))
        session.save(messages)
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            break

        for call in message.tool_calls:
            args, result = execute(call)
            ui.tool(call.function.name, args, result)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            session.save(messages)

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage):
        messages = commands.compact(messages)
    return messages


def main():
    parser = argparse.ArgumentParser(prog="harness")
    parser.add_argument("--resume", action="store_true", help="continue the most recent chat")
    cli = parser.parse_args()

    ui.banner(sandbox.name())
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            history.strip(messages)
            ui.resumed(messages)
            ui.replay(messages)

    while True:
        user_input = ui.ask()
        if not user_input:
            break
        if user_input.startswith("/"):
            messages = commands.handle(user_input, messages)
            continue
        messages = turn(messages, user_input)
    ui.summary()


if __name__ == "__main__":
    main()
