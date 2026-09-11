"""Stage 3 - the loop from 2.4, drawn by ui.py and wrapped in a chat.

Two loops now. The outer one asks you for the next message and keeps the
transcript alive between turns. The inner one is stage 2.4 unchanged: call,
append, run tools, append, repeat until the model answers in text.

Run:   python agent.py
"""

import json

from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS
from ui import ui

ui.banner()

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_input = ui.ask()
    if not user_input:
        break

    messages.append({"role": "user", "content": user_input})

    while True:
        with ui.working():
            message, usage = call_llm(messages)

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = TOOLS[tool_call.function.name](**args)
            ui.tool(tool_call.function.name, args, result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

ui.summary()
