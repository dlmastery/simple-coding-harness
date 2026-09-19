# Step 20 - The same harness on OpenRouter

**What this step adds:** one gateway in front of hundreds of models, with a
route instead of a model name. The stage 15 harness keeps its loop; a new
module, `openrouter.py`, owns the route: a primary model, an ordered list of
fallbacks, optional provider preferences, and a request for per-call cost.
Two commands, `/models` and `/route`, let you inspect and change the route
while the chat is running.

## Why

A coding agent that depends on one model is down when that model is down.
Rate limits, a provider outage, a model retired overnight: each one stops
the chat mid-task. And every model has its own SDK, its own key and its own
usage format, so trying another one means code.

Without this step, the fix for "the model is rate limited" is: quit, edit
the environment, restart, lose the context. With it, OpenRouter retries the
same request against the next model on the route and the usage line shows
which model actually answered. The chat carries on.

## Files

```text
step_20_openrouter/
├── harness/
│   ├── llm.py         the client points at OpenRouter; sends the route, reads the cost
│   ├── openrouter.py  the route: primary model, fallbacks, provider preferences
│   ├── tools.py       the registry; execute() is the one permission-checked entry point
│   ├── agent.py       the loop, unchanged in its ideas from stage 15
│   ├── commands.py    /models shows the route and catalogue; /route swaps it in place
│   ├── ui.py          usage() shows which model answered and what the call cost
│   ├── compact.py     the compaction agent from stage 14
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py     the late injection block, unchanged since stage 10
│   ├── history.py     keeps the transcript small: caps, strips and drops tool output
│   ├── permissions.py allow / ask / deny rules; which tool calls need a human
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash, and the process-group timeout
│   ├── session.py     append-only JSONL session log, unchanged since stage 14
│   ├── skills.py      skills, unchanged since stage 9
│   ├── subagent.py    exploration subagents with their own context window
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests against a fake client
├── pyproject.toml     package metadata; version 0.20.0
└── README.md          this file
```

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

`DEFAULT_MODELS` is the route when neither `MODELS` nor `MODEL` is set. The
first entry is the primary. The other two are fallbacks, in order.

`harness/openrouter.py`:

```python
def parse_route(text):
    """'a, b,,c' -> ['a', 'b', 'c']; blank or None -> the default route."""
    models = [m.strip() for m in (text or "").split(",") if m.strip()]
    return models or list(DEFAULT_MODELS)
```

```python
# The ordered route. MODELS[0] is the primary; MODELS[1:] are the fallbacks.
# MODEL (singular) has been the setting since stage 1; a one-model route honours it.
MODELS = parse_route(os.environ.get("MODELS") or os.environ.get("MODEL"))

# Optional provider preferences, sent as extra_body["provider"].
PROVIDER = parse_provider(os.environ.get("OPENROUTER_PROVIDER_SORT"))
```

`MODELS` in the environment is a comma-separated list. A `MODEL` from an
earlier stage still works and becomes a route of one. `parse_route` is a
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
prints it. When every model on the route fails, OpenRouter returns an HTTP
error and the `openai` client raises; the "Error handling" section says
what the loop does with that.

The route is worth a moment's thought. The primary should be the model you
want. The fallbacks should be models that handle tool calls well and that you
are happy to pay for, because a fallback runs the same request with the same
tool schemas. A cheap fallback that cannot call tools breaks the loop. And
the fallbacks see the same transcript, so `CONTEXT_WINDOW` (stage 14) has to
be the *smallest* window on the route, or `fit` and compaction fire too late
for the model that ends up answering.

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
put the price of the call in `usage.cost`, in dollars of credit. The `openai`
client keeps unknown fields on its response objects, so the attribute is
there when OpenRouter sends it and missing when it does not. `cost_of`
treats missing as `None` rather than zero. A zero would be a claim; `None`
is an honest blank, and the UI prints nothing for it. `:free` models and
providers that report no usage at all both come back as `None`.

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

    if not response.choices:  # some providers answer an error as an empty reply
        raise RuntimeError(getattr(response, "error", None) or "empty reply")
    message = response.choices[0].message

    return message, usage_from(response)
```

```python
def usage_from(response):
    """The numbers we keep per call. usage can be missing, and so can its details."""
    u = response.usage
    usage = {
        "prompt_tokens": getattr(u, "prompt_tokens", None),
        "completion_tokens": getattr(u, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
        "cost": openrouter.cost_of(u),
        # OpenRouter sets this to the model that actually answered, so a
        # fallback shows up here rather than passing silently.
        "model": getattr(response, "model", None),
    }
    return usage
```

The signature is the stage 15 one, `call_llm(messages, tools=None)`, so
`agent.py`, `compact.py` and `subagent.py` call it as before. The request
gains `extra_headers` and `extra_body` from `request_extras()`. The usage
dict gains two keys. `cost` is the dollar figure. `model` is the model that
answered, which is how you notice that a fallback took over. Every read of
`usage` goes through `getattr`, because a provider on the route may send no
usage block at all, and an empty `choices` list raises a `RuntimeError`
naming the provider's error instead of an `IndexError` a line later.

`openrouter.primary()` is read on every call rather than once at import.
That is what lets `/route` take effect mid-chat.

One more thing changes because of the route. The transcript entry for a
reply is built by hand:

`harness/llm.py`:

```python
def entry(message):
    """The transcript entry for a reply: role, content, tool calls - and nothing else.

    `message.model_dump()` would also echo reasoning, annotations and other
    provider extras back on the next request, and a fallback provider may
    reject them.
    """
    record = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        record["tool_calls"] = [c.model_dump(exclude_none=True) for c in message.tool_calls]
    return record
```

DeepSeek answers with a `reasoning` field, other providers with
`annotations`. With one model those extras go back and forth harmlessly.
With a route, the next request may land on a provider that rejects fields
it did not produce, so only the three keys the API defines are kept.

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
CONTEXT_WINDOW=128000
```

| Variable | Meaning | Default |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | the key; `API_KEY` is read if this is unset | none |
| `MODELS` | comma-separated route, primary first; `MODEL` is read if this is unset | the three defaults above |
| `OPENROUTER_PROVIDER_SORT` | `price`, `throughput` or `latency` | unset: OpenRouter's load balancing |
| `OPENROUTER_REFERER` | the URL sent in the `HTTP-Referer` attribution header | this repository's URL |
| `CONTEXT_WINDOW` | tokens; set it to the smallest window on the route | 128000 |

## Run it

bash:

```bash
pip install -e .
export OPENROUTER_API_KEY=sk-or-...
harness
```

PowerShell:

```powershell
pip install -e .
$env:OPENROUTER_API_KEY = "sk-or-..."
harness
```

Then, at the prompt:

```text
> /models
> /route openai/gpt-4.1-mini,deepseek/deepseek-v4-flash
> list the python files here and count their lines
```

### Expected output

```text
  primary   openai/gpt-4.1-mini
  fallback  deepseek/deepseek-v4-flash

  ┌─ late injection ─────────────────────────────────┐
  │ <env>                                            │
  │ time: 2026-09-18 10:42                           │
  │ git branch: main                                 │
  │ </env>                                           │
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │ bash find . -name "*.py" | xargs wc -l           │
  ├──────────────────────────────────────────────────┤
  │   92 harness/agent.py                            │
  │  119 harness/openrouter.py                       │
  │  ...                                             │
  └──────────────────────────────────────────────────┘

  1,834 prompt · 41 completion · 1,792 cached · deepseek/deepseek-v4-flash · $0.0006

  agent
  Seventeen Python files, 2,140 lines in total. The biggest are ...
```

The usage line ends with the model that answered and the cost of the
call. Here the primary was rate limited, so the model name on that line is
the fallback and the chat carried on. The closing table adds a `cost` row
with the session total.

Offline tests: `python -m pytest test_step.py`. They drive `call_llm` with
a fake client, check the shape of `extra_body`, run the agent loop once
with a fake model, and cover the error paths below.

## Error handling

Nothing the model or a tool does takes the chat down. The rule since stage
5 is "errors are results": whatever goes wrong inside a tool call comes back
to the model as a string starting with `Error:`, and the transcript stays
valid because every `tool_call` still gets its one tool message.

`harness/tools.py`:

```python
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as failure:  # json.JSONDecodeError is a ValueError
        return {}, f"Error: the arguments of {name} are not a JSON object: {failure}"

    if allowed is not None and name not in allowed:
        action, reason = "deny", f"{name} is not available to this agent"
    elif name not in TOOLS:
        return args, f"Error: no tool named {name!r}."
    else:
        action, reason = check(name, args)
```

```python
    try:
        result = TOOLS[name](**args)
    except Exception as failure:  # noqa: BLE001 - errors are results, never crashes
        return args, f"Error: {type(failure).__name__}: {failure}"
```

- **Bad tool call.** Arguments that are not a JSON object, a tool name that
  does not exist, a missing argument (`TypeError`), a file that is not
  there (`FileNotFoundError`): each becomes an `Error:` result the model
  reads and works around.
- **A failing command.** `bash` returns stdout and stderr whatever the exit
  code. A command that runs past 60 seconds is killed together with every
  process it started (`sandbox.kill_tree`) and the result is
  `Error: command timed out after 60s`.
- **A dead model call.** A rate limit, an exhausted balance, a route where
  every model failed: the `openai` client raises, the loop prints
  `model call failed: ...` and returns to the prompt. Your message is still
  in the transcript; ask again, or `/route` to something else first.
- **ctrl-c during a turn.** Every tool call the model asked for but did not
  get an answer to receives `(interrupted before this tool ran)`, the turn
  ends, and the prompt is back. The transcript is still sendable.
- **A runaway turn.** After 40 model calls in one turn the loop stops with
  `stopped after 40 model calls in one turn; say 'continue' to go on`.
- **A crash between save and tool result.** Opening the session again
  (`--resume`, `/sessions`) fills any unanswered tool call with
  `(the harness stopped before this tool ran; no result was recorded)`.
- **Leaving.** `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at
  the prompt. An empty line does nothing.

## Gotchas / what this is not

- The tool named `bash` runs the command through `cmd.exe` on Windows and
  `/bin/sh` elsewhere. There is no OS sandbox on Windows; the banner says
  `sandbox: none`.
- A fallback is only as good as its tool calling. Put models you have
  tested with tool schemas on the route.
- `usage.cost` is OpenRouter's number, in credits. It is `None` for free
  models and for providers that report no usage; the totals then undercount.
- `cached_tokens` means whatever the answering provider means by it.
- `/route` lives in memory. The session file records the messages, not the
  route that produced them.
- The `models` list is sent on every request, including the compaction
  agent's and the subagent's, so all three share one route.

## Diff from stage 15

```bash
diff -r ../step_15_subagents/harness harness
```

New: `openrouter.py`. Changed: `llm.py` (client, `extra_body`, `usage_from`,
`entry`, `cost` and `model` in usage), `ui.py` (`usage` line, `models`
table), `commands.py` (`/models`, `/route`), `openrouter.py` reads `MODEL`
as well as `MODELS`. Everything else - `agent.py`, `tools.py`, `subagent.py`,
`compact.py`, `history.py`, `session.py` - is stage 15. `config.py` still
defines `BASE_URL` and `MODEL`, but `openrouter.py` owns the base URL now
and turns `MODEL` into a route of one.

## What the next step adds

Step 21 streams the reply token by token and adds a headless `-p` mode, so
the harness can run from a script as well as a keyboard.
