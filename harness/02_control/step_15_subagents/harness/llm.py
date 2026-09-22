"""Stage 15 - the system prompt tells the model when to delegate to a task subagent.
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

For any task that takes more than one step, call write_todos first and plan it
out. Send the whole list every time you call it - it replaces the old one.
Keep at most one task in_progress, mark it completed the moment it is finished,
and move the next one to in_progress in the same call. Skip the tool entirely
for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.

Long tool output is cut short, and the whole thing is written to a temp file
whose path is given at the cut. Page through it with head, tail, sed -n or
grep rather than asking for it again. That file only exists for the current
turn, so read it now or re-run the command later.

When you need to understand how something works - where a feature lives, how
data flows, what calls what - send a task subagent instead of grepping your
way there yourself. It explores in its own context window and hands you back
just the findings, so the search does not fill yours. It cannot see this
conversation, so write the question so it stands alone. Do all editing
yourself; the subagent only reads.

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


def call_llm(messages, tools=None):
    """tools=None means the full registry; tools=[] means no tools (the compaction agent)."""
    request = {"model": MODEL, "messages": messages}
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    response = client.chat.completions.create(**request)
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
