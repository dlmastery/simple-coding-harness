"""Stage 1 - a minimal chat completion round trip.

One prompt in, one reply out. A system message, a user message, the model's
answer, and the usage numbers. This is the whole program, and every later
stage is this file plus one more idea.

Run:   python llm.py
Needs: BASE_URL and API_KEY in the environment. The defaults point at
       OpenRouter with deepseek/deepseek-v4-flash; MODEL overrides that.
"""

import os

from openai import OpenAI

client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)

MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")

user_input = input("Enter your prompt> ")

SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
"""

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
)

output = response.choices[0].message.content

completion_details = response.usage.completion_tokens_details
prompt_details = response.usage.prompt_tokens_details

usage = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
    "cached_tokens": getattr(prompt_details, "cached_tokens", None),
}

print("\nAgent: ", output, "\n")
print(usage)
