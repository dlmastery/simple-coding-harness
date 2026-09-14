# Stage 1 - Minimal chat

The first stage is a minimal chat application. It asks for a prompt, sends
it to the model, and prints the reply.

**What this stage is:** one file, `llm.py`, one request, one reply. No
tools, no loop, no memory. Every later stage is this file plus one idea at
a time, so it is worth reading slowly.

```text
you type a prompt ──▶ [system message, user message] ──▶ model ──▶ reply text + usage
```

## Files

```text
step_01_minimal_chat/
├── llm.py           one request, one reply: the whole program
├── test_step.py     offline test: the script against a fake OpenAI client
└── README.md        this file
```

## The code, piece by piece

### 1. The client and its credentials

`llm.py`:

```python
client = OpenAI(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["API_KEY"],
)

MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-flash")
```

`BASE_URL` and `API_KEY` come from the environment. The defaults point at
OpenRouter, so the OpenAI client talks to an OpenRouter credential. The
`openai` package speaks the standard chat API that almost every provider
implements. The same three variables therefore work with OpenAI, Gemini,
DeepSeek, Ollama or OpenRouter without a code change. The default model is
`deepseek/deepseek-v4-flash`, one of the fastest and cheapest models
available; `MODEL` overrides it.

### 2. Two messages

`llm.py`:

```python
SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
"""

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
)
```

The request carries two messages. The first has the system role and holds
the system prompt. The second has the user role and holds the user input.
The system prompt is not magic: it is the first message in a list. The
model only ever sees this list. There is no hidden state anywhere.

### 3. Reading the reply and the usage

`llm.py`:

```python
output = response.choices[0].message.content

completion_details = response.usage.completion_tokens_details
prompt_details = response.usage.prompt_tokens_details

usage = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
    "cached_tokens": getattr(prompt_details, "cached_tokens", None),
}

print("\nAgent: ", output, "\n")
print(usage)
```

The reply lives at `response.choices[0].message`. This stage only reads
its `.content`. From stage 2.1 the same object also carries
`.tool_calls`. The usage dictionary is printed from the very first stage
on purpose. `prompt_tokens` is what you pay to send. `completion_tokens`
is what the model wrote. `cached_tokens` is the number to watch from stage
2.4 onward, when the transcript starts to be re-sent on every call.

## Run it

```bash
export BASE_URL=https://openrouter.ai/api/v1     # or any OpenAI-compatible endpoint
export API_KEY=sk-or-...
python llm.py
Enter your prompt> hi
```

You get one reply and a line like
`{'prompt_tokens': 24, 'completion_tokens': 9, 'reasoning_tokens': None, 'cached_tokens': 0}`.

This is the most basic step. It is also one of the most important, because
every later stage builds on this one request.

## What it cannot do

Ask *what files are in this directory?* and it guesses or apologises. It
has no way to look. Stage 2.1 gives it one.

## Test

`python -m pytest test_step.py` runs the script with a fake client and a
canned prompt and checks the two messages that were sent.
