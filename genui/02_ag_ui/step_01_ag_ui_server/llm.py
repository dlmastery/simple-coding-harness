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


def stream_text(messages):
    """One streamed chat completion. Yields each text delta as it arrives."""
    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
