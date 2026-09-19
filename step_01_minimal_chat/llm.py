"""Stage 1 - a minimal chat completion round trip.

One prompt in, one reply out. A system message, a user message, the model's
answer, and the usage numbers. This is the whole program, and every later
stage is this file plus one more idea.

Run:   python llm.py
Needs: BASE_URL and API_KEY in the environment; MODEL is optional and
       defaults to deepseek/deepseek-v4-flash (an OpenRouter model id).
"""

import os
import sys

import openai
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)

MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

try:
    user_input = input("Enter your prompt> ")
except (EOFError, KeyboardInterrupt):  # ctrl-d, ctrl-z+enter, ctrl-c, or nothing on stdin
    sys.exit("\nno prompt given")

SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
"""

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
    )
except openai.APIError as e:  # wrong key, wrong URL, model down: one line, no traceback
    sys.exit(f"model call failed: {e}")

if not response.choices:  # some providers answer an error as an empty reply
    sys.exit(f"empty reply: {getattr(response, 'error', None)}")

output = response.choices[0].message.content

# usage can be missing (some proxies), and its detail objects can be None
u = response.usage
usage = {
    "prompt_tokens": getattr(u, "prompt_tokens", None),
    "completion_tokens": getattr(u, "completion_tokens", None),
    "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
    "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
}

print("\nAgent: ", output, "\n")
print(usage)
