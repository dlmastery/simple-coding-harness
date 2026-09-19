"""Stage 20 - the client points at OpenRouter; call_llm sends the route and reads back the cost.

The loop in agent.py does not change. The two things that do: the client is
built with OpenRouter's base URL, key and attribution headers, and every
request carries `extra_body` from openrouter.request_extras() - the fallback
route, provider preferences and the ask for per-call cost.
"""

import json
import os

from openai import OpenAI

from . import config  # noqa: F401 - imported first so ~/.simple-harness/env is loaded
from . import openrouter
from .skills import skills_prompt
from .tools import TOOLS, TOOL_SCHEMAS

client = OpenAI(base_url=openrouter.BASE_URL, api_key=openrouter.API_KEY, default_headers=openrouter.HEADERS)

SYSTEM_PROMPT = f"""
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Use write_file to create files and str_replace to edit them.
Answer back to the user once exploration is done.

For any task that takes more than one step, call write_todos first and plan it
out. Send the whole list every time you call it - it replaces the old one.
Keep exactly one task in_progress, mark it completed the moment it is finished,
and move the next one to in_progress in the same call. Skip the tool entirely
for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.

When you need to understand how something works - where a feature lives, how
data flows, what calls what - send a task subagent instead of grepping your
way there yourself. It explores in its own context window and hands you back
just the findings, so the search does not fill yours. It cannot see this
conversation, so write the question so it stands alone. Do all editing
yourself; the subagent only reads.

Long tool output is cut short, and the whole thing is written to a temp file
whose path is given at the cut. Page through it with head, tail, sed -n or
grep rather than asking for it again. That file only exists for the current
turn, so read it now or re-run the command later.

Your current working directory is: {os.getcwd()}

You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
"""


def call_llm(messages, tools=None):
    """tools=None means the full registry; tools=[] means no tools (the compaction agent)."""
    request = {"model": openrouter.primary(), "messages": messages, **openrouter.request_extras()}
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    response = client.chat.completions.create(**request)

    if not response.choices:  # some providers answer an error as an empty reply
        raise RuntimeError(getattr(response, "error", None) or "empty reply")
    message = response.choices[0].message

    return message, usage_from(response)


def usage_from(response):
    """The numbers we keep per call. usage can be missing, and so can its details."""
    u = response.usage
    usage = {
        "prompt_tokens": getattr(u, "prompt_tokens", None),
        "completion_tokens": getattr(u, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
        "cost": openrouter.cost_of(u),
        # OpenRouter sets this to the model that actually answered, so a
        # fallback shows up here rather than passing silently.
        "model": getattr(response, "model", None),
    }
    return usage


def entry(message):
    """The transcript entry for a reply: role, content, tool calls - and nothing else.

    `message.model_dump()` would also echo reasoning, annotations and other
    provider extras back on the next request, and a fallback provider may
    reject them.
    """
    record = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        record["tool_calls"] = [c.model_dump(exclude_none=True) for c in message.tool_calls]
    return record


if __name__ == "__main__":
    user_input = input("Enter your prompt> ")

    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ])

    print("\nAgent: ", message.content, "\n")

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

    print(usage)
