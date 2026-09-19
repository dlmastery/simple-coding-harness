"""Step 38 - `harness eval --workspace DIR` grades a copy of DIR with
every task's checker and runs no model turn. The rest is step 35: the user
can steer a running turn. Ctrl-C anywhere in a turn does not kill the
loop: turn() catches the KeyboardInterrupt, run_results() first gives
every call without a result INTERRUPTED so the transcript stays valid,
then steer() reads one line at the steer prompt and turn() appends it as a
user message. The loop goes on from there. A second Ctrl-C within
STEER_WINDOW seconds, or Ctrl-D, ends the turn and the chat. A Ctrl-C
inside a /command is caught by chat(). The rest is step 34: the loop
survives a bad model, a bad network and a bad crash; MAX_CALLS caps the
model calls of one turn; recover() finishes a resumed transcript that ends
in tool calls without results, and a call that fails there becomes an
Error: result instead of a crash at start-up.
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
from . import history
from . import hooks
from . import jobs
from . import mcp_client
from . import plan
from . import prompt
from . import sandbox
from . import session
from . import todos
from . import tools
from .context import reminder
from .llm import build_system_prompt, call_llm, with_mode
from .todos import active_form
from .ask_user import NO_ANSWER
from .tools import INTERRUPTED, active_schemas, execute_all
from .ui import ui

MAX_CALLS = 40      # model calls one turn may make before the loop stops and asks
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
    ends when the model answers without tool calls, when a model call
    fails for good, or when MAX_CALLS calls have been made. A Ctrl-C
    anywhere in the turn reads a steering message and goes on; a second
    one within STEER_WINDOW seconds raises KeyboardInterrupt out of the
    turn, with the transcript valid and saved.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    messages.append({"role": "user", "content": user_input})
    session.save(messages)  # the question is on disk before the first model call
    detector = durability.LoopDetector()
    calls = 0  # model calls so far in this turn
    usage = {}

    while True:
        if calls >= MAX_CALLS:
            ui.note(f"stopped after {calls} model calls in one turn; say 'continue' to go on")
            break
        try:
            calls, message, usage, allowed = one_call(messages, submitted.context, calls, debug)
        except KeyboardInterrupt:
            if not steered(messages, "the turn"):  # run_results has answered every call by now
                raise
            continue  # a new request, with the steering message at the end
        if message is None or not message.tool_calls:
            break

        repeated = detector.observe(message.tool_calls)
        for tool_call, flag in zip(message.tool_calls, repeated):
            if flag:
                ui.note(f"repeated call detected: {tool_call.function.name} with the same arguments {durability.REPEAT_LIMIT} times in a row")
        try:
            run_results(messages, message.tool_calls, repeated, allowed)
        except KeyboardInterrupt:
            if not steered(messages, "the tool calls"):  # every call has a result by now
                raise

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, len(messages)):
        messages = commands.compact(messages)
    return messages


def one_call(messages, hook_context, calls, debug):
    """One model call: the late block, the request, the reply into the transcript.

    Returns (calls, message, usage, allowed); message is None when the call
    failed for good and nothing went in the transcript, and allowed is the
    set of tool names the model was offered. A KeyboardInterrupt from
    anywhere in here - the git status in the late block, the request, the
    stream - leaves the transcript as it was, with the interrupted call
    counted.
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

        schemas = active_schemas(plan.toolset())
        allowed = {s["function"]["name"] for s in schemas}  # what the model was offered is all it may run
        estimate = budget.breakdown(messages)["total"]  # what this request should cost
        with spinner:
            message, usage = call_llm(with_mode(messages) + [injection], tools=schemas, on_delta=on_delta, on_restart=on_restart)
    except KeyboardInterrupt:
        if streamed:
            ui.stream_end()  # the part that arrived is on screen, but it goes nowhere: a reply is whole or absent
        raise
    finally:
        calls += 1

    if getattr(message, "failed", None):
        if streamed:
            ui.stream_end()  # a stream that broke may have shown part of a reply
        ui.note(message.failed)  # the model never answered; nothing goes in the transcript
        return calls, None, usage, allowed

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
    return calls, message, usage, allowed


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


def run_results(messages, tool_calls, repeated=None, allowed=None):
    """Run the tool calls of one reply and append their results in order.

    A call flagged in `repeated` does not run: its result is REPEATED, so
    the model reads why nothing new came back. The rest are decided first,
    run together, then reported in order, as before. `allowed` is the set
    of tool names the model was offered; a call to any other name is
    denied, so the offered set is the runnable set.

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
            execute_all(fresh, outcomes, allowed)
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
    and saved. A call that fails to run - the very thing that may have
    crashed the last run - becomes an Error: result, so a resume never
    crashes on the same call twice. A transcript that ends anywhere else is
    left alone.
    """
    pending = durability.unanswered(messages)
    if not pending:
        return 0
    # the edits belong to the turn that crashed: the one that began at the last user message
    start = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=len(messages))
    checkpoint.TURN = max(checkpoint.turns(), default=0) or checkpoint.begin_turn(start)
    try:
        run_results(messages, pending)
    except Exception as failed:  # noqa: BLE001 - whatever broke, the transcript must end whole
        answered = {m.get("tool_call_id") for m in messages if m.get("role") == "tool"}
        for call in pending:
            if call.id not in answered:
                messages.append({"role": "tool", "tool_call_id": call.id, "content": f"Error: {type(failed).__name__}: {failed}"})
        session.save(messages)
    count = len(pending)
    ui.note(f"recovered {count} tool call{'s' if count != 1 else ''} left unanswered by the last run")
    return count


def resume(messages):
    """Point the module state at a loaded transcript: strip it, rebuild todos and loaded tools, recover."""
    history.strip(messages)
    todos.from_transcript(messages)
    tools.relearn(messages)
    ui.resumed(messages)
    ui.replay(messages)
    recover(messages)  # a crash mid-turn left tool calls without results: run them now
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
    run.add_argument("--workspace", metavar="DIR", help="grade a copy of DIR with every task's checker; the agent does not run")
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
    if not cli.resume:
        session.save = lambda messages: None  # a one-shot answer is not a chat to resume
    try:
        messages = turn(messages, cli.print, cli)
    except KeyboardInterrupt:
        raise SystemExit(130)  # the exit code a shell gives an interrupted command
    answer = last_reply(messages)
    print(answer)
    raise SystemExit(0 if answer else 1)


def chat(cli):
    if cli.print:
        ui.headless()
    else:
        ui.banner(sandbox.name(), plan.MODE)
    mcp_client.connect_all()  # external tools join the registry before the first turn
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    messages = [{"role": "system", "content": build_system_prompt()}]  # after connect_all: the deferred list is complete

    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = resume(session.open_session(saved[0]["id"]))

    if cli.print:
        headless(messages, cli)

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
                    ui.note("command interrupted")  # a /pipeline or /init cut short; the files it wrote stay
                session.save(messages)
            else:
                messages = turn(messages, user_input, cli)
        except KeyboardInterrupt:
            break  # a second Ctrl-C, or Ctrl-D at the steer prompt: the transcript is saved

    ui.summary()


if __name__ == "__main__":
    main()
