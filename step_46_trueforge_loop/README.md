# Step 46 - The loop on TrueForge

**What this step adds:** the stage 2.4 agent loop, run by a server instead
of by this process. TrueForge is an open-source agent harness that runs as
a service: the loop, the sessions, the tools, the sandbox, the skills, the
subagents, the compaction and the approvals all live in the server. A
client opens a session, sends one message, and reads the turn back as a
stream of events. This step is that client, in one short module: a
`chat()` function that streams one turn, a REPL with `--resume` and `-p`,
and a setup script that registers the model provider. It is the first of
six steps that map every capability the codelab built by hand onto the
server, one step per capability.

## Quick demo

```bash
python demo.py -p "Remember this: the project codename is HERON. Reply in one short sentence."
python demo.py --resume 01m2g5hdbnwxcf89jxt68tqscy -p "What is the project codename? One short sentence."
```

```text
Got it, the project codename is HERON.
[1,059 input, 13 output, 1,072 total | session 01m2g5hdbnwxcf89jxt68tqscy]
The project codename is HERON.
[1,089 input, 10 output, 1,099 total | session 01m2g5hdbnwxcf89jxt68tqscy]
```

Two processes, one conversation. The second command sends only the new
question. The server chained the turn onto the first one, so the model
already knew the codename. The bracketed line is the usage line from the
turn's `metrics`; the reply itself arrived as deltas on stdout, and the
usage line goes to stderr so `-p` output stays pipeable.

## Files

```text
step_46_trueforge_loop/
├── client/          a thin client for one agent loop on a TrueForge server
│   ├── __init__.py  package marker
│   └── loop.py      chat(): one session, one streamed turn, deltas as they arrive
├── demo.py          a chat REPL on TrueForge, with --resume and -p headless mode
├── setup_server.py  registers the OpenAI provider and one model on the server
├── test_step.py     offline tests: the real SDK against a fake server in a thread
└── README.md        this file
```

## Setup

TrueForge runs as one process. `npx @truefoundry/trueforge@latest` starts
it on `http://localhost:8790` with a SQLite database and no login. Open
that URL for the chat UI and the Settings pages. This codelab talks to the
same server from Python:

```bash
pip install trueforge_sdk truststore
python setup_server.py        # registers openai/gpt-4-1-mini from ~/.simple-harness/env
python demo.py
```

`setup_server.py` reads `OPENAI_API_KEY` from the stage 9 key file (or the
environment), PUTs one model provider, and prints the model list. It never
prints the key; the server redacts it in every response anyway.

**Windows note.** TrueForge standalone (0.1.4) crashes on Windows, and its
local sandbox needs Linux or macOS with `bwrap`, `socat` and `rg` on
`PATH`. On a Windows machine, run the server inside WSL Ubuntu. Set
`networkingMode=mirrored` in `%USERPROFILE%\.wslconfig` so `localhost` is
shared both ways; then the Python client on Windows reaches
`http://localhost:8790` without any port forwarding. Later Part 7 steps
link back to this note.

**HTTPS note.** Python's `ssl` module does not read the system trust
store. Behind a corporate proxy, an HTTPS call to a hosted TrueForge fails
with a certificate error. `truststore.inject_into_ssl()` fixes that, and
`client/loop.py` calls it before the SDK creates any HTTP client. The
import is guarded, so the module works without the package for plain
`http://localhost`.

## One turn, five events

Stage 2.4's loop is a `while True` in `agent.py`: call the model, append
the reply, run the tool calls, append the results, repeat until a reply
has no tool calls. On TrueForge the same loop runs in the server and the
client sees it as events. A plain turn with no tool calls streams exactly
five:

| # | Event                 | What it is                                                | Stage 2.4 equivalent                   |
|---|-----------------------|-----------------------------------------------------------|----------------------------------------|
| 1 | `turn.created`        | the turn has a `turn_id`; the input is echoed back        | `messages.append({"role": "user", ...})` |
| 2 | `model.message`       | an empty assistant message with an `id`; deltas fill it   | `call_llm(messages)` begins            |
| 3 | `model.message.delta` | a text fragment; all deltas share the base message's `id` | a chunk of `message.content`           |
| 4 | `model.message.delta` | the last delta carries `finish_reason` and `usage`        | `usage` from the completion            |
| 5 | `turn.done`           | `state.status`, the final `output`, the turn's `metrics`  | `break` when there are no tool calls   |

A turn that calls tools streams more: a `model.message` whose `tool_calls`
are filled in by deltas, then one `tool.response` per call, then another
`model.message`. That is the inner `for tool_call in message.tool_calls`
loop, executed by the server. Step 47 builds the tools; this step only
needs the five.

## The code, piece by piece

### 1. The client, built on first use

`client/loop.py`:

```python
try:
    import truststore

    truststore.inject_into_ssl()  # the system trust store, so HTTPS works behind a corporate proxy
except ImportError:
    pass

from trueforge_sdk import AgentSpec, Model, SessionAgentSpecBody, TrueForge, UserMessage

BASE_URL = os.environ.get("TRUEFORGE_BASE_URL", "http://localhost:8790")
MODEL = os.environ.get("TRUEFORGE_MODEL", "openai/gpt-4-1-mini")
INSTRUCTIONS = "You are a concise coding assistant. Answer in plain text, in a few sentences."
TIMEOUT = 600  # seconds; a turn holds one HTTP connection open for as long as it runs
```

```python
def client():
    """The SDK client, created on first use so tests can point BASE_URL at a fake server."""
    global _client
    if _client is None:
        _client = TrueForge(base_url=BASE_URL, timeout=TIMEOUT)
    return _client
```

The SDK client takes the server's base URL with no `/api` suffix; the SDK
adds `api/v1/...` itself. The default timeout is 60 seconds, which is too
short for a turn that runs tools, so the client is built with 600. The
model name is the server's fully qualified name, `provider/model`, which
is why `setup_server.py` names the model `gpt-4-1-mini` under the `openai`
provider. Nothing here reads an API key. The key lives in the server.

### 2. A session with an inline agent

`client/loop.py`:

```python
def open_session():
    """Create a session bound to an inline agent spec and return its id."""
    spec = AgentSpec(model=Model(name=MODEL), instructions=INSTRUCTIONS)
    session = client().sessions.create(agent=SessionAgentSpecBody(spec=spec))
    return session.data.id
```

An agent on TrueForge is a spec: a model, instructions, and optionally MCP
servers, skills and a runtime config. A spec can be saved under a name in
the registry or passed inline when the session is created. Inline is the
stage 2.4 shape, where `SYSTEM_PROMPT` is a constant in `llm.py`: the
system prompt travels with the session and nothing has to be registered
first. The session id is the handle for everything that follows. Note the
SDK type: `SessionAgentSpecBody(spec=...)`. Server 0.1.4 rejects the
`{"type": "inline"}` shape that some docs pages show.

### 3. One streamed turn

`client/loop.py`:

```python
def chat(prompt, session_id=None, on_delta=print_delta):
    """Run one turn. Return (session_id, text, metrics).

    A new session is opened when `session_id` is None. Passing an id back
    continues that conversation: the server chains the new turn onto the last
    one (`previous_turn_id` defaults to "auto"), so no history is resent.
    """
    if session_id is None:
        session_id = open_session()
    stream = client().sessions.create_turn_stream(session_id=session_id, input=[UserMessage(content=prompt)])
    pieces = []
    text = None
    metrics = {}
    for event in stream.with_metadata():
        data = event.data
        if data.type == "model.message.delta" and data.thread_id == "main" and data.content:
            pieces.append(data.content)
            if on_delta:
                on_delta(data.content)
        elif data.type == "turn.done":
            text, metrics = finish(data.state)
    if text is None:
        text = "".join(pieces)
    return session_id, text, metrics
```

This is the whole loop from the client's side. `create_turn_stream` sends
one `user.message` and returns a stream; the HTTP request goes out when
the first event is read. `with_metadata()` wraps each event with its
sequence number, which later steps use to resume a dropped stream. The
loop looks at two event types. A `model.message.delta` on the `main`
thread is a piece of the reply, so it is appended and handed to
`on_delta`, which prints it. `turn.done` is the end; `finish` reads the
final text and the metrics out of its state. Events from subagent threads
carry another `thread_id` and are skipped here.

There is no `while True`, no `messages` list and no tool dispatch. The
server holds the transcript. The client sends the new message and reads
the events. That is the trade Part 7 is about.

### 4. The terminal state

`client/loop.py`:

```python
def finish(state):
    """Read the final text and the metrics out of a turn.done state.

    `done` carries the final model.message in `output` (None when the turn
    paused for an approval) and the whole turn's token totals in `metrics`.
    `cancelled` and `error` carry a reason or a message instead.
    """
    if state.status != "done":
        detail = getattr(state, "reason", None) or getattr(state, "message", None) or ""
        return f"[turn {state.status}: {detail}]", {}
    output = state.output
    text = output.content if output is not None and isinstance(output.content, str) else None
    metrics = state.metrics.dict(exclude_none=True) if state.metrics is not None else {}
    return text, metrics
```

`turn.done` has three shapes. `done` carries `output`, the merged final
`model.message`, and `metrics`, the token totals for the whole turn across
every model call it made. `cancelled` carries a `reason` such as
`client-cancelled` or `cancelled-for-next-turn`. `error` carries a
`message`. `finish` returns the output's text when there is one and
`None` otherwise, and `chat` falls back to the joined deltas. The
fallback matters for a turn that paused for an approval: `output` is
`None` then, but the deltas already printed are still the text the user
saw.

### 5. The usage line

`client/loop.py`:

```python
METRIC_LABELS = {
    "total_input_tokens": "input",
    "total_output_tokens": "output",
    "total_cache_read_tokens": "cached",
    "total_reasoning_tokens": "reasoning",
    "total_tokens": "total",
}


def usage_line(metrics):
    """'1,034 input, 7 output, 1,041 total' from a turn's metrics; '' when the turn had none."""
    parts = [f"{metrics[key]:,} {label}" for key, label in METRIC_LABELS.items() if metrics.get(key)]
    cost = metrics.get("total_cost_in_usd")
    if cost is not None:
        parts.append(f"${cost:.4f}")
    return ", ".join(parts)
```

Stage 3 printed one usage line per model call. A turn can make several
calls, one per tool round, and `metrics` sums them: `total_input_tokens`,
`total_output_tokens`, `total_tokens`, plus cache and reasoning counters
when the provider reports them. Zero counters are left out so the line
stays short. `total_cost_in_usd` appears when the server can price the
model; the local server does not, so the demo shows tokens only.

### 6. The REPL and the headless mode

`demo.py`:

```python
def headless(prompt, session_id):
    """Stream one reply to stdout; the usage line goes to stderr so stdout stays pipeable."""
    session_id, _, metrics = loop.chat(prompt, session_id)
    print(flush=True)
    print(f"[{loop.usage_line(metrics)} | session {session_id}]", file=sys.stderr)
    return 0
```

```python
        session_id, _, metrics = loop.chat(prompt, session_id)
        print()
        print(f"  [{loop.usage_line(metrics)}]")
```

```python
    if session_id:
        print(f"session {session_id}  (python demo.py --resume {session_id})")
```

The REPL is stage 8's session loop with the session file replaced by a
session id. `--resume <id>` skips `open_session` and the first `chat`
call chains onto the server's stored history. `-p "prompt"` is step 21's
headless mode: one turn, the reply on stdout, exit code 0. The REPL prints
the resume command on exit so the id is easy to copy.

### 7. The provider manifest

`setup_server.py`:

```python
def manifest(api_key):
    """The provider manifest the server stores. Well-known types are named by their type."""
    return OpenAiModelProvider(
        auth=ModelProviderAuth(api_key=api_key),
        models=[
            ConfiguredModel(
                model_id=MODEL_ID,
                name=MODEL_NAME,
                properties=ModelProperties(context_length=CONTEXT_LENGTH, max_output_tokens=MAX_OUTPUT_TOKENS),
            )
        ],
    )
```

```python
    client = TrueForge(base_url=BASE_URL, timeout=60)
    client.settings.model_providers.create_or_update(manifest=manifest(key))
```

`create_or_update` is `PUT /api/v1/settings/model-providers`. Well-known
provider types are named by their type, so there is one `openai` provider
and the PUT replaces it in full, models included. That makes the script
idempotent: run it twice and the server holds the same manifest. The
`model_id` is what the server sends to OpenAI; the `name` is what agents
use. Resource names match `^[a-z][a-z0-9-]*[a-z0-9]$`, so a dot is not
allowed, hence `gpt-4-1-mini`. `context_length` and `max_output_tokens`
are the model's capability metadata; the server's context management
reads them.

## Run it

```bash
pip install trueforge_sdk truststore
python setup_server.py
python demo.py
> what does a coding agent's loop do, in two sentences?
> /exit
python demo.py --resume <the id printed on exit>
python demo.py -p "one line: what is a turn?"
```

`setup_server.py` prints `openai/gpt-4-1-mini  ->  gpt-4.1-mini  (context
1,047,576)`. The REPL prints the reply as it streams, then a bracketed
usage line, and on `/exit` the resume command. `-p` prints the reply and
exits; its usage line is on stderr.

Offline tests: `python -m pytest test_step.py`. They start a fake TrueForge
server on a free port in a thread, point the real SDK at it, and stream
the five events by hand. Nothing in the tests touches port 8790.

## What to notice

- **The loop moved.** Stage 2.4 owned the transcript and the tool
  dispatch. Here the server owns both; the client is an event reader.
  `chat` has no `messages` list and no `while True`.
- **The transcript stays on the server.** `--resume` sends the new
  message only. Stage 8 loaded the JSONL file and sent the whole
  transcript on every model call.
- **One turn is many model calls.** `metrics` on `turn.done` sums them.
  The last `model.message.delta` of each call carries that call's own
  `usage`, with a breakdown of the input into harness, skills,
  instructions, tool definitions and messages.
- **Deltas share an id.** Every `model.message.delta` carries the `id` of
  the empty `model.message` that came before it. That is how a client with
  several threads knows which message a fragment belongs to.
- **The SDK is generated.** Method names follow the OpenAPI operations:
  `sessions.create`, `sessions.create_turn_stream`,
  `settings.model_providers.create_or_update`. `openapi.json` is the
  reference when a docs page and the server disagree.

## Capability table

| Capability        | This codelab                                                        | TrueForge                                                                 |
|-------------------|---------------------------------------------------------------------|---------------------------------------------------------------------------|
| the agent loop    | stage 2.4, `while True` around `call_llm` in `agent.py`             | the server runs the loop; the client streams `turn` events                |
| system prompt     | stage 1, `SYSTEM_PROMPT` in `llm.py`                                | `instructions` in an inline or saved `AgentSpec`                          |
| streaming         | step 21, `stream=True` and `on_delta` in `llm.py`                   | `model.message.delta` events on `create_turn_stream`                      |
| usage line        | stage 3, one line per call from `response.usage`                    | `turn.done` `state.metrics`, summed over the turn                         |
| sessions, resume  | stage 8, JSONL under `~/.simple-harness/sessions`, `--resume`       | server-side sessions; pass the session id back, `previous_turn_id=auto`   |
| headless mode     | step 21, `-p` runs one turn and prints the text                     | the same `-p` in `demo.py` over one streamed turn                         |
| model config      | stage 9, `MODEL` and `API_KEY` in `~/.simple-harness/env`           | `PUT /api/v1/settings/model-providers`; the key stays in the server       |

## Diff from step 45

None. Part 7 steps are standalone: no `harness/` is copied in, and nothing
from steps 1 to 45 is imported. The files are `client/loop.py`,
`setup_server.py`, `demo.py` and `test_step.py`.
