"""Step 02 - one streamed model call over the OpenAI-compatible API.

Settings come from the environment or from ~/.simple-harness/env, a file of
KEY=VALUE lines that is read and never printed. The env var API_KEY wins;
OPENAI_API_KEY fills the gap so the file needs no edit.
"""

import os
from pathlib import Path

try:
    import truststore

    truststore.inject_into_ssl()  # this machine's TLS proxy needs the system store
except ImportError:
    pass

from openai import OpenAI

ENV_FILE = Path.home() / ".simple-harness" / "env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")

# The tests replace this with a fake that yields scripted chunks.
client = OpenAI(base_url=BASE_URL, api_key=API_KEY) if API_KEY else None


def usage_from(chunk_usage):
    """The usage of the final chunk, or all None when none came."""
    if chunk_usage is None:
        return {"prompt_tokens": None, "completion_tokens": None}
    return {"prompt_tokens": chunk_usage.prompt_tokens, "completion_tokens": chunk_usage.completion_tokens}


def stream_chat(messages, tools=None, response_format=None):
    """One streamed request, as a generator of events.

    {"type": "text", "text": ...}                            one per text delta
    {"type": "tool_call", "id", "name", "arguments"}         one per call, in index order, after the stream
    {"type": "usage", "prompt_tokens", "completion_tokens"}  last

    A tool call streams as pieces that share an index. Pieces of different
    calls may interleave and some providers omit the index, so every call is
    assembled until the stream ends; a piece without an index joins the call
    with its id, or the last one opened.
    """
    if client is None:
        raise RuntimeError("no API key: set API_KEY (or OPENAI_API_KEY) in the environment or ~/.simple-harness/env")
    request = {"model": MODEL, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
    if tools:
        request["tools"] = tools
    if response_format:
        request["response_format"] = response_format  # {"type": "json_object"} keeps fences out
    stream = client.chat.completions.create(**request)

    calls = {}          # tool call index -> {"id", "name", "arguments"} being assembled
    final_usage = None  # arrives with the last chunk, which has no choices
    last_index = None

    for chunk in stream:
        if getattr(chunk, "usage", None) is not None:
            final_usage = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue

        if delta.content:
            yield {"type": "text", "text": delta.content}

        for piece in delta.tool_calls or []:
            index = piece.index
            if index is None:  # no index: the piece belongs to the call with its id, else the last one
                index = next((i for i, c in calls.items() if piece.id and c["id"] == piece.id), last_index)
                index = len(calls) if index is None else index
            call = calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
            last_index = index
            if piece.id:
                call["id"] = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call["name"] = function.name
            if function.arguments:
                call["arguments"] += function.arguments

    for index in sorted(calls):
        yield {"type": "tool_call", **calls[index]}
    yield {"type": "usage", **usage_from(final_usage)}
