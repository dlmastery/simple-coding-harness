"""Step 21 - the inner loop is turn(). The reply streams to the screen as it is
written, and the spinner stops at the first delta. `harness -p PROMPT` runs
one turn without the chat and prints the answer to stdout.
"""

import argparse

import openai

from . import commands
from . import compact
from . import history
from . import sandbox
from . import session
from . import todos
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm
from .todos import active_form
from .tools import execute
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
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
    usage = {}

    try:
        for _ in range(MAX_CALLS):
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    parser.add_argument("-p", "--print", metavar="PROMPT", help="run one turn, print the answer, exit")
    cli = parser.parse_args()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.print:
        ui.headless()
        if cli.resume:
            messages = resume_last(messages)
        else:
            session.PERSIST = False  # a one-off run leaves no session behind
        messages = turn(messages, cli.print, cli)
        reply = last_reply(messages)
        print(reply)
        raise SystemExit(0 if reply else 1)  # empty answer or a failed turn: tell the caller

    ui.banner(sandbox.name())

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
