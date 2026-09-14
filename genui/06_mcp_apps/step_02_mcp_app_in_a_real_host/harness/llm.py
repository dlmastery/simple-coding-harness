"""Step 26 - the system prompt names the MCP tools. call_llm streams, as before.

The loop in agent.py appends `message.model_dump(exclude_none=True)` and reads
`message.content` and `message.tool_calls`. The StreamedMessage dataclass
below keeps that exact surface, so nothing downstream knows the reply was
streamed.
"""

import json
import os
from dataclasses import dataclass, field

from openai import OpenAI

from . import config
from .skills import skills_prompt
from .tools import TOOLS, TOOL_SCHEMAS

client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
MODEL = config.MODEL

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

When a task needs a web page - reading documentation, checking a page,
filling a form - call browse with the URL and the steps. It drives a real
browser in its own context window and returns a short report; page contents
never enter this conversation. It cannot see this conversation either, so
say exactly what to find or do. It never enters credentials.

When a task needs the desktop itself - an application window, a dialog, a
program without a command line - use the computer tools yourself. Call
computer_screen once, then computer_screenshot; the picture arrives in the
next message. Act with computer_act, then take a new screenshot to check
what happened. Never guess coordinates from memory: look first, act, look
again. Report what you see, and stop if the screen asks for a password.

You have a memory that lasts across sessions. The <memory> block in every
turn lists what is stored, one line per memory. Call remember for durable
facts: who the user is and how they like to work, how this project is built
and run, a correction the user made, a link or ticket worth keeping. Do not
store what the code or git history already records. Before asking the user
something you may already know, look at the <memory> block and call recall
on the matching entry. Call forget when a memory turns out to be wrong.

Tools named mcp__<server>__<tool> come from MCP servers the user configured.
They run in another process; call them like any other tool and read the
result as text. If one returns Error:, say so and do not retry blindly.

When several tool calls do not depend on each other - reading three files,
running two greps - put them all in one reply. They run at the same time and
the results come back together, in order. A call that needs the result of
another one goes in the next reply.

Long tool output is cut short, and the whole thing is written to a temp file
whose path is given at the cut. Page through it with head, tail, sed -n or
grep rather than asking for it again. That file only exists for the current
turn, so read it now or re-run the command later.

Your current working directory is: {os.getcwd()}

You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
"""


@dataclass
class StreamedFunction:
    """The name and the JSON arguments of one tool call, built up from deltas."""

    name: str = ""
    arguments: str = ""


@dataclass
class StreamedToolCall:
    """One tool call. Same attributes as the SDK's ChatCompletionMessageToolCall."""

    id: str = ""
    type: str = "function"
    function: StreamedFunction = field(default_factory=StreamedFunction)


@dataclass
class StreamedMessage:
    """The assembled reply. Same surface as the SDK's ChatCompletionMessage."""

    content: str | None = None
    tool_calls: list[StreamedToolCall] | None = None
    role: str = "assistant"

    def model_dump(self, exclude_none=True):
        """The dict the loop appends to the transcript."""
        entry = {"role": self.role, "content": self.content, "tool_calls": None}
        if self.tool_calls:
            entry["tool_calls"] = [
                {"id": c.id, "type": c.type, "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in self.tool_calls
            ]
        if exclude_none:
            entry = {k: v for k, v in entry.items() if v is not None}
        return entry


def usage_from(chunk_usage):
    """The same usage dict the non-streaming call produced. All None if no usage came."""
    if chunk_usage is None:
        return {"prompt_tokens": None, "completion_tokens": None, "reasoning_tokens": None, "cached_tokens": None}
    completion_details = getattr(chunk_usage, "completion_tokens_details", None)
    prompt_details = getattr(chunk_usage, "prompt_tokens_details", None)
    return {
        "prompt_tokens": chunk_usage.prompt_tokens,
        "completion_tokens": chunk_usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
    }


def call_llm(messages, tools=None, on_delta=None):
    """One streamed request. Returns (message, usage).

    tools=None means the full registry; tools=[] means no tools (the
    compaction agent). on_delta, if given, is called with every piece of
    text as it arrives.
    """
    request = {"model": MODEL, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    stream = client.chat.completions.create(**request)

    parts = []          # text deltas, in order
    calls = {}          # tool call index -> StreamedToolCall
    final_usage = None  # arrives with the last chunk, which has no choices

    for chunk in stream:
        if getattr(chunk, "usage", None) is not None:
            final_usage = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue

        if delta.content:
            parts.append(delta.content)
            if on_delta:
                on_delta(delta.content)

        for piece in delta.tool_calls or []:
            call = calls.setdefault(piece.index, StreamedToolCall())
            if piece.id:
                call.id = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call.function.name = function.name
            if function.arguments:
                call.function.arguments += function.arguments

    message = StreamedMessage(
        content="".join(parts) or None,
        tool_calls=[calls[index] for index in sorted(calls)] or None,
    )
    return message, usage_from(final_usage)


if __name__ == "__main__":
    user_input = input("Enter your prompt> ")

    print("\nAgent: ", end="", flush=True)
    message, usage = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ], on_delta=lambda text: print(text, end="", flush=True))
    print("\n")

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

    print(usage)
