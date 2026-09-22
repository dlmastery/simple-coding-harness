"""Stage 2.4 - llm.py becomes a function.

The chat completion request moves into call_llm(messages). agent.py owns
the message list and the loop and calls this function. entry(message)
turns a reply into the transcript entry the loop stores. Run this file on
its own and it still does the single-turn request from 2.3.
"""

import os
import sys

import openai
from openai import OpenAI

from tools import TOOL_SCHEMAS, run_tool

client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)

MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

SYSTEM_PROMPT = f"""
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Answer back to the user once exploration is done.

Your current working directory is: {os.getcwd()}
"""


def call_llm(messages):
    """One model call. Takes the whole transcript, returns (message, usage)."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )

    if not response.choices:  # some providers answer an error as an empty reply
        raise RuntimeError(getattr(response, "error", None) or "empty reply")
    message = response.choices[0].message

    u = response.usage  # can be None on some proxies; the detail objects can be None
    usage = {
        "prompt_tokens": getattr(u, "prompt_tokens", None),
        "completion_tokens": getattr(u, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
    }

    return message, usage


def entry(message):
    """The reply as a transcript entry: role, content and the tool calls, nothing else.
    Provider extras such as reasoning or annotations are not echoed back."""
    e = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        e["tool_calls"] = [c.model_dump(exclude_none=True) for c in message.tool_calls]
    return e


if __name__ == "__main__":
    try:
        user_input = input("Enter your prompt> ")
    except (EOFError, KeyboardInterrupt):
        sys.exit("\nno prompt given")

    try:
        message, usage = call_llm([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ])
    except (openai.APIError, RuntimeError) as e:
        sys.exit(f"model call failed: {e}")

    print("\nAgent: ", message.content, "\n")

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args, result = run_tool(tool_call)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

    print(usage)
