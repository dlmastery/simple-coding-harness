"""Stage 9 - the loop from stage 8 inside main(), so pip can install it as a command.

    pip install -e .
    harness            # from any directory

The project directory is wherever you run it: skills, sessions and git
status all key off the current working directory.
"""

import argparse

import openai

from . import commands
from . import session
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm, entry
from .tools import run_tool
from .ui import ui

MAX_CALLS = 40  # model calls in one turn before we stop and ask the user


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
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
        if user_input is None or user_input in ("/exit", "/quit"):
            break
        if not user_input:
            continue

        if user_input.startswith("/"):
            messages = commands.handle(user_input, messages)
            session.save(messages)
            continue

        messages.append({"role": "user", "content": user_input})
        session.save(messages)

        try:
            for _ in range(MAX_CALLS):
                injection = reminder()
                ui.injection(injection["content"])

                try:
                    with ui.working():
                        message, usage = call_llm(messages + [injection])
                except (openai.APIError, RuntimeError) as failed:
                    ui.note(f"model call failed: {failed}")
                    break

                messages.append(entry(message))
                session.save(messages)
                ui.usage(usage)

                if cli.debug:
                    ui.debug(message.model_dump(exclude_none=True))

                if message.content:
                    ui.agent(message.content)

                if not message.tool_calls:
                    break

                for tool_call in message.tool_calls:
                    args, result = run_tool(tool_call)
                    ui.tool(tool_call.function.name, args, result)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                    session.save(messages)  # after every message, so a crash loses nothing
            else:
                ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
        except KeyboardInterrupt:
            # ctrl-c mid-turn: answer the tool calls that never ran, so the
            # transcript stays valid, and go back to the prompt.
            session.repair(messages, "(interrupted before this tool ran)")
            session.save(messages)
            ui.note("interrupted")

    ui.summary()


if __name__ == "__main__":
    main()
