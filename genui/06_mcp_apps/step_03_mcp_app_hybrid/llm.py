"""Step 03 - model calls over the OpenAI-compatible API: one for the host, one for the server.

Settings come from the environment or from ~/.simple-harness/env, a file of
KEY=VALUE lines that is read and never printed. The env var API_KEY wins;
OPENAI_API_KEY fills the gap so the file needs no edit.

Two processes import this module. The host (host.py) uses `complete` with
tools, as in step 01. The MCP server (server.py) uses `generate` for the
open-ended region of the report. Each process reads its own key; MCP Apps
keeps credentials on the server side, so the view and the host page never
see the server's.
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

# The tests replace this with a fake whose chat.completions.create returns a scripted reply.
client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120) if API_KEY else None  # a hung upstream fails the call, it does not hang it


def complete(messages, tools=None):
    """One request with tools. Returns {"content": str | None, "tool_calls": [{"id", "name", "arguments"}]}.

    The arguments stay a JSON string: the host page parses them, like the
    harness codelab's loop does.
    """
    if client is None:
        raise RuntimeError("no API key: set API_KEY (or OPENAI_API_KEY) in the environment or ~/.simple-harness/env")
    request = {"model": MODEL, "messages": messages}
    if tools:
        request["tools"] = tools
    message = client.chat.completions.create(**request).choices[0].message
    return {
        "content": message.content,
        "tool_calls": [
            {"id": call.id, "name": call.function.name, "arguments": call.function.arguments}
            for call in (message.tool_calls or [])
        ],
    }


def generate(messages):
    """One plain text request, with its cost. Returns {"content": str, "usage": {"prompt_tokens", "completion_tokens"}}.

    The server calls this once per tool call. The usage travels to the view
    in structuredContent, so the demo can print what the region cost.
    """
    if client is None:
        raise RuntimeError("no API key: set API_KEY (or OPENAI_API_KEY) in the environment or ~/.simple-harness/env")
    response = client.chat.completions.create(model=MODEL, messages=messages)
    if not response.choices:
        raise RuntimeError(f"empty reply: {getattr(response, 'error', None)}")
    usage = response.usage  # some proxies send none: the reply is still good
    return {
        "content": response.choices[0].message.content or "",
        "usage": {"prompt_tokens": getattr(usage, "prompt_tokens", None), "completion_tokens": getattr(usage, "completion_tokens", None)},
    }
