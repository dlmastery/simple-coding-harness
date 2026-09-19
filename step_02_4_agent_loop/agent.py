"""Stage 2.4 - the agent loop.

An agent is a loop around a model call. This file is the harness loop:
call the model, append its reply, run every tool call it asked for, append
each result with role "tool", and call again until a reply has no tool
calls.

Run:   python agent.py
"""

import sys

import openai

from llm import SYSTEM_PROMPT, call_llm, entry
from tools import run_tool

MAX_CALLS = 40  # model calls per question; a model that never stops calling tools stops here

try:
    user_input = input("Enter your prompt> ")
except (EOFError, KeyboardInterrupt):
    sys.exit("\nno prompt given")

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input},
]

for _ in range(MAX_CALLS):
    # 1. the model sees the whole transcript so far
    try:
        message, usage = call_llm(messages)
    except (openai.APIError, RuntimeError) as e:
        sys.exit(f"model call failed: {e}")
    # 2. its reply joins the transcript - tool calls included, because every
    #    "tool" message must follow the assistant message that asked for it
    messages.append(entry(message))
    print(usage)

    if message.content:
        print("\nAgent: ", message.content, "\n")

    # 3. no tool calls means it has answered; the loop is done
    if not message.tool_calls:
        break

    # 4. otherwise run each call and feed the result back, tied to the call by id.
    #    run_tool never raises, so every call gets its tool message, error or not
    for tool_call in message.tool_calls:
        args, result = run_tool(tool_call)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
else:
    print(f"stopped after {MAX_CALLS} model calls; the model kept calling tools")
