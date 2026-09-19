"""Stage 2.3 - unchanged from 2.2: adding read_file touched only tools.py.

The tool is looked up by name in a table. The model's `tool_call.function.name`
becomes a dictionary key and the JSON arguments become keyword arguments.

Run:   python llm.py
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

try:
    user_input = input("Enter your prompt> ")
except (EOFError, KeyboardInterrupt):
    sys.exit("\nno prompt given")

SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Answer back to the user once exploration is done.
"""

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        tools=TOOL_SCHEMAS,
    )
except openai.APIError as e:
    sys.exit(f"model call failed: {e}")

if not response.choices:
    sys.exit(f"empty reply: {getattr(response, 'error', None)}")

message = response.choices[0].message
output = message.content

u = response.usage
usage = {
    "prompt_tokens": getattr(u, "prompt_tokens", None),
    "completion_tokens": getattr(u, "completion_tokens", None),
    "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
    "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
}
print("\nAgent: ", output, "\n")

if message.tool_calls:
    tool_call = message.tool_calls[0]
    args, result = run_tool(tool_call)  # name -> function, JSON -> kwargs, errors -> text
    print("Tool: ", tool_call.function.name, args)
    print(result, "\n")

print(usage)
