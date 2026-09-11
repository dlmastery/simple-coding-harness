"""Stage 7 - the loop, unchanged from stage 6.

`call_llm(messages + [reminder()])` is the only change. "We never touch the
messages array itself. So in future turns, the old dates and the old git
statuses never get shown to the agent."

Run:   python agent.py
"""

import json

from context import reminder
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
            message, usage = call_llm(messages + [reminder()])  # request = transcript + late block

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
