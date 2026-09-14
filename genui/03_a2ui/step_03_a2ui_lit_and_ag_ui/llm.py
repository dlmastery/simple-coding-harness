"""Model access, the harness convention: API_KEY, BASE_URL and MODEL from the
environment, with ~/.simple-harness/env (KEY=VALUE lines) filling the gaps.
The file is read, never printed."""

import os
from pathlib import Path

try:
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

BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4.1-mini")

last_usage = None  # prompt/completion tokens of the most recent stream, when the API reports them


def stream(messages, temperature=0):
    """One streamed chat completion. Yields text deltas as they arrive."""
    global last_usage
    from openai import OpenAI

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=temperature,
        stream=True, stream_options={"include_usage": True},
    )
    last_usage = None
    for chunk in response:
        if getattr(chunk, "usage", None) is not None:
            last_usage = {"prompt_tokens": chunk.usage.prompt_tokens, "completion_tokens": chunk.usage.completion_tokens}
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
