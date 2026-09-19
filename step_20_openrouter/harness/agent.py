"""Stage 15 - the loop hands every tool call to tools.execute(), which the subagent
shares - same permissions, same sandbox.
"""

import argparse

import openai

from . import commands
from . import compact
from . import context
from . import history
from . import sandbox
from . import session
from . import todos
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm, entry
from .todos import active_form
from .tools import execute
from .ui import ui

MAX_CALLS = 40  # model calls per user turn; a runaway loop stops here, the transcript stays valid


def interrupted(messages):
    """ctrl-c mid-turn: answer every unanswered tool call so the transcript stays sendable."""
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    last = next((m for m in reversed(messages) if m["role"] == "assistant"), {})
    for call in last.get("tool_calls") or []:
        if call["id"] not in answered:
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": "(interrupted before this tool ran)"})
    ui.note("interrupted")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="continue the last session")
    parser.add_argument("--debug", action="store_true", help="show the raw model response")
    cli = parser.parse_args()

    ui.banner(sandbox.name())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if cli.resume:
        saved = session.all_sessions()
        if saved:
            messages = session.open_session(saved[0]["id"])
            history.strip(messages)
            todos.rebuild(messages)
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

        messages.append({"role": "user", "content": user_input})
        session.save(messages)
        usage = {}

        try:
            for _ in range(MAX_CALLS):
                injection = reminder()
                ui.injection(injection["content"])

                if history.fit(messages):
                    ui.note("dropped old tool output to make this request fit")

                try:
                    with ui.working(active_form()):
                        message, usage = call_llm(messages + [injection])
                except (openai.APIError, RuntimeError) as failure:
                    ui.note(f"model call failed: {failure}")
                    break  # the user message stays; ask again or try /route
                context.mark_seen()

                messages.append(entry(message))
                session.save(messages)
                ui.usage(usage)

                if cli.debug:
                    ui.debug(entry(message))

                if message.content:
                    ui.agent(message.content)

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
            interrupted(messages)
            session.save(messages)
            continue

        history.sweep()          # the turn is over: bin its temp files...
        history.strip(messages)  # ...and shrink the tool output it produced

        if compact.needed(usage, messages):
            messages = commands.compact(messages)

    ui.summary()


if __name__ == "__main__":
    main()
