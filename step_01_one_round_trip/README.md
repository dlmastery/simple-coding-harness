# Step 1 - One round trip

**New in this step:** everything. A system prompt, one user message, one reply.

```
you ──▶ [system + user] ──▶ model ──▶ reply ──▶ printed
```

That is the whole program. No tools, no loop, no memory. It is worth staring
at because every later step is this file plus one more idea.

## Run it

```bash
export BASE_URL=https://api.openai.com/v1     # any OpenAI-compatible endpoint
export API_KEY=sk-...
export MODEL=gpt-4.1-mini                     # optional
python agent.py
```

## What to notice

- The model only sees what is in the `messages` list. There is no hidden
  state. If it is not in the list, the model does not know it.
- The system prompt is just the first message. It is text, nothing magical.
- The reply is `response.choices[0].message`. Later steps will look at
  `message.tool_calls` on that same object. For now it is only `.content`.

## What it cannot do yet

Ask it "what files are in this directory?" and it will guess or apologise.
It has no way to look. Step 2 gives it one.

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `agent.py` | ~35 | the whole program |
