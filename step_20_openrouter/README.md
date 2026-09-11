# Step 20 - The same harness on OpenRouter

**What this step adds:** the stage 15 harness, unchanged in its loop, with
OpenRouter as the model gateway. One key and one base URL reach hundreds of
models. A new module, `openrouter.py`, owns the route: a primary model, an
ordered list of fallbacks, optional provider preferences, and a request for
per-call cost. Two commands, `/models` and `/route`, let you inspect and
change the route while the chat is running.

## What OpenRouter is

OpenRouter is a gateway. It exposes one endpoint, `https://openrouter.ai/api/v1`,
that speaks the OpenAI chat completions API. Behind it sit hundreds of models
from many labs, each served by one or more providers. You send the same JSON
you would send to OpenAI, with a model id like `anthropic/claude-sonnet-4`,
and OpenRouter forwards the request, normalises the reply, and bills one
account.

That is why the harness needs no code change to swap models. Since stage 1
the harness has used the `openai` client against a `BASE_URL`. OpenRouter is
just another base URL. The tool schemas, the tool-call parsing, the message
list, prefix caching: all of it is the OpenAI wire format, and OpenRouter
carries it to whichever model the id names. Changing the model is a string
change.

What OpenRouter adds on top is routing. The OpenAI schema has no field for
"try this model, then that one". OpenRouter reads extra fields in the request
body for that, and the `openai` client lets them through in `extra_body`.
This stage is about those extra fields.

## The code, piece by piece

### 1. The key, the headers, the route

`harness/openrouter.py`:

```python
BASE_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("API_KEY", "")

# Optional app attribution. OpenRouter uses these to list the app on its
# rankings page; the API works without them.
HEADERS = {
    "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "https://github.com/dlmastery/simple-coding-harness"),
    "X-Title": "simple-coding-harness",
}

DEFAULT_MODELS = ["deepseek/deepseek-v4-flash", "openai/gpt-4.1-mini", "anthropic/claude-sonnet-4"]
```

The key comes from `OPENROUTER_API_KEY`. If that is unset, the older
`API_KEY` still works, so a `~/.simple-harness/env` file from stage 9
needs no edit. `config.py` loads that file into the environment before
this module runs.

The two headers are OpenRouter's app attribution. `HTTP-Referer` names the
site the app belongs to and `X-Title` names the app. OpenRouter uses them to
list the app on its public rankings and to break down usage per app in your
dashboard. They are optional. The request works without them.

`DEFAULT_MODELS` is the route when `MODELS` is not set. The first entry is
the primary. The other two are fallbacks, in order.

`harness/openrouter.py`:

```python
def parse_route(text):
    """'a, b,,c' -> ['a', 'b', 'c']; blank or None -> the default route."""
    models = [m.strip() for m in (text or "").split(",") if m.strip()]
    return models or list(DEFAULT_MODELS)
```

```python
# The ordered route. MODELS[0] is the primary; MODELS[1:] are the fallbacks.
MODELS = parse_route(os.environ.get("MODELS"))

# Optional provider preferences, sent as extra_body["provider"].
PROVIDER = parse_provider(os.environ.get("OPENROUTER_PROVIDER_SORT"))
```

`MODELS` in the environment is a comma-separated list. `parse_route` is a
separate function because `/route` calls it too.

### 2. Model routing with fallbacks

`harness/openrouter.py`:

```python
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
```

`models` is the fallback route. OpenRouter tries the first entry. If that
model returns an error, is rate limited, or refuses the request, OpenRouter
retries the same request against the next entry, and so on down the list.
The caller sees one response. The `model` field of that response names the
model that actually answered. Section 6 below shows where the harness
prints it.

The route is worth a moment's thought. The primary should be the model you
want. The fallbacks should be models that handle tool calls well and that you
are happy to pay for, because a fallback runs the same request with the same
tool schemas. A cheap fallback that cannot call tools breaks the loop.

### 3. Provider preferences

`harness/openrouter.py`:

```python
PROVIDER_SORTS = ("price", "throughput", "latency")
```

```python
def parse_provider(sort):
    """OPENROUTER_PROVIDER_SORT=price -> {'sort': 'price'}; unset or unknown -> None."""
    sort = (sort or "").strip().lower()
    return {"sort": sort} if sort in PROVIDER_SORTS else None
```

One model id can be served by several providers at different prices and
speeds. By default OpenRouter balances load across them. The `provider`
object in the request changes that. `{"sort": "price"}` picks the cheapest
provider first, `throughput` the fastest by tokens per second, `latency` the
quickest to first token. Set `OPENROUTER_PROVIDER_SORT` to one of those
three words. Anything else, or nothing, leaves the default. OpenRouter also
accepts an `order` list of provider names and other keys in the same object.
The env var covers the common case. Edit `PROVIDER` for the rest.

### 4. Cost accounting per call

`harness/openrouter.py`:

```python
def cost_of(usage):
    """The dollar cost OpenRouter reports for one call, or None if it did not."""
    cost = getattr(usage, "cost", None)
    if cost is None and isinstance(usage, dict):
        cost = usage.get("cost")
    try:
        return float(cost) if cost is not None else None
    except (TypeError, ValueError):
        return None
```

The `usage: {"include": true}` field in `request_extras` asks OpenRouter to
put the price of the call in `usage.cost`, in dollars. The `openai` client
keeps unknown fields on its response objects, so the attribute is there when
OpenRouter sends it and missing when it does not. `cost_of` treats missing
as `None` rather than zero. A zero would be a claim; `None` is an honest
blank, and the UI prints nothing for it.

### 5. The client and the call

`harness/llm.py`:

```python
from . import config  # noqa: F401 - imported first so ~/.simple-harness/env is loaded
from . import openrouter
from .skills import skills_prompt
from .tools import TOOLS, TOOL_SCHEMAS

client = OpenAI(base_url=openrouter.BASE_URL, api_key=openrouter.API_KEY, default_headers=openrouter.HEADERS)
```

```python
def call_llm(messages, tools=None):
    """tools=None means the full registry; tools=[] means no tools (the compaction agent)."""
    request = {"model": openrouter.primary(), "messages": messages, **openrouter.request_extras()}
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    response = client.chat.completions.create(**request)
```

```python
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
        "cost": openrouter.cost_of(response.usage),
        # OpenRouter sets this to the model that actually answered, so a
        # fallback shows up here rather than passing silently.
        "model": getattr(response, "model", None),
    }
```

The signature is the stage 15 one, `call_llm(messages, tools=None)`, so
`agent.py`, `compact.py` and `subagent.py` are untouched. The request gains
`extra_headers` and `extra_body` from `request_extras()`. The usage dict
gains two keys. `cost` is the dollar figure. `model` is the model that
answered, which is how you notice that a fallback took over.

`openrouter.primary()` is read on every call rather than once at import.
That is what lets `/route` take effect mid-chat.

**Prompt caching.** The `cached_tokens` line has been there since stage 3.
Through OpenRouter it still works, but the number is what the serving
provider reports, and providers differ. OpenAI models cache automatically
and report the cached prefix. Anthropic models cache only where the request
marks a breakpoint, which the plain OpenAI schema does not do, so through
OpenRouter their cached count is usually zero. DeepSeek reports cache hits
on its own field, which OpenRouter maps into `cached_tokens`. Read the
number as "what this provider chose to tell us", not as a property of the
harness. OpenRouter's own docs list the caching rules per provider.

### 6. The usage line

`harness/ui.py`:

```python
    def usage(self, stats):
        """One muted line per call: tokens, then the model that answered, then its cost."""
        for key, value in stats.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._totals[key] = self._totals.get(key, 0) + value  # "model" is a string: not summed
        parts = [f"{value:,} {key.replace('_tokens', '')}" for key, value in stats.items() if key not in ("model", "cost") and value]
        if stats.get("model"):
            parts.append(str(stats["model"]))
        if stats.get("cost") is not None:
            parts.append(f"${stats['cost']:.4f}")
        self.console.print(Padding(Text(" · ".join(parts), style=MUTED), (1, 0, 0, 2)))
```

A line now reads
`1,200 prompt · 30 completion · 1,000 cached · deepseek/deepseek-v4-flash · $0.0004`.
The totals only sum numeric values, so the model name never reaches the
closing table, and the cost total prints as dollars there.

### 7. `/models` and `/route`

`harness/commands.py`:

```python
def models(messages):
    """The route, then the top of the catalogue sorted by prompt price."""
    with ui.working("fetching models"):
        catalogue = openrouter.list_models(llm.client)
    if not catalogue:
        ui.note("could not fetch the model list (no key, or offline); showing the route only")
    priced = [m for m in catalogue if m[2] is not None]
    cheapest = sorted(priced, key=lambda m: (m[2], m[3] or 0))[:CATALOGUE_ROWS]
    ui.models(openrouter.MODELS, cheapest)
    return messages


def route(command, messages):
    """/route a/b,c/d -> a/b is the primary, c/d the fallback. No argument shows the route."""
    argument = command[len("/route"):].strip()
    if not argument:
        ui.models(openrouter.MODELS, [])
        return messages
    openrouter.MODELS = openrouter.parse_route(argument)
    ui.note("route: " + " -> ".join(openrouter.MODELS))
    return messages
```

`/models` prints the route, then calls `GET /models` on the same client and
shows the twenty cheapest models by prompt price, with context length and
prices per million tokens. `list_models` returns an empty list on any
failure, so the command still shows the route when offline.

`/route deepseek/deepseek-v4-flash,openai/gpt-4.1-mini` replaces the route
for the rest of the chat. Nothing else has to know: the next `call_llm`
reads `openrouter.MODELS` and sends the new list. The change is not saved
to the session file. Set `MODELS` in the environment to make it stick.

## Getting a key

1. Sign in at openrouter.ai.
2. Open the Keys page and create a key. It starts with `sk-or-`.
3. Add credit, or pick a route whose models are free-tier.
4. Put the key in the environment, or in `~/.simple-harness/env`.

```bash
OPENROUTER_API_KEY=sk-or-...
MODELS=deepseek/deepseek-v4-flash,openai/gpt-4.1-mini,anthropic/claude-sonnet-4
OPENROUTER_PROVIDER_SORT=price
```

| Variable | Meaning | Default |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | the key; `API_KEY` is read if this is unset | none |
| `MODELS` | comma-separated route, primary first | the three defaults above |
| `OPENROUTER_PROVIDER_SORT` | `price`, `throughput` or `latency` | unset: OpenRouter's load balancing |
| `OPENROUTER_REFERER` | the URL sent in the `HTTP-Referer` attribution header | a placeholder project URL |

## Run it

```bash
pip install -e .
export OPENROUTER_API_KEY=sk-or-...
harness
> /models
> /route openai/gpt-4.1-mini,deepseek/deepseek-v4-flash
> list the python files here and count their lines
```

Every usage line ends with the model that answered and the cost of the
call. If the primary is rate limited, the model name on that line changes
to the fallback and the chat carries on. The closing table adds a `cost`
row with the session total.

Offline tests: `python -m pytest test_step.py`. They drive `call_llm` with
a fake client, check the shape of `extra_body`, and run the agent loop
once with a fake model.

## Diff from stage 15

```bash
diff -r ../step_15_subagents/harness harness
```

New: `openrouter.py`. Changed: `llm.py` (client, `extra_body`, `cost` and
`model` in usage), `ui.py` (`usage` line, `models` table), `commands.py`
(`/models`, `/route`). Everything else, including `agent.py`,
`subagent.py` and `compact.py`, is byte-for-byte stage 15. `config.py` is
also unchanged; its `BASE_URL` and `MODEL` are no longer read, since
`openrouter.py` owns both now.
