"""Generative UI step 01 - the stage 15 loop, unchanged, plus a --web flag that
opens a second surface for the render_ui tool.
"""

import argparse

import openai

from . import commands
from . import compact
from . import history
from . import sandbox
from . import session
from . import web
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm, entry
from .todos import active_form, restore
from .tools import execute
from .ui import ui

MAX_CALLS = 40  # model calls in one turn before we stop and ask the user


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    parser.add_argument("--web", nargs="?", const=8770, type=int, metavar="PORT", help="also serve rendered UI to a browser page")
    cli = parser.parse_args()

    ui.banner(sandbox.name())
    if cli.web is not None:
        try:
            _, url = web.serve(cli.web)
            ui.note(f"web surface: open {url} in a browser")
        except OSError as error:  # the port is taken: the terminal surface still works
            ui.note(f"web surface not started on port {cli.web}: {error}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            history.strip(messages)
            restore(messages)  # the plan lives outside the transcript; rebuild it
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

        usage = {}
        try:
            for _ in range(MAX_CALLS):
                injection = reminder()
                ui.injection(injection["content"])

                if history.fit(messages):
                    ui.note("dropped old tool output to make this request fit")

                try:
                    with ui.working(active_form()):
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
                    args, result = execute(tool_call)
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

        history.sweep()          # the turn is over: bin its temp files...
        history.strip(messages)  # ...and shrink the tool output it produced

        if compact.needed(usage, messages):
            messages = commands.compact(messages)

    ui.summary()


if __name__ == "__main__":
    main()
