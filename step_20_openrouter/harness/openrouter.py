"""Stage 20 - OpenRouter as the model gateway: one key, one base URL, hundreds of models.

Nothing in the agent loop changes. OpenRouter speaks the OpenAI chat
completions API, so the harness talks to it through the same client it has
used since stage 1. What this module adds is the routing that OpenRouter
layers on top of that API:

- a fallback route (`MODELS`): the primary model first, the rest tried in
  order if the primary fails or is rate limited;
- provider preferences (`PROVIDER`): sort the providers behind a model by
  price, throughput or latency;
- per-call cost, returned in `usage.cost` when the request asks for it;
- the optional attribution headers that list the app on openrouter.ai.

Every value here is read from the environment, so the whole route can be
changed without touching code. `config.py` already loads
~/.simple-harness/env into os.environ before this module is imported.
"""

import os

BASE_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("API_KEY", "")

# Optional app attribution. OpenRouter uses these to list the app on its
# rankings page; the API works without them.
HEADERS = {
    "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "https://github.com/dlmastery/simple-coding-harness"),
    "X-Title": "simple-coding-harness",
}

DEFAULT_MODELS = ["deepseek/deepseek-v4-flash", "openai/gpt-4.1-mini", "anthropic/claude-sonnet-4"]

PROVIDER_SORTS = ("price", "throughput", "latency")


def parse_route(text):
    """'a, b,,c' -> ['a', 'b', 'c']; blank or None -> the default route."""
    models = [m.strip() for m in (text or "").split(",") if m.strip()]
    return models or list(DEFAULT_MODELS)


def parse_provider(sort):
    """OPENROUTER_PROVIDER_SORT=price -> {'sort': 'price'}; unset or unknown -> None."""
    sort = (sort or "").strip().lower()
    return {"sort": sort} if sort in PROVIDER_SORTS else None


# The ordered route. MODELS[0] is the primary; MODELS[1:] are the fallbacks.
MODELS = parse_route(os.environ.get("MODELS"))

# Optional provider preferences, sent as extra_body["provider"].
PROVIDER = parse_provider(os.environ.get("OPENROUTER_PROVIDER_SORT"))


def primary():
    """The model named in the request body. OpenRouter may still serve a fallback."""
    return MODELS[0]


def request_extras():
    """The OpenRouter-only parts of a chat request.

    The OpenAI client rejects unknown keyword arguments, so anything beyond
    the OpenAI schema has to travel in `extra_body`, and the attribution
    headers in `extra_headers`.
    """
    body = {
        "models": list(MODELS),        # the fallback route, primary first
        "usage": {"include": True},    # ask for usage.cost in the response
    }
    if PROVIDER:
        body["provider"] = dict(PROVIDER)
    return {"extra_headers": dict(HEADERS), "extra_body": body}


def cost_of(usage):
    """The dollar cost OpenRouter reports for one call, or None if it did not."""
    cost = getattr(usage, "cost", None)
    if cost is None and isinstance(usage, dict):
        cost = usage.get("cost")
    try:
        return float(cost) if cost is not None else None
    except (TypeError, ValueError):
        return None


def list_models(client):
    """[(id, context_length, prompt_price, completion_price), ...] from GET /models.

    Defensive on purpose: the catalogue is large and its shape has changed
    before. A model missing a field is kept with None in that slot.
    """
    try:
        payload = client.get("/models", cast_to=dict)
    except Exception:  # noqa: BLE001 - the caller decides how to report it
        return []
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    models = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        pricing = row.get("pricing") or {}
        models.append((
            row["id"],
            row.get("context_length"),
            _price(pricing.get("prompt")),
            _price(pricing.get("completion")),
        ))
    return models


def _price(value):
    """OpenRouter quotes prices as strings of dollars per token."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
