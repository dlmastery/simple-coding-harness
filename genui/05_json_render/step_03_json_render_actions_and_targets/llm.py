"""The model call. One OpenAI-compatible client, configured from the environment
or from ~/.simple-harness/env (KEY=VALUE lines; read, never printed).

stream_text() yields the model's reply as it arrives, chunk by chunk. The
tests replace it with a fake that yields scripted chunks.
"""

import os
from pathlib import Path

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

from openai import OpenAI

ENV_FILE = Path.home() / ".simple-harness" / "env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
os.environ.setdefault("API_KEY", os.environ.get("OPENAI_API_KEY", ""))

BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")

_client = None


def client():
    """The client, created on first use so importing this module needs no key."""
    global _client
    if _client is None:
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    return _client


class Stream:
    """Iterates over text deltas as they arrive. After the loop, .usage holds
    the token counts the API sends with its last chunk."""

    def __init__(self, response):
        self.response = response
        self.usage = None

    def __iter__(self):
        for chunk in self.response:
            if chunk.usage is not None:
                self.usage = {"prompt_tokens": chunk.usage.prompt_tokens, "completion_tokens": chunk.usage.completion_tokens}
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def stream_text(messages):
    """One streaming call on a transcript. No JSON mode: the reply is JSONL,
    one patch per line, and JSON mode would insist on a single object."""
    response = client().chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
        temperature=0.2,
    )
    return Stream(response)
