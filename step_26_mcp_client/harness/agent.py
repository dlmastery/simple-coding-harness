"""Step 26 - the MCP servers start before the first turn and stop on the way
out. connect_all() adds their tools to the registry; the turn loop is
unchanged and calls them like any other tool.
"""

import argparse

import openai

from . import browser
from . import commands
from . import compact
from . import history
from . import mcp_client
from . import sandbox
from . import session
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm
from .todos import active_form, restore
from .tools import execute_all
from .ui import ui

MAX_CALLS = 40  # model calls one turn may make before the harness stops it

INTERRUPTED = "(interrupted before this tool ran)"


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced.
    """
    messages.append({"role": "user", "content": user_input})
    session.save(messages)  # the prompt is on disk even if the first model call fails

    try:
        return turn_body(messages, cli)
    except KeyboardInterrupt:
        # ctrl-c mid-turn: answer the tool calls that never ran, so the
        # transcript stays valid, and hand control back to the prompt
        last = messages[-1]
        if last.get("role") == "assistant":
            for call in last.get("tool_calls") or []:
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": INTERRUPTED})
        session.save(messages)
        ui.note("interrupted")
        return messages


def turn_body(messages, cli, hook_context=""):
    """Every model call and tool call of one turn. Returns the message list."""
    debug = getattr(cli, "debug", False)
    calls = 0
    usage = {}  # of the last model call; empty when none succeeded

    while True:
        if calls >= MAX_CALLS:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
            break
        calls += 1
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

        try:
            with spinner:
                message, usage = call_llm(messages + [injection], on_delta=on_delta)
        except (openai.APIError, RuntimeError) as failed:
            ui.note(f"model call failed: {failed}")  # the transcript is valid as it is: the user message stays
            break

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
        pictures = []  # (tool name, PNG path) for every image a result asked to show
        for tool_call, (args, result) in zip(message.tool_calls, outcomes):
            result, paths = history.split_images(result)
            pictures += [(tool_call.function.name, path) for path in paths]
            ui.tool(tool_call.function.name, args, result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            session.save(messages)  # after every message, so a crash loses nothing

        # the pictures go after the last result, so no tool message is orphaned
        for name, path in pictures:
            messages.append(history.image_message(path, f"screenshot from tool {name}"))
            session.save(messages)

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, messages):
        messages = commands.compact(messages)
    return messages


def last_reply(messages):
    """The text of the newest assistant message, or an empty string."""
    for message in reversed(messages):
        if message["role"] == "assistant" and message.get("content"):
            return message["content"]
    return ""


def main():
    try:
        chat()
    finally:
        browser.browser_close()  # a no-op unless a browse call opened one
        mcp_client.close_all()   # stops every MCP server that was started


def chat():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    parser.add_argument("-p", "--print", metavar="PROMPT", help="run one turn, print the answer, exit")
    cli = parser.parse_args()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.print:
        ui.headless()
    else:
        ui.banner(sandbox.name())
    mcp_client.connect_all()  # external tools join the registry before the first turn

    if cli.print:
        messages = turn(messages, cli.print, cli)
        print(last_reply(messages))
        raise SystemExit(0)

    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            history.strip(messages)
            restore(messages)  # the todo list, from the last write_todos in the transcript
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

        messages = turn(messages, user_input, cli)

    ui.summary()


if __name__ == "__main__":
    main()
