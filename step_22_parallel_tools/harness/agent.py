"""Step 22 - the tool calls of one reply go to tools.execute_all(), which runs
them side by side and hands the results back in order. The panels print
after all of them finish.
"""

import argparse

from . import commands
from . import compact
from . import history
from . import sandbox
from . import session
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm
from .todos import active_form
from .tools import execute_all
from .ui import ui


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced.
    """
    debug = getattr(cli, "debug", False)
    messages.append({"role": "user", "content": user_input})

    while True:
        injection = reminder()
        ui.injection(injection["content"])

        if history.fit(messages):
            ui.note("dropped old tool output to make this request fit")

        spinner = ui.working(active_form())
        streamed = False

        def on_delta(text):
            nonlocal streamed
            if not streamed:
                spinner.stop()  # the wait is over: the first words are here
                ui.stream_start()
                streamed = True
            ui.stream_delta(text)

        with spinner:
            message, usage = call_llm(messages + [injection], on_delta=on_delta)

        messages.append(message.model_dump(exclude_none=True))
        session.save(messages)

        if streamed:
            ui.stream_end()
        elif message.content:
            ui.agent(message.content)  # a reply that did not stream, e.g. from a fake model
        ui.usage(usage)

        if debug:
            ui.debug(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            break

        # decide every call first, run the allowed ones together, then report in order
        outcomes = execute_all(message.tool_calls)
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            ui.tool(tool_call.function.name, args, result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            session.save(messages)  # after every message, so a crash loses nothing

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage):
        messages = commands.compact(messages)
    return messages


def last_reply(messages):
    """The text of the newest assistant message, or an empty string."""
    for message in reversed(messages):
        if message["role"] == "assistant" and message.get("content"):
            return message["content"]
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    parser.add_argument("-p", "--print", metavar="PROMPT", help="run one turn, print the answer, exit")
    cli = parser.parse_args()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.print:
        ui.headless()
        messages = turn(messages, cli.print, cli)
        print(last_reply(messages))
        raise SystemExit(0)

    ui.banner(sandbox.name())

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
            session.save(messages)
            continue

        messages = turn(messages, user_input, cli)

    ui.summary()


if __name__ == "__main__":
    main()
