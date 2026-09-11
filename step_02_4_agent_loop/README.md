# Stage 2.4 - The agent loop (video 12:07 - 16:50)

> "So here for the first time, we are talking about agents now because an
> agent is something that loops around an LLM call."

Two changes:

- `llm.py`: the request moves into `call_llm(messages)`, which returns
  `(message, usage)`. The system prompt now also states the working
  directory.
- `agent.py`, new: **the harness loop.**

```python
while True:
    message, usage = call_llm(messages)
    messages.append(message.model_dump(exclude_none=True))
    if not message.tool_calls:
        break
    for tool_call in message.tool_calls:
        result = TOOLS[tool_call.function.name](**json.loads(tool_call.function.arguments))
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

That is the whole agent. Everything from here to stage 15 is this loop with
more things happening inside it.

## Read the loop with the video

1. `call_llm(messages)` - the model sees the entire transcript, every time.
2. `messages.append(message.model_dump(...))` - the reply, *including its
   tool calls*, joins the transcript. A `tool` message is only valid after
   the assistant message that requested it.
3. No tool calls: the model answered, break.
4. Otherwise run each tool and append its result with `role: "tool"` and
   the matching `tool_call_id`. "Notice the role here is tool. It's not an
   assistant message. It is a tool call output."

Run it with *explain what happens in llm.py and agent.py*: it reads
`llm.py`, then `agent.py`, then `tools.py`, then explains all three. Four
model calls for one question.

## Prefix caching (video 15:01)

Every call re-sends the whole transcript, and "the prefix always grows".
Providers cache the part they have already processed, so the bulk of the
cost is the *new* tokens: the tool output and the reply. The video's rule
for the rest of the build: **never break the prefix.** "Even if you just
change a single word or two at the beginning of the prompt, the entire
cache breaks and you pay for the entire input at one go." Watch
`cached_tokens` in the usage line to see it working.

## Diff from stage 2.3

```bash
diff ../step_02_3_read_file/llm.py llm.py     # the request becomes call_llm()
cat agent.py                                   # new
```
