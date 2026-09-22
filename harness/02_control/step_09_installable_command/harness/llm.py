"""Stage 9 - call_llm reads its credentials from config.py.
"""

import os

from openai import OpenAI

from . import config
from .skills import skills_prompt
from .tools import TOOL_SCHEMAS

client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
MODEL = config.MODEL

SYSTEM_PROMPT = f"""
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Use write_file to create files and str_replace to edit them.
Answer back to the user once exploration is done.

Your current working directory is: {os.getcwd()}

You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
"""


def entry(message):
    """The transcript entry for a reply: role, content and tool_calls, nothing else.

    Providers attach extras (reasoning, annotations) that must not be sent
    back on the next call, so the whole message is never dumped as it is.
    """
    saved = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        saved["tool_calls"] = [call.model_dump(exclude_none=True) for call in message.tool_calls]
    return saved


def usage_from(usage):
    """Token counts as a plain dict. Some proxies send no usage at all."""
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
    }


def call_llm(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    if not response.choices:  # some providers answer an error as an empty reply
        raise RuntimeError(getattr(response, "error", None) or "empty reply")

    return response.choices[0].message, usage_from(response.usage)


if __name__ == "__main__":
    user_input = input("Enter your prompt> ")

    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])

    print("\nAgent: ", message.content, "\n")
    print(entry(message))
    print(usage)
