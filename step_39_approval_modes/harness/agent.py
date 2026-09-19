"""Step 39 - the --mode flag starts the chat in an approval mode, and the
banner shows it. The loop itself is unchanged: the mode acts inside
permissions.check, before any prompt.
The rest is step 38: `harness eval --workspace DIR` grades a copy of DIR with
every task's checker and runs no model turn. The rest is step 35: the user
can steer a running turn. Ctrl-C during a model call
or during the tool calls does not kill the loop: turn() catches the
KeyboardInterrupt, run_results() first gives every call without a result
INTERRUPTED so the transcript stays valid, then steer() reads one line at
the steer prompt and turn() appends it as a user message. The loop goes on
from there. A second Ctrl-C within STEER_WINDOW seconds, or Ctrl-D, ends
the turn and the chat. The rest is step 34: the loop survives a bad model,
a bad network and a bad crash; MAX_CALLS caps the model calls of one turn;
recover() finishes a resumed transcript that ends in tool calls without
results.
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
from . import modes
from . import plan
from . import prompt
from . import sandbox
from . import session
from .context import reminder
from .llm import build_system_prompt, call_llm, with_mode
from .todos import active_form, rebuild as rebuild_todos
from .tools import INTERRUPTED, active_schemas, execute_all, rebuild_loaded
from .ui import ui

MAX_CALLS = 40      # model calls one turn may make before the loop stops and asks
STEER_WINDOW = 2.0  # seconds: a second Ctrl-C within this many after the first exits

EXIT_WORDS = ("/exit", "/quit")  # typed at the prompt, they end the chat like ctrl-d


class LeaveChat(KeyboardInterrupt):
    """The user asked to leave at the steer prompt: a second Ctrl-C, or Ctrl-D. The chat loop ends on it."""


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
    during the model call or the tool calls reads a steering message and
    goes on; a second one within STEER_WINDOW seconds raises
    KeyboardInterrupt out of the turn, with the transcript valid and saved.
    """
    debug = getattr(cli, "debug", False)

    submitted = hooks.run_hooks("UserPromptSubmit", {"prompt": user_input})
    if submitted.blocked:
        ui.note(f"prompt blocked by hook: {submitted.reason}")
        return messages
    checkpoint.begin_turn(len(messages))  # where /undo cuts back to, and what the captures are keyed by
    messages.append({"role": "user", "content": user_input})
    session.save(messages)  # the question is on disk before the first call, whatever happens next
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
        try:
            with spinner:
                message, usage = call_llm(with_mode(messages) + [injection], tools=active_schemas(plan.toolset()), on_delta=on_delta)
        except KeyboardInterrupt:
            if streamed:
                ui.stream_end()  # the part that arrived is on screen, but it goes nowhere: a reply is whole or absent
            calls += 1
            if not steered(messages, "the model call"):
                raise LeaveChat()
            continue  # a new request, with the steering message at the end
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
        try:
            run_results(messages, message.tool_calls, repeated)
        except KeyboardInterrupt:
            if not steered(messages, "the tool calls"):  # every call has a result by now
                raise LeaveChat()

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, len(messages)):
        messages = commands.compact(messages)
    return messages


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
    """Run the tool calls of one reply and append their results in order.

    A call flagged in `repeated` does not run: its result is REPEATED, so
    the model reads why nothing new came back. The rest are decided first,
    run together, then reported in order, as before.

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
            execute_all(fresh, outcomes)
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
    and saved. Whatever goes wrong on the way, every call ends up with a
    result: the transcript is valid when this returns. A transcript that
    ends anywhere else is left alone.
    """
    pending = durability.unanswered(messages)
    if not pending:
        return 0
    # the edits belong to the turn that crashed, so /undo takes them back with it
    start = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=len(messages))
    checkpoint.TURN = max(checkpoint.turns(), default=0) or checkpoint.begin_turn(start)
    try:
        run_results(messages, pending)
    except Exception as failed:  # noqa: BLE001 - the calls that got no result get the failure as one
        answered = {m.get("tool_call_id") for m in messages if m.get("role") == "tool"}
        for call in pending:
            if call.id not in answered:
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


def headless():
    """Print mode without a terminal: nothing may wait for a keyboard.

    Every approve prompt is answered n with a note on stderr, and ask_user
    tells the model that nobody is there. With a terminal on stdin the
    prompts still work, so `harness -p` at a shell can still say yes.
    """
    from . import tools
    from .ask_user import NO_ANSWER

    ui.headless()
    if sys.stdin.isatty():
        return
    ui.approve = lambda reason: (ui.note(f"denied (no terminal to ask on): {reason}"), "n")[1]
    tools.TOOLS["ask_user"] = lambda question, options=None: NO_ANSWER


def resume(messages):
    """Open the newest session and put the state it implies back: todos, loaded tools, unanswered calls."""
    saved = session.all_sessions()
    if not saved:
        return messages
    messages = session.open_session(saved[0]["id"])
    history.strip(messages)
    rebuild_todos(messages)                        # the todo list the transcript last wrote
    rebuild_loaded(messages)                       # the deferred tools it loaded
    ui.resumed(messages)
    ui.replay(messages)
    recover(messages)  # a crash mid-turn left tool calls without results: run them now
    return messages


def chat(cli):
    if cli.print:
        headless()
        session.ENABLED = bool(cli.resume)  # a one-off question leaves no session behind
    if cli.mode:
        modes.set_mode(cli.mode)  # before the banner and the first check; logged, so --resume comes back in it
    if not cli.print:
        ui.banner(sandbox.name(), modes.current())
    mcp_client.connect_all()  # external tools join the registry before the first turn
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    messages = [{"role": "system", "content": build_system_prompt()}]  # after connect_all: the deferred list is complete

    if cli.resume:
        messages = resume(messages)

    if cli.print:
        try:
            messages = turn(messages, cli.print, cli)
        except KeyboardInterrupt:
            raise SystemExit(130)  # the exit code a shell gives an interrupted command
        answer = last_reply(messages)
        print(answer)
        raise SystemExit(0 if answer.strip() else 1)  # no answer is a failure a script can see

    while True:
        user_input = ui.ask()
        if user_input is None or user_input in EXIT_WORDS:
            break  # ctrl-d, ctrl-c at the prompt, /exit
        if not user_input:
            continue  # an empty line is not a message

        try:
            if user_input.startswith("/"):
                messages = commands.handle(user_input, messages)
                session.save(messages)
            else:
                messages = turn(messages, user_input, cli)
        except LeaveChat:
            break  # a second Ctrl-C, or Ctrl-D at the steer prompt: the transcript is saved
        except KeyboardInterrupt:
            ui.note("interrupted; the transcript is saved")  # a Ctrl-C outside the steer prompts: the chat goes on
            session.save(messages)

    ui.summary()


if __name__ == "__main__":
    main()
