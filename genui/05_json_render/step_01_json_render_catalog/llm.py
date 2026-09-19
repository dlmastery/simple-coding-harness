"""The model call. One OpenAI-compatible client, configured from the environment
or from ~/.simple-harness/env (KEY=VALUE lines; read, never printed).

complete_spec() asks for the whole spec as one JSON object. The tests replace
the client with a fake that returns scripted output.
"""

import json
import os
import time
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
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120)  # a hung upstream fails the request, it does not hang the page
    return _client


def complete_spec(system_prompt, user_prompt):
    """One non-streaming call. Returns (spec, usage, seconds).

    JSON mode makes the API return one JSON object, which is the complete
    spec the catalog prompt asks for.
    """
    started = time.perf_counter()
    response = client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    elapsed = time.perf_counter() - started
    if not response.choices:
        raise ValueError(f"empty reply: {getattr(response, 'error', None)}")
    content = response.choices[0].message.content
    try:
        spec = json.loads(content or "")
    except ValueError as error:  # a refusal (content None) or text that is not JSON despite JSON mode
        raise ValueError(f"the model reply is not JSON: {error}") from None
    usage = {  # some proxies send no usage
        "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
        "completion_tokens": getattr(response.usage, "completion_tokens", None),
    }
    return spec, usage, elapsed
