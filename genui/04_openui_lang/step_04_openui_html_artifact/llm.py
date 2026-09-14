"""Step 04 - the model call. Same convention as the harness codelab.

Environment variables API_KEY, BASE_URL (default https://api.openai.com/v1)
and MODEL (default gpt-4.1-mini) come from the environment or from
~/.simple-harness/env, a KEY=VALUE file that is read and never printed.
OPENAI_API_KEY in that file also fills API_KEY.

This step also asks the API for its token usage (`stream_options`), so the
demo can say how much of the completion the artifact document took.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

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

try:  # this machine needs the OS certificate store for live calls
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass


def stream_completion(messages: list[dict], usage: dict | None = None) -> Iterator[str]:
    """Yield the text deltas of one streamed chat completion.

    When `usage` is a dict, the API's prompt_tokens and completion_tokens are
    written into it after the last chunk (the stream's final chunk carries
    them when stream_options asks for it).
    """
    from openai import OpenAI

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    stream = client.chat.completions.create(
        model=MODEL, messages=messages, stream=True, temperature=0,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if usage is not None and getattr(chunk, "usage", None):
            usage["prompt_tokens"] = chunk.usage.prompt_tokens
            usage["completion_tokens"] = chunk.usage.completion_tokens
