"""The model call for this step. One place for the settings and one
streaming function; everything else in the step talks AG-UI, not OpenAI.

Settings come from the environment or from ~/.simple-harness/env, a
KEY=VALUE file: API_KEY (OPENAI_API_KEY is accepted as an alias), BASE_URL
and MODEL. The file is read, never printed.
"""

import os
from pathlib import Path

from openai import OpenAI

try:  # on some machines Python needs the OS certificate store for live calls
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

ENV_FILE = Path.home() / ".simple-harness" / "env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
if "API_KEY" not in os.environ and "OPENAI_API_KEY" in os.environ:
    os.environ["API_KEY"] = os.environ["OPENAI_API_KEY"]

BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY or "missing")


def stream_chat(messages, tools=None):
    """One streamed chat completion with tools. Yields tuples as the pieces arrive:

        ("text", delta)
        ("tool_start", call_id, name)
        ("tool_args", call_id, delta)
        ("tool_end", call_id)

    The model streams tool calls one at a time, keyed by index. A new index
    ends the previous call; the end of the stream ends the last one.
    """
    request = {"model": MODEL, "messages": messages, "stream": True}
    if tools:
        request["tools"] = tools
    stream = client.chat.completions.create(**request)

    open_call = None  # (index, id) of the tool call being streamed
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue
        if delta.content:
            yield ("text", delta.content)
        for piece in delta.tool_calls or []:
            if open_call and open_call[0] != piece.index:
                yield ("tool_end", open_call[1])
                open_call = None
            if open_call is None:
                open_call = (piece.index, piece.id)
                yield ("tool_start", piece.id, piece.function.name)
            if piece.function and piece.function.arguments:
                yield ("tool_args", open_call[1], piece.function.arguments)
    if open_call:
        yield ("tool_end", open_call[1])
