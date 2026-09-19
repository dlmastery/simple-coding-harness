# Stage 2.4 - The agent loop

This is the first stage that is an agent. An agent is a loop around a
model call. Whatever a tool call returns is appended to the message list
and passed back to the same model.

**What this stage adds:** the harness loop. Tool results go back to the
model and the model is called again, until a reply has no tool calls.
This is the step where the program becomes an agent. Every later stage
modifies this loop.

```text
              ┌───────────────────────────────────────────────┐
              │                                               │
messages ──▶ call_llm ──▶ tool calls? ──yes──▶ run each tool, append results
                              │
                              no
                              ▼
                        the answer
```

## Why a loop

Stage 2.3 read a file into *your* terminal. The model never saw it, so
it could not answer "explain this file". The fix is not a bigger prompt;
it is feeding the tool result back as a message and calling the model
again. One question can then take as many tool calls as it needs, and
the model decides when it has seen enough. Without the loop every task
that needs two facts from the machine is impossible.

## The code, piece by piece

### 1. `llm.py` becomes a function

`llm.py`:

```python
def call_llm(messages):
    """One model call. Takes the whole transcript, returns (message, usage)."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )

    if not response.choices:  # some providers answer an error as an empty reply
        raise RuntimeError(getattr(response, "error", None) or "empty reply")
    message = response.choices[0].message
```

The chat completion request moves into a function. `call_llm` is invoked
from `agent.py`, which passes in the messages list. It returns the message
*and* the usage, so the loop can show both. An empty `choices` list, which
some providers send instead of an HTTP error, is raised as a
`RuntimeError` so the loop treats it like any failed call. The system
prompt in `llm.py` also gains the working directory:

```python
Your current working directory is: {os.getcwd()}
```

### 2. What goes back into the transcript

`llm.py`:

```python
def entry(message):
    """The reply as a transcript entry: role, content and the tool calls, nothing else.
    Provider extras such as reasoning or annotations are not echoed back."""
    e = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        e["tool_calls"] = [c.model_dump(exclude_none=True) for c in message.tool_calls]
    return e
```

The reply object carries more than the three fields the API needs back.
OpenAI adds `annotations`, OpenRouter and DeepSeek add `reasoning`,
`reasoning_content` and `reasoning_details`. Dumping the whole object
into the transcript would re-send the model's reasoning on every later
call (it grows the prompt for nothing) and some providers reject their
own reasoning fields as input. `entry` keeps exactly `role`, `content`
and `tool_calls`. The tool calls must be kept: the API rejects a `tool`
message that does not follow the assistant message which requested it.

### 3. `agent.py`: the loop

`agent.py`:

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input},
]

for _ in range(MAX_CALLS):
    # 1. the model sees the whole transcript so far
    try:
        message, usage = call_llm(messages)
    except (openai.APIError, RuntimeError) as e:
        sys.exit(f"model call failed: {e}")
    # 2. its reply joins the transcript - tool calls included, because every
    #    "tool" message must follow the assistant message that asked for it
    messages.append(entry(message))
    print(usage)

    if message.content:
        print("\nAgent: ", message.content, "\n")

    # 3. no tool calls means it has answered; the loop is done
    if not message.tool_calls:
        break

    # 4. otherwise run each call and feed the result back, tied to the call by id.
    #    run_tool never raises, so every call gets its tool message, error or not
    for tool_call in message.tool_calls:
        args, result = run_tool(tool_call)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
else:
    print(f"stopped after {MAX_CALLS} model calls; the model kept calling tools")
```

Step by step:

1. The transcript starts with the system prompt and the user input. Each
   pass first calls `call_llm` with the whole transcript.
2. The output is `message`, the model's reply. Its `entry` is appended to
   the transcript at once, and the usage line is printed for every call,
   including the last one.
3. A reply with no tool calls is the answer. `break`.
4. If tool calls are present, the loop runs each one through `run_tool`
   from stage 2.2. The result is appended to the transcript with the role
   `tool`, not `assistant`. The `tool_call_id` ties each result to the
   call that asked for it, which matters when one reply contains several
   calls.

Two things bound the loop. `MAX_CALLS = 40` caps the number of model
calls per question: a model that retries a failing command forever would
otherwise run, and bill, forever. The `for ... else` prints a note when
the cap is hit. And `run_tool` never raises, so the invariant the API
enforces - every `tool_calls` entry is followed by exactly one `tool`
message with its id - holds even when a tool fails. If a tool could
raise here, the assistant message would already be in the transcript
with no result behind it, and the next request would be refused with a
400.

## Run it

bash:

```bash
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python agent.py
```

PowerShell:

```powershell
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python agent.py
```

Expected output:

```text
Enter your prompt> explain what happens in llm.py and agent.py
{'prompt_tokens': 260, 'completion_tokens': 18, 'reasoning_tokens': None, 'cached_tokens': 0}
Tool:  read_file {'path': 'llm.py'}
"""Stage 2.4 - llm.py becomes a function.
...

{'prompt_tokens': 1180, 'completion_tokens': 17, 'reasoning_tokens': None, 'cached_tokens': 256}
Tool:  read_file {'path': 'agent.py'}
"""Stage 2.4 - the agent loop.
...

{'prompt_tokens': 1900, 'completion_tokens': 240, 'reasoning_tokens': None, 'cached_tokens': 1152}

Agent:  llm.py builds one request from the transcript ...
```

A typical run makes three or four model calls for one question. The
first tool call reads `llm.py`, the second `agent.py`, and once the
results are back in the transcript the model writes the explanation.
That is the loop working.

## Prefix caching

Every call re-sends the whole `messages` list, and the prefix grows on
every call. Providers cache the tokens they have already processed. When
new messages are appended to an existing transcript, the cached prefix
costs much less than fresh input. Most of the cost goes to processing the
new input tokens and generating the new output tokens.

The rule that shapes the rest of the build: **never break the prefix.** A
change to a single word near the start of the prompt invalidates the whole
cache, and the entire input is paid for again. Stages 6, 10 and 14 are
each designed around this rule. Watch `cached_tokens` in the usage line
to see it hold: in the transcript above it climbs on every call.

## Error handling

- A bad tool call (broken JSON, unknown name, a tool that raises) becomes
  an `Error: ...` tool message and the model gets another turn. The loop
  never dies over a tool.
- A dead model call (`openai.APIError`, or an empty reply): `model call
  failed: ...`, exit code 1. There is nothing to keep in a one-question
  script; stage 3 keeps the transcript alive instead.
- More than 40 model calls for one question: the loop stops with a note.
- No prompt on stdin, or ctrl-c at the prompt: `no prompt given`.
  ctrl-c during a call ends the program.
- Leaving: the program ends after the answer.

## Gotchas

- One question per run. Stage 3 wraps this loop in a chat.
- The whole result of every tool goes into the transcript; a 5 MB `cat`
  is a 5 MB prompt from then on. Stage 14 trims.
- Tool calls in one reply run one after another, in the order the model
  wrote them. Stage 22 runs them in parallel.

## Files

```text
step_02_4_agent_loop/
├── agent.py         the harness loop: call, append, run tools, repeat; capped at MAX_CALLS
├── llm.py           call_llm(messages) and entry(message): the request becomes a function
├── tools.py         tools, unchanged from 2.3
├── test_step.py     offline tests: a scripted model drives the loop; bad calls; the cap; EOF
└── README.md        this file
```

## Test

The offline tests script model replies and check that the second request
carried the first tool result under the right `tool_call_id` and only
`role`/`content`/`tool_calls` in the assistant entry; that a reply with a
malformed call, an unknown tool and a raising tool yields one `tool`
message each and the loop continues; that the loop stops after
`MAX_CALLS`; and that an empty stdin exits cleanly.

## Diff from stage 2.3

```bash
diff ../step_02_3_read_file/llm.py llm.py     # the request becomes call_llm()
cat agent.py                                   # new: the loop
```

## What the next step adds

Stage 3 puts an outer loop around this one, so the transcript survives
between questions, and draws everything with `rich`.
