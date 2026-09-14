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

## Files

```text
step_02_4_agent_loop/
├── agent.py         the harness loop: call, append, run tools, repeat
├── llm.py           call_llm(messages): the request becomes a function
├── tools.py         tools, unchanged from 2.3
├── test_step.py     offline test: a scripted model drives the loop
└── README.md        this file
```

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

    message = response.choices[0].message
```

The chat completion request moves into a function. `call_llm` is invoked
from `agent.py`, which passes in the messages list. It returns the message
*and* the usage, so the loop can show both. The system prompt in `llm.py`
also gains the working directory:

```python
Your current working directory is: {os.getcwd()}
```

### 2. `agent.py`: the loop

`agent.py`:

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input},
]

while True:
    # 1. the model sees the whole transcript so far
    message, usage = call_llm(messages)
    # 2. its reply joins the transcript - tool calls included, because every
    #    "tool" message must follow the assistant message that asked for it
    messages.append(message.model_dump(exclude_none=True))

    if message.content:
        print("\nAgent: ", message.content, "\n")

    # 3. no tool calls means it has answered; the loop is done
    if not message.tool_calls:
        break

    # 4. otherwise run each call and feed the result back, tied to the call by id
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })
```

Step by step:

1. The transcript starts with the system prompt and the user input. The
   `while True` runs until a `break`. Each pass first calls `call_llm`
   with the whole transcript.
2. The output is `message`, the model's reply. The reply is appended to
   the transcript at once. `model_dump` keeps the tool calls inside that
   assistant message. That is not optional: the API rejects a `tool`
   message that does not follow the assistant message which requested it.
3. A reply with no tool calls is the answer. `break`.
4. If tool calls are present, the loop runs each one.
   `tool_call.function.name` is the function name, such as `bash`, and
   `TOOLS` holds the Python function. The arguments the model sent become
   keyword arguments. The result is appended to the transcript with the
   role `tool`, not `assistant`. The `tool_call_id` ties each result to
   the call that asked for it, which matters when one reply contains
   several calls.

## Run it

```bash
python agent.py
Enter your prompt> explain what happens in llm.py and agent.py
```

A typical run makes four model calls for one question. The first tool
call reads `llm.py`. The second reads `agent.py`. The third reads
`tools.py`. After all three results are back in the transcript, the model
writes a full explanation. That is the loop working.

## Prefix caching

Every call re-sends the whole `messages` list, and the prefix grows on
every call. Providers cache the tokens they have already processed. When
new messages are appended to an existing transcript, the cached prefix
costs much less than fresh input. Most of the cost goes to processing the
new input tokens and generating the new output tokens.

The rule that shapes the rest of the build: **never break the prefix.** A
change to a single word near the start of the prompt invalidates the whole
cache, and the entire input is paid for again. Stages 6, 10 and 14 are
each designed around this rule. Watch `cached_tokens` in the usage line to
see it hold.

## Diff from stage 2.3

```bash
diff ../step_02_3_read_file/llm.py llm.py     # the request becomes call_llm()
cat agent.py                                   # new: the loop
```

## Test

The offline test scripts three model replies (two tool calls, then text)
and checks that the second request carried the first tool result under the
right `tool_call_id`, and the third request the full six-message
transcript.
