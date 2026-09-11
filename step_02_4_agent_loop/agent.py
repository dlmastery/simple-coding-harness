"""Stage 2.4 - the agent loop (video 12:07 - 16:50).

"An agent is something that loops around an LLM call." This file is the
harness loop: call the model, append its reply, run every tool it asked
for, append each result with role "tool", and go again until a reply has no
tool calls.

Run:   python agent.py
"""

import json

from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS

user_input = input("Enter your prompt> ")

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input},
]

while True:
    # 1. the model sees the whole transcript so far
    message, usage = call_llm(messages)
    # 2. its reply joins the transcript - tool calls included, because every
    #    "tool" message must follow the assistant message that asked for it
    messages.append(message.model_dump(exclude_none=True))

    if message.content:
        print("\nAgent: ", message.content, "\n")

    # 3. no tool calls means it has answered; the loop is done
    if not message.tool_calls:
        break

    # 4. otherwise run each call and feed the result back, tied to the call by id
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    print(usage)
