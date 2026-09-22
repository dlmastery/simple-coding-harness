"""Step 34 - the loop survives a bad model, a bad network and a bad crash.
A model call that fails after every retry comes back with `failed` set;
turn() shows the reason and ends the turn instead of raising. A
LoopDetector watches the tool calls of consecutive replies, and the
third identical call in a row gets REPEATED as its result without running.
recover(messages) finishes a resumed transcript that ends in tool calls
without results, the way a crash between a reply and its results leaves
it; chat() calls it on --resume and /sessions calls it too. The rest is step
33: turn() numbers each turn for the checkpoints, and MAX_CALLS caps the
model calls of one turn.
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
from .llm import build_system_prompt, call_llm, entry, with_mode
from .todos import active_form, restore
from .tools import active_schemas, execute_all, relearn
from .ui import ui

MAX_CALLS = 40  # model calls in one turn before we stop and ask the user

INTERRUPTED = "(interrupted before this tool ran)"


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced. Returns
    it early, with every tool call answered, when the model call fails for
    good or the turn is interrupted.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
    usage = {}
    detector = durability.LoopDetector()

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

            def on_restart():
                nonlocal streamed
                ui.stream_end()
                ui.note("that reply broke off and is discarded; the retry starts it over")
                streamed = False  # the next words open a fresh reply on screen

            schemas = active_schemas(plan.toolset())  # the stubs stand in for the deferred tools
            estimate = budget.breakdown(messages)["total"]  # what this request should cost
            with spinner:
                message, usage = call_llm(with_mode(messages) + [injection], tools=schemas, on_delta=on_delta, on_restart=on_restart)

            if getattr(message, "failed", None):
                # every retry failed: the user message stays, nothing dangles, so 'try again' works
                if streamed:
                    ui.stream_end()  # a stream that broke may have shown part of a reply
                ui.note(message.failed)
                break

            messages.append(entry(message))
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
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
    except KeyboardInterrupt:
        # ctrl-c mid-turn: answer the tool calls that never ran, so the
        # transcript stays valid, and go back to the prompt.
        session.repair(messages, INTERRUPTED)
        session.save(messages)
        ui.note("interrupted")

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, messages):
        messages = commands.compact(messages)
    return messages


def run_results(messages, tool_calls, repeated=None):
    """Run the tool calls of one reply and append a tool message for each, in order.

    Every call is decided first, the allowed ones run together, and the
    results are reported in reply order. A call flagged in `repeated` does
    not run: its result is REPEATED, so the model reads why nothing new came
    back. Shared by turn() and by recover().
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
    and saved. A call that raises anyway gets an Error: result, so the
    session can always be resumed. A transcript that ends anywhere else is
    left alone.
    """
    pending = durability.unanswered(messages)
    if not pending:
        return 0
    # the edits belong to the turn that crashed, so /undo takes them back with it: its start is
    # the user message before the reply, not where the transcript stands now
    start = max((i for i, m in enumerate(messages) if m.get("role") == "user" and isinstance(m.get("content"), str)), default=len(messages))
    checkpoint.TURN = max(checkpoint.turns(), default=0) or checkpoint.begin_turn(start)
    try:
        run_results(messages, pending)
    except Exception as failed:  # noqa: BLE001 - a recovery that crashes would crash every resume after it
        for call in durability.unanswered(messages):
            messages.append({"role": "tool", "tool_call_id": call.id, "content": f"Error: {type(failed).__name__}: {failed}"})
        session.save(messages)
    count = len(pending)
    ui.note(f"recovered {count} tool call{'s' if count != 1 else ''} left unanswered by the last run")
    return count


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
    restore(messages)  # the plan lives outside the transcript; rebuild it
    relearn(messages)  # and so do the deferred tools the model loaded
    return messages


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
        if cli.resume:
            messages = resume_last(messages)
            recover(messages)  # a crash mid-turn left tool calls without results: run them now
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
        recover(messages)  # a crash mid-turn left tool calls without results: run them now

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
