"""Step 41 - stop conditions. A turn ends when the model answers without
tool calls, as before; it calls finish(summary), and the loop stops
after that reply's results are in; or a budget trips: stop.tripped()
reads the calls of the turn, the dollars of the session and the seconds
of the turn against MAX_TURN_CALLS, MAX_SESSION_COST and
MAX_TURN_SECONDS. The Stop hooks may refuse the first two endings: the
block goes back to the agent as a user message, MAX_STOP_BLOCKS times,
and the loop goes on. Every model call is priced with stop.record().
last_reply() reads a finish summary as the answer. The rest is step 40:
the loop runs as the active agent. Every model call goes out
with handoff.toolset(), the active agent's tools, and after the tool
results of a reply are in, handoff.switch() applies a handoff the reply
asked for: messages[0] becomes the new agent's prompt, the session log
gets a marker, and the next call is the new agent's. recover() applies
one too, so a crash right after a handoff_to call does not lose it.
The rest is step 39: the --mode flag starts the chat in an approval mode, and the
banner shows it. The loop itself is unchanged: the mode acts inside
permissions.check, before any prompt.
The rest is step 38: `harness eval --workspace DIR` grades a copy of DIR with
every task's checker and runs no model turn. The rest is step 35: the user
can steer a running turn. Ctrl-C anywhere in a turn does not kill the
loop: turn() catches the KeyboardInterrupt, run_results() first gives
every call without a result INTERRUPTED so the transcript stays valid,
then steer() reads one line at the steer prompt and turn() appends it as a
user message. The loop goes on from there. A second Ctrl-C within
STEER_WINDOW seconds, or Ctrl-D, ends the turn and the chat. A Ctrl-C
inside a /command is caught by chat(). headless() is the -p path: without
a terminal every approve prompt is declined and ask_user gets NO_ANSWER.
The rest is step 34: the loop survives a bad model, a bad network and a
bad crash; MAX_CALLS caps the model calls of one turn; recover() finishes
a resumed transcript that ends in tool calls without results.
"""

import argparse
import sys
import time

from . import browser
from . import budget
from . import checkpoint
from . import commands
from . import compact
from . import durability
from . import evaluate
from . import handoff
from . import history
from . import hooks
from . import jobs
from . import mcp_client
from . import modes
from . import prompt
from . import sandbox
from . import session
from . import stop
from . import tools
from .ask_user import NO_ANSWER
from .context import reminder
from .llm import build_system_prompt, call_llm, entry, with_mode
from .todos import active_form, restore
from .tools import INTERRUPTED, active_schemas, execute_all, relearn
from .ui import ui

STEER_WINDOW = 2.0  # seconds: a second Ctrl-C within this many after the first exits


def steer(where):
    """Ctrl-C was pressed during `where`. Read one line to steer the turn.

    Returns the line, an empty string when the user pressed enter with
    nothing to add, or None when the user wants out: a second Ctrl-C within
    STEER_WINDOW seconds, or Ctrl-D. A Ctrl-C later than that cancels the
    steer prompt and the turn goes on.
    """
    pressed = time.monotonic()
    ui.interrupted(where)
    try:
        return prompt.read("  steer> ").strip()
    except EOFError:
        return None
    except KeyboardInterrupt:
        return None if time.monotonic() - pressed < STEER_WINDOW else ""


def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced. The turn
    ends when the model answers without tool calls or calls finish, when
    a model call fails for good, or when a budget in stop.py trips: the
    calls of the turn, the cost of the session, the seconds of the turn.
    The Stop hooks may refuse the first two ends and send the agent back
    with a user message, MAX_STOP_BLOCKS times at most. A Ctrl-C anywhere
    in the turn reads a steering message and goes on; a second one within
    STEER_WINDOW seconds raises KeyboardInterrupt out of the turn, with
    the transcript valid and saved.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    report = stop.tripped(0)
    if report:  # the session's budget is spent: nothing goes in the transcript, the note says what to do
        ui.note(report)
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    start = len(messages)  # the Stop hooks read the turn from here
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
    usage = {}
    detector = durability.LoopDetector()
    handoff.new_turn()  # the handoff count is per turn
    stop.begin_turn()   # the clock starts; the last turn's finish and blocks are forgotten
    calls = 0  # model calls so far in this turn

    while True:
        report = stop.tripped(calls)
        if report:
            ui.note(report)  # a budget is crossed: no more calls this turn
            break
        calls += 1  # counted before the call: an interrupted one counts too
        try:
            message, usage = one_call(messages, submitted.context, debug)
        except KeyboardInterrupt:
            if not steered(messages, "the model call"):  # nothing dangles: the reply never went in
                raise
            continue  # a new request, with the steering message at the end
        if message is None:
            break
        if not message.tool_calls:
            reason = stop.may_stop(messages, start, message.content or "")  # the Stop hooks have the last word
            if reason:
                stop.send_back(messages, reason)
                continue  # the block is a user message now; the agent reads it on the next call
            break

        repeated = detector.observe(message.tool_calls)
        for tool_call, flag in zip(message.tool_calls, repeated):
            if flag:
                ui.note(f"repeated call detected: {tool_call.function.name} with the same arguments {durability.REPEAT_LIMIT} times in a row")
        try:
            run_results(messages, message.tool_calls, repeated)
        except KeyboardInterrupt:
            if not steered(messages, "the tool calls"):  # every call has a result by now
                raise
        finally:
            handoff.switch(messages)  # a handoff_to result in this reply: the next call is the new agent's - even when the user leaves

        summary = stop.finished()
        if summary is not None:  # the reply called finish: its other calls ran, and the turn ends here
            reason = stop.may_stop(messages, start, summary, ended_by="finish")
            if reason:
                stop.send_back(messages, reason)
                continue
            ui.note("finish: the turn ends here")
            break

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, messages):
        messages = commands.compact(messages)
    return messages


def one_call(messages, hook_context, debug):
    """One model call: the late block, the request, the reply into the transcript.

    Returns (message, usage); message is None when the call failed for good
    and nothing went in the transcript. A KeyboardInterrupt from anywhere
    in here - the git status in the late block, the request, the stream -
    leaves the transcript as it was.
    """
    streamed = False
    try:
        injection = reminder(hook_context=hook_context)
        ui.injection(injection["content"])

        if history.fit(messages):
            ui.note("dropped old tool output to make this request fit")

        spinner = ui.working(active_form())

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

        schemas = active_schemas(handoff.toolset() + [stop.FINISH_SCHEMA])  # the active agent's tools and finish; the stubs stand in for the deferred ones
        estimate = budget.breakdown(messages)["total"]  # what this request should cost
        with spinner:
            message, usage = call_llm(with_mode(messages) + [injection], tools=schemas, on_delta=on_delta, on_restart=on_restart)
    except KeyboardInterrupt:
        if streamed:
            ui.stream_end()  # the part that arrived is on screen, but it goes nowhere: a reply is whole or absent
        raise

    if getattr(message, "failed", None):
        # every retry failed: the user message stays, nothing dangles, so 'try again' works
        if streamed:
            ui.stream_end()  # a stream that broke may have shown part of a reply
        ui.note(message.failed)
        return None, usage

    messages.append(entry(message))
    session.save(messages)

    if streamed:
        ui.stream_end()
    elif message.content:
        ui.agent(message.content)  # a reply that did not stream, e.g. from a fake model
    ui.usage(usage, estimate, cost=stop.record(usage))  # priced and added to the session's total
    warning = budget.check(usage.get("prompt_tokens") or estimate)
    if warning:
        ui.note(warning)

    if debug:
        ui.debug(message.model_dump(exclude_none=True))
    return message, usage


def steered(messages, where):
    """Read a steering line after a Ctrl-C during `where` and append it. Returns False when the user wants out.

    The line goes in as a user message, after whatever the turn has
    appended so far, so a reply and its tool results stay together. An
    empty line appends nothing and the turn goes on as it was.
    """
    line = steer(where)
    if line is None:
        ui.note("exiting; the transcript is saved and --resume picks it up")
        return False
    if line:
        messages.append({"role": "user", "content": line})
        session.save(messages)
        ui.user(line)
    return True


def run_results(messages, tool_calls, repeated=None):
    """Run the tool calls of one reply and append a tool message for each, in order.

    Every call is decided first, the allowed ones run together, and the
    results are reported in reply order. A call flagged in `repeated` does
    not run: its result is REPEATED, so the model reads why nothing new came
    back. Shared by turn() and by recover().

    A Ctrl-C while the calls run does not lose the reply: every call that
    has no result by then gets INTERRUPTED, the results are appended in
    order as usual, and only then is the KeyboardInterrupt raised again,
    for turn() to read the steering message after a valid transcript.
    """
    repeated = repeated or [False] * len(tool_calls)
    fresh = [call for call, flag in zip(tool_calls, repeated) if not flag]
    outcomes = []  # (args, result) per fresh call, filled as each one finishes
    interrupt = None
    try:
        if fresh:
            execute_all(fresh, outcomes=outcomes)
    except KeyboardInterrupt as stop:
        interrupt = stop
    outcomes += [(durability.parse_args(call), None) for call in fresh[len(outcomes):]]  # never started
    ran = iter((args, INTERRUPTED if result is None else result) for args, result in outcomes)
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

    if interrupt is not None:
        raise interrupt  # the transcript is whole; now the user gets to speak


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
        handoff.switch(messages)  # one of them may have been a handoff_to
    except Exception as failed:  # noqa: BLE001 - a recovery that crashes would crash every resume after it
        for call in durability.unanswered(messages):
            messages.append({"role": "tool", "tool_call_id": call.id, "content": f"Error: {type(failed).__name__}: {failed}"})
        session.save(messages)
    count = len(pending)
    ui.note(f"recovered {count} tool call{'s' if count != 1 else ''} left unanswered by the last run")
    return count


def last_reply(messages):
    """The answer of the newest assistant message: its finish summary, else its text, else an empty string.

    A finish call counts only when its tool result is the summary: one a
    hook blocked or a rule denied never ended the turn.
    """
    results = {m.get("tool_call_id"): m.get("content") for m in messages if m.get("role") == "tool"}
    for message in reversed(messages):
        if message["role"] != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            summary = stop.finish_summary(call["function"]["arguments"])
            if call["function"]["name"] == "finish" and results.get(call["id"]) == summary:
                return summary
        if message.get("content"):
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
    top.add_argument("--mode", choices=modes.NAMES, help="start in this approval mode (default: default)")
    commands_ = top.add_subparsers(dest="command", metavar="COMMAND")
    run = commands_.add_parser("eval", help="run an evaluation suite and report pass rates")
    run.add_argument("suite", help="directory of task directories")
    run.add_argument("--repeat", type=int, default=1, metavar="N", help="run every task N times")
    run.add_argument("--keep", action="store_true", help="keep the temp workspaces for inspection")
    run.add_argument("--workspace", metavar="DIR", help="grade a copy of DIR with every task's checker; the agent does not run")
    return top


def main(argv=None):
    cli = parser().parse_args(argv)
    try:
        if cli.command == "eval":
            if cli.mode:
                modes.set_mode(cli.mode, log=False)  # the tasks run in that mode; an eval keeps no chat log to note it in
            raise SystemExit(evaluate.main(cli))
        chat(cli)
    finally:
        browser.browser_close()  # a no-op unless a browse call opened one
        mcp_client.close_all()   # stops every MCP server that was started
        jobs.kill_all()          # a background job never outlives the session
        hooks.run_hooks("SessionEnd")


def headless(messages, cli):
    """`-p`: one turn, the answer on stdout, exit 1 when there is none.

    Without a terminal on stdin nobody can answer a prompt, so every ask
    is declined with a note and ask_user gets NO_ANSWER; the session is
    not written unless --resume asked for one.
    """
    if not sys.stdin.isatty():
        def decline(reason):
            ui.note(f"declined, no terminal to ask on: {reason}")
            return "n"

        ui.approve = decline
        tools.TOOLS["ask_user"] = lambda question, options=None: NO_ANSWER
    if cli.resume:
        messages = resume_last(messages)
        recover(messages)  # a crash mid-turn left tool calls without results: run them now
    try:
        messages = turn(messages, cli.print, cli)
    except KeyboardInterrupt:
        raise SystemExit(130)  # the exit code a shell gives an interrupted command
    reply = last_reply(messages)
    print(reply)
    raise SystemExit(0 if reply else 1)  # empty answer or a failed turn: tell the caller


def chat(cli):
    if cli.print:
        ui.headless()
        session.PERSIST = bool(cli.resume)  # a one-off question leaves no session behind, --mode or not
    if cli.mode:
        modes.set_mode(cli.mode)  # before the banner and the first check; logged, so --resume comes back in it
    if not cli.print:
        ui.banner(sandbox.name(), modes.current())
    mcp_client.connect_all()  # external tools join the registry before the first turn
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    messages = [{"role": "system", "content": build_system_prompt()}]  # after connect_all: the deferred list is complete

    if cli.print:
        headless(messages, cli)

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
                try:
                    messages = commands.handle(user_input, messages)
                except KeyboardInterrupt:
                    ui.note("command interrupted")  # a /compact or /init cut short; the files it wrote stay
                session.save(messages)
                continue

            messages = turn(messages, user_input, cli)
        except KeyboardInterrupt:
            break  # a second Ctrl-C, or Ctrl-D at the steer prompt: the transcript is saved

    ui.summary()


if __name__ == "__main__":
    main()
