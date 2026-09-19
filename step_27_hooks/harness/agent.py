"""Step 27 - the loop has hook points. turn() runs the UserPromptSubmit
hooks before the first model call, and their context rides in the late
block for that turn. main() runs SessionStart before the first prompt and
SessionEnd on the way out. The tool hooks live in tools.py.
"""

import argparse

import openai

from . import browser
from . import commands
from . import compact
from . import history
from . import hooks
from . import mcp_client
from . import sandbox
from . import session
from . import todos
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm
from .todos import active_form
from .tools import execute_all
from .ui import ui

MAX_CALLS = 40  # model calls in one turn; past that the model is looping, not working

INTERRUPTED = "(interrupted before this tool ran)"


def answer_pending(messages):
    """Give every unanswered tool call a tool message, so the transcript stays valid."""
    answered = {m.get("tool_call_id") for m in messages if m["role"] == "tool"}
    last = messages[-1]
    if last["role"] != "assistant":
        return
    for call in last.get("tool_calls") or []:
        if call["id"] not in answered:
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": INTERRUPTED})


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced. Returns
    it early, with every tool call answered, when the model call fails or
    the turn is interrupted.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
    usage = {}

    try:
        for _ in range(MAX_CALLS):
            injection = reminder(hook_context=submitted.context)
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
                # the user message stays, nothing dangles: the next turn can retry
                if streamed:
                    ui.stream_end()
                ui.note(f"model call failed: {failed}")
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
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
    except KeyboardInterrupt:
        answer_pending(messages)  # a call was cut off between the reply and its results
        session.save(messages)
        ui.note("interrupted")

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


def resume_last(messages):
    """Open the newest saved chat, if there is one; else keep the fresh transcript."""
    saved = session.all_sessions()
    if not saved:
        return messages
    messages = session.open_session(saved[0]["id"])
    history.strip(messages)
    todos.restore(messages)
    return messages


def main():
    try:
        chat()
    finally:
        browser.browser_close()  # a no-op unless a browse call opened one
        mcp_client.close_all()   # stops every MCP server that was started
        hooks.run_hooks("SessionEnd")


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
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    if cli.print:
        if cli.resume:
            messages = resume_last(messages)
        else:
            session.PERSIST = False  # a one-off run leaves no session behind
        messages = turn(messages, cli.print, cli)
        reply = last_reply(messages)
        print(reply)
        raise SystemExit(0 if reply else 1)  # empty answer or a failed turn: tell the caller

    if cli.resume:
        messages = resume_last(messages)
        ui.resumed(messages)
        ui.replay(messages)

    while True:
        user_input = ui.ask()
        if user_input is None or user_input in ("/exit", "/quit"):
            break
        if not user_input:
            continue

        try:
            if user_input.startswith("/"):
                messages = commands.handle(user_input, messages)
                session.save(messages)
                continue

            messages = turn(messages, user_input, cli)
        except KeyboardInterrupt:  # e.g. during /compact: back to the prompt
            ui.note("interrupted")

    ui.summary()


if __name__ == "__main__":
    main()
