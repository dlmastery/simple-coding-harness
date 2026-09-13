"""Step 34 - the loop survives a bad model, a bad network and a bad crash.
A model call that fails after every retry comes back with `failed` set;
turn() shows the reason and ends the turn instead of raising. MAX_CALLS
caps the model calls of one turn; on reaching it the loop stops and says
so. A LoopDetector watches the tool calls of consecutive replies, and the
third identical call in a row gets REPEATED as its result without running.
recover(messages) finishes a resumed transcript that ends in tool calls
without results, the way a crash between a reply and its results leaves
it; chat() calls it on --resume before asking for input. The rest is step
33: turn() numbers each turn for the checkpoints.
"""

import argparse

from . import browser
from . import budget
from . import checkpoint
from . import commands
from . import compact
from . import durability
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

MAX_CALLS = 40  # model calls one turn may make before the loop stops and asks


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced. The turn
    ends when the model answers without tool calls, when a model call
    fails for good, or when MAX_CALLS calls have been made.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    messages.append({"role": "user", "content": user_input})
    detector = durability.LoopDetector()
    calls = 0  # model calls so far in this turn
    usage = {}

    while True:
        if calls >= MAX_CALLS:
            ui.note(f"stopped after {calls} model calls in one turn; say continue to go on")
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

        estimate = budget.breakdown(messages)["total"]  # what this request should cost
        with spinner:
            message, usage = call_llm(with_mode(messages) + [injection], tools=active_schemas(plan.toolset()), on_delta=on_delta)
        calls += 1

        if getattr(message, "failed", None):
            if streamed:
                ui.stream_end()  # a stream that broke may have shown part of a reply
            ui.note(message.failed)  # the model never answered; nothing goes in the transcript
            break

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

        repeated = detector.observe(message.tool_calls)
        for tool_call, flag in zip(message.tool_calls, repeated):
            if flag:
                ui.note(f"repeated call detected: {tool_call.function.name} with the same arguments {durability.REPEAT_LIMIT} times in a row")
        run_results(messages, message.tool_calls, repeated)

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage):
        messages = commands.compact(messages)
    return messages


def run_results(messages, tool_calls, repeated=None):
    """Run the tool calls of one reply and append their results in order.

    A call flagged in `repeated` does not run: its result is REPEATED, so
    the model reads why nothing new came back. The rest are decided first,
    run together, then reported in order, as before.
    """
    repeated = repeated or [False] * len(tool_calls)
    fresh = [call for call, flag in zip(tool_calls, repeated) if not flag]
    ran = iter(execute_all(fresh) if fresh else [])
    pictures = []  # (tool name, PNG path) for every image a result asked to show
    for tool_call, flag in zip(tool_calls, repeated):
        args, result = (durability.parse_args(tool_call), durability.REPEATED) if flag else next(ran)
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


def recover(messages):
    """Finish the tool calls a crash left without results. Returns how many ran.

    A resumed transcript that ends in an assistant message with tool calls,
    or in some but not all of their results, cannot be sent back: the API
    wants a result for every call. The missing calls run here, through the
    same permissions and hooks as in a turn, and their results are appended
    and saved. A transcript that ends anywhere else is left alone.
    """
    pending = durability.unanswered(messages)
    if not pending:
        return 0
    # the edits belong to the turn that crashed, so /undo takes them back with it
    checkpoint.TURN = max(checkpoint.turns(), default=0) or checkpoint.begin_turn(len(messages))
    run_results(messages, pending)
    count = len(pending)
    ui.note(f"recovered {count} tool call{'s' if count != 1 else ''} left unanswered by the last run")
    return count


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
            recover(messages)  # a crash mid-turn left tool calls without results: run them now

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
