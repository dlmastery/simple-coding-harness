"""Step 30 - main() has subcommands. Plain `harness` is the chat, as
before, with the same flags. `harness eval <suite>` runs an evaluation
suite through evaluate.main() and exits with its status. The turn loop
is unchanged: the eval runner calls turn() directly, once per task.

The loop has three guards. MAX_CALLS caps the model calls of one turn. A
model call that raises ends the turn with a note, not a traceback. A
ctrl-c during a turn is caught in chat(): a tool call left without a
result gets one that says so, and the prompt comes back.
"""

import argparse

import openai

from . import browser
from . import commands
from . import compact
from . import evaluate
from . import history
from . import hooks
from . import jobs
from . import mcp_client
from . import plan
from . import sandbox
from . import session
from . import todos
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm, with_mode
from .todos import active_form
from .tools import execute_all
from .ui import ui

MAX_CALLS = 40  # model calls one turn may make before the loop stops and asks

INTERRUPTED = "(interrupted before this tool ran)"


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced. The turn
    ends when the model answers without tool calls, when a model call
    fails, or when MAX_CALLS calls have been made.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
    calls = 0  # model calls so far in this turn
    usage = {}

    while True:
        if calls >= MAX_CALLS:
            ui.note(f"stopped after {calls} model calls in one turn; say 'continue' to go on")
            break
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

        schemas = plan.toolset()
        allowed = {s["function"]["name"] for s in schemas}  # what the model was offered is all it may run
        with spinner:
            try:
                message, usage = call_llm(with_mode(messages) + [injection], tools=schemas, on_delta=on_delta)
            except openai.APIError as failed:
                if streamed:
                    ui.stream_end()  # a stream that broke may have shown part of a reply
                ui.note(f"model call failed: {failed}")  # the user message stays; the transcript is still valid
                break
        calls += 1

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

        run_results(messages, message.tool_calls, allowed)

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, messages):
        messages = commands.compact(messages)
    return messages


def run_results(messages, tool_calls, allowed=None):
    """Run the tool calls of one reply and append their results in order.

    Every call gets exactly one tool message, whatever happened to it: a
    denied call, a blocked call, a call whose tool raised, all come back as
    text the model can read. The results are decided first, run together,
    then reported in order.
    """
    outcomes = execute_all(tool_calls, allowed)
    pictures = []  # (tool name, PNG path) for every image a result asked to show
    for tool_call, (args, result) in zip(tool_calls, outcomes):
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


def unanswered_ids(messages):
    """The ids of the tool calls at the end of the transcript that have no result yet."""
    index = len(messages) - 1
    while index >= 0 and messages[index].get("role") == "tool":
        index -= 1
    if index < 0 or messages[index].get("role") != "assistant":
        return []
    answered = {m.get("tool_call_id") for m in messages[index + 1:]}
    return [call["id"] for call in messages[index].get("tool_calls") or [] if call["id"] not in answered]


def interrupted(messages):
    """A ctrl-c landed mid-turn: give every tool call without a result one that says so.

    The transcript stays valid for the API, the user's message and the
    model's reply stay, and the prompt comes back.
    """
    for call_id in unanswered_ids(messages):
        messages.append({"role": "tool", "tool_call_id": call_id, "content": INTERRUPTED})
    ui.note("interrupted")
    session.save(messages)
    return messages


def last_reply(messages):
    """The text of the newest assistant message, or an empty string."""
    for message in reversed(messages):
        if message["role"] == "assistant" and message.get("content"):
            return message["content"]
    return ""


def parser():
    """The command line: chat flags at the top level, `eval` as a subcommand."""
    top = argparse.ArgumentParser(prog="harness")
    top.add_argument("--resume", action="store_true", help="continue the last session")
    top.add_argument("--debug", action="store_true", help="show the raw model response")
    top.add_argument("-p", "--print", metavar="PROMPT", help="run one turn, print the answer, exit")
    commands_ = top.add_subparsers(dest="command", metavar="COMMAND")
    run = commands_.add_parser("eval", help="run an evaluation suite and report pass rates")
    run.add_argument("suite", help="directory of task directories")
    run.add_argument("--repeat", type=int, default=1, metavar="N", help="run every task N times")
    run.add_argument("--keep", action="store_true", help="keep the temp workspaces for inspection")
    return top


def main(argv=None):
    cli = parser().parse_args(argv)
    try:
        if cli.command == "eval":
            raise SystemExit(evaluate.main(cli))
        chat(cli)
    finally:
        browser.browser_close()  # a no-op unless a browse call opened one
        mcp_client.close_all()   # stops every MCP server that was started
        jobs.kill_all()          # a background job never outlives the session
        hooks.run_hooks("SessionEnd")


def chat(cli):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.print:
        ui.headless()
    else:
        ui.banner(sandbox.name(), plan.MODE)
    mcp_client.connect_all()  # external tools join the registry before the first turn
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    if cli.print:
        messages = turn(messages, cli.print, cli)
        reply = last_reply(messages)
        print(reply)
        raise SystemExit(0 if reply else 1)  # no answer is an error a script can see

    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            history.strip(messages)
            todos.from_transcript(messages)  # the plan lives outside the transcript; rebuild it
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
        except KeyboardInterrupt:
            messages = interrupted(messages)

    ui.summary()


if __name__ == "__main__":
    main()
