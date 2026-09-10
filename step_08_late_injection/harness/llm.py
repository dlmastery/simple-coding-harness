"""The one function that talks to the model."""

from openai import OpenAI

from . import config
from .tools import TOOL_SCHEMAS

_client = None


def client():
    """Create the client on first use, so importing the package needs no key."""
    global _client
    if _client is None:
        if not config.API_KEY:
            raise SystemExit(
                "No API key. Set API_KEY (and BASE_URL) in the environment "
                f"or in {config.ENV_FILE}."
            )
        _client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
    return _client


def complete(messages, tools=None):
    """Return (assistant message, usage dict) for one model call."""
    response = client().chat.completions.create(
        model=config.MODEL,
        messages=messages,
        tools=tools or TOOL_SCHEMAS,
    )
    usage = response.usage
    details = getattr(usage, "completion_tokens_details", None)
    cached = getattr(usage, "prompt_tokens_details", None)
    return response.choices[0].message, {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "reasoning_tokens": getattr(details, "reasoning_tokens", None),
        "cached_tokens": getattr(cached, "cached_tokens", None),
    }
