"""Stage 8 - sessions, slash commands and rewind.

Every message is saved as it happens, `--resume` reopens the last chat,
`/sessions` opens any chat and `/rewind` cuts the transcript back. `--debug`
shows the raw model reply. The inner loop is still stage 7's; the only
additions are the `session.save` calls and the slash-command branch.

Run:   python agent.py [--resume] [--debug]
"""

import argparse

import openai

import commands
import session
from context import reminder
from llm import SYSTEM_PROMPT, call_llm, entry
from tools import run_tool
from ui import ui

MAX_CALLS = 40  # model calls per turn

parser = argparse.ArgumentParser()
parser.add_argument("--resume", action="store_true", help="continue the last session")
parser.add_argument("--debug", action="store_true", help="show the raw model response")
cli = parser.parse_args()

ui.banner()

messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if cli.resume:
    saved = session.all_sessions()
    if saved:
        messages = session.open_session(saved[0]["id"])
        ui.resumed(messages)
        ui.replay(messages)

while True:
    user_input = ui.ask()
    if user_input is None or user_input in ("/exit", "/quit"):  # ctrl-d, ctrl-c, or asked to leave
        break
    if not user_input:  # an empty line is not a message
        continue

    if user_input.startswith("/"):  # anything starting with / is a command, never a message
        messages = commands.handle(user_input, messages)
        session.save(messages)
        continue

    messages.append({"role": "user", "content": user_input})
    session.save(messages)  # on disk before the model answers: ctrl-c during the call loses nothing

    try:
        for _ in range(MAX_CALLS):
            injection = reminder()
            ui.injection(injection["content"])

            with ui.working():
                message, usage = call_llm(messages + [injection])  # request = transcript + late block

            messages.append(entry(message))
            session.save(messages)
            ui.usage(usage)

            if cli.debug:
                ui.debug(message.model_dump(exclude_none=True))

            if message.content:
                ui.agent(message.content)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args, result = run_tool(tool_call)
                ui.tool(tool_call.function.name, args, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
                session.save(messages)  # after every message, so a crash loses nothing
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
    except KeyboardInterrupt:  # ctrl-c mid-turn: keep the transcript valid and ask again
        session.repair(messages, "(interrupted before this tool ran)")
        session.save(messages)
        ui.note("interrupted")
    except (openai.APIError, RuntimeError) as e:  # the user message stays; try again later
        ui.note(f"model call failed: {e}")

ui.summary()
