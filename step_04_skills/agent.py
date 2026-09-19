"""Stage 4 - the loop, unchanged from stage 3.

Two loops. The outer one asks you for the next message and keeps the
transcript alive between turns. The inner one is stage 2.4 unchanged: call,
append, run tools, append, repeat until the model answers in text.

Run:   python agent.py
"""

import openai

from llm import SYSTEM_PROMPT, call_llm, entry
from tools import run_tool
from ui import ui

MAX_CALLS = 40  # model calls per turn


def repair(messages, note):
    """Give every tool call at the end of the transcript that has no result one, so the
    next request is valid. Used when a turn is interrupted between a call and its result."""
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    last = next((m for m in reversed(messages) if m["role"] != "tool"), None)
    if last and last["role"] == "assistant":
        for call in last.get("tool_calls") or []:
            if call["id"] not in answered:
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": note})


ui.banner()

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_input = ui.ask()
    if user_input is None or user_input in ("/exit", "/quit"):  # ctrl-d, ctrl-c, or asked to leave
        break
    if not user_input:  # an empty line is not a message
        continue

    messages.append({"role": "user", "content": user_input})

    try:
        for _ in range(MAX_CALLS):
            with ui.working():
                message, usage = call_llm(messages)

            messages.append(entry(message))
            ui.usage(usage)

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
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
    except KeyboardInterrupt:  # ctrl-c mid-turn: keep the transcript valid and ask again
        repair(messages, "(interrupted before this tool ran)")
        ui.note("interrupted")
    except (openai.APIError, RuntimeError) as e:  # the user message stays; try again later
        ui.note(f"model call failed: {e}")

ui.summary()
