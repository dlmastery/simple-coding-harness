"""Step 33 - turn() numbers each turn. Once the UserPromptSubmit hooks let
the prompt through, checkpoint.begin_turn() records the turn number and
how long the transcript is at that moment. Every file the turn's tools
change is captured under that number, and /undo cuts the transcript back
to that length. The rest is step 32: the loop measures what it sends, and
main() has subcommands.
"""

import argparse

from . import browser
from . import budget
from . import checkpoint
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
from .context import reminder
from .llm import build_system_prompt, call_llm, with_mode
from .todos import active_form
from .tools import active_schemas, execute_all
from .ui import ui


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    messages.append({"role": "user", "content": user_input})

    while True:
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

        estimate = budget.breakdown(messages)["total"]  # what this request should cost
        with spinner:
            message, usage = call_llm(with_mode(messages) + [injection], tools=active_schemas(plan.toolset()), on_delta=on_delta)

        messages.append(message.model_dump(exclude_none=True))
        session.save(messages)

        if streamed:
            ui.stream_end()
        elif message.content:
            ui.agent(message.content)  # a reply that did not stream, e.g. from a fake model
        ui.usage(usage, estimate)
        warning = budget.check(usage.get("prompt_tokens") or estimate)
        if warning:
            ui.note(warning)

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

    if compact.needed(usage):
        messages = commands.compact(messages)
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
    if cli.print:
        ui.headless()
    else:
        ui.banner(sandbox.name(), plan.MODE)
    mcp_client.connect_all()  # external tools join the registry before the first turn
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    messages = [{"role": "system", "content": build_system_prompt()}]  # after connect_all: the deferred list is complete

    if cli.print:
        messages = turn(messages, cli.print, cli)
        print(last_reply(messages))
        raise SystemExit(0)

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
