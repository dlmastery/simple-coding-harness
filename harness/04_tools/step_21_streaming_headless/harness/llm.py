"""Step 21 - call_llm streams. Text deltas reach the caller as they arrive; tool
calls are assembled chunk by chunk; the usage comes with the final chunk.

The loop in agent.py appends `entry(message)` and reads `message.content` and
`message.tool_calls`. The StreamedMessage dataclass below keeps that exact
surface, so nothing downstream knows the reply was streamed.
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

# OpenRouter reports the price of a call when asked; other gateways ignore the field.
EXTRA_BODY = {"usage": {"include": True}} if "openrouter" in config.BASE_URL else {}

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

    def model_dump(self, exclude_none=True):
        """The dict entry() stores for this call: id, type and the function."""
        return {"id": self.id, "type": self.type, "function": {"name": self.function.name, "arguments": self.function.arguments}}


@dataclass
class StreamedMessage:
    """The assembled reply. Same surface as the SDK's ChatCompletionMessage."""

    content: str | None = None
    tool_calls: list[StreamedToolCall] | None = None
    role: str = "assistant"

    def model_dump(self, exclude_none=True):
        """The same three keys entry() keeps - there is nothing else to drop."""
        return entry(self)


def usage_from(usage):
    """Token counts as a plain dict. Some proxies send no usage at all."""
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
        "cost": getattr(usage, "cost", None),  # OpenRouter, in dollars; None everywhere else
    }


CUT_OFF = "(reply cut off by max_tokens)"


def call_llm(messages, tools=None, on_delta=None):
    """One streamed request. Returns (message, usage).

    tools=None means the full registry; tools=[] means no tools (the
    compaction agent). on_delta, if given, is called with every piece of
    text as it arrives.
    """
    request = {"model": MODEL, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
    if EXTRA_BODY:
        request["extra_body"] = EXTRA_BODY
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    stream = client.chat.completions.create(**request)

    parts = []           # text deltas, in order
    calls = {}           # tool call index -> StreamedToolCall
    final_usage = None   # arrives with the last chunk, which has no choices
    finish_reason = None

    for chunk in stream:
        if getattr(chunk, "error", None):  # a gateway can answer an error as a chunk
            raise RuntimeError(f"model call failed: {chunk.error}")
        if getattr(chunk, "usage", None) is not None:
            final_usage = chunk.usage
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        finish_reason = getattr(choice, "finish_reason", None) or finish_reason
        delta = choice.delta
        if delta is None:
            continue

        if delta.content:
            parts.append(delta.content)
            if on_delta:
                on_delta(delta.content)

        for piece in delta.tool_calls or []:
            # fragments of one call share an index; a provider that sends none gets keyed by id
            key = piece.index if getattr(piece, "index", None) is not None else piece.id or len(calls)
            call = calls.setdefault(key, StreamedToolCall())
            if piece.id:
                call.id = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call.function.name = function.name
            if function.arguments:
                call.function.arguments += function.arguments

    if finish_reason == "length" and calls:
        # the arguments stopped mid-JSON: no call is safe to run, say so instead
        calls = {}
        parts.append(f"\n{CUT_OFF}")
        if on_delta:
            on_delta(f"\n{CUT_OFF}")

    message = StreamedMessage(
        content="".join(parts) or None,
        tool_calls=[calls[key] for key in sorted(calls, key=str)] or None,
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

    print(entry(message))
    print(usage)
