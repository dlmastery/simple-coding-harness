# Stage 1 - Minimal chat

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. This is the first lesson. Next: [Stage 2.1 - Chat with a simple bash tool](../step_02_1_bash_tool/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

The first stage is a minimal chat application. It asks for a prompt, sends
it to the model, and prints the reply.

**What this stage is:** one file, `llm.py`, one request, one reply. No
tools, no loop, no memory. Every later stage is this file plus one idea at
a time, so it is worth reading slowly.

```text
you type a prompt ──▶ [system message, user message] ──▶ model ──▶ reply text + usage
```

## Why start here

Everything an agent does later - running tools, remembering a
conversation, resuming a session - is built on this one request. If you
can read this file you can read every other stage, because the shape of
the request never changes: a list of messages goes in, one message comes
out. Without this stage the codelab would start with a loop and you would
have to take the request on faith.

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

`BASE_URL` and `API_KEY` must be set; there is no default for either, and
an unset one stops the script with `KeyError: 'BASE_URL'`. The `openai`
package speaks the standard chat API that almost every provider
implements, so the same three variables work with OpenAI, Gemini,
DeepSeek, Ollama or OpenRouter without a code change. Only the model has a
default: `deepseek/deepseek-v4-flash`, an OpenRouter model id and one of
the fastest and cheapest models available. `MODEL` overrides it; with a
provider other than OpenRouter you will need to.

### 2. Reading the prompt

`llm.py`:

```python
try:
    user_input = input("Enter your prompt> ")
except (EOFError, KeyboardInterrupt):  # ctrl-d, ctrl-z+enter, ctrl-c, or nothing on stdin
    sys.exit("\nno prompt given")
```

`input()` raises `EOFError` when stdin is empty or closed (piped input,
ctrl-d on Linux and macOS, ctrl-z then enter on Windows) and
`KeyboardInterrupt` on ctrl-c. Both end the script with a one-line
message instead of a traceback.

### 3. Two messages

`llm.py`:

```python
SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
"""

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
    )
except openai.APIError as e:  # wrong key, wrong URL, model down: one line, no traceback
    sys.exit(f"model call failed: {e}")
```

The request carries two messages. The first has the system role and holds
the system prompt. The second has the user role and holds the user input.
The system prompt is not magic: it is the first message in a list. The
model only ever sees this list. There is no hidden state anywhere.

`openai.APIError` is the base class of everything the client raises after
it has reached the network: a bad key (401), an unknown model (404), a
rate limit (429), a provider outage (5xx), a connection error. One
`except` covers them all.

### 4. Reading the reply and the usage

`llm.py`:

```python
if not response.choices:  # some providers answer an error as an empty reply
    sys.exit(f"empty reply: {getattr(response, 'error', None)}")

output = response.choices[0].message.content

# usage can be missing (some proxies), and its detail objects can be None
u = response.usage
usage = {
    "prompt_tokens": getattr(u, "prompt_tokens", None),
    "completion_tokens": getattr(u, "completion_tokens", None),
    "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None),
    "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", None),
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

Every field is read with `getattr(..., None)` because the usage block is
optional in the API: some proxies and local servers omit it, and the
detail objects are `None` on models without reasoning or caching. A
missing number prints as `None`; it never stops the program.

## Run it

bash:

```bash
export BASE_URL=https://openrouter.ai/api/v1     # or any OpenAI-compatible endpoint
export API_KEY=sk-or-...
python llm.py
```

PowerShell:

```powershell
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python llm.py
```

Prerequisite: `pip install openai` (or `pip install -r requirements.txt`
from the repository root).

Expected output:

```text
Enter your prompt> write hello world in python

Agent:  print("hello world")

{'prompt_tokens': 24, 'completion_tokens': 9, 'reasoning_tokens': None, 'cached_tokens': 0}
```

This is the most basic step. It is also one of the most important, because
every later stage builds on this one request.

## Error handling

- No prompt (empty stdin, ctrl-d, ctrl-z+enter, ctrl-c): `no prompt given`, exit code 1.
- A failed model call (wrong key, wrong URL, unknown model, outage):
  `model call failed: ...` with the provider's message, exit code 1.
- An empty reply: `empty reply: ...`.
- Missing usage numbers print as `None`.
- Leaving: the script ends after one reply. There is nothing to quit.

## Gotchas

- `BASE_URL` and `API_KEY` have no defaults. The default `MODEL` is an
  OpenRouter id; point `BASE_URL` at another provider and set `MODEL` too.
- The reply is printed as plain text. Stage 3 renders markdown.
- Nothing is remembered. Run it twice and the second run knows nothing of
  the first; stage 3 keeps a transcript.

## What it cannot do

Ask *what files are in this directory?* and it guesses or apologises. It
has no way to look. Stage 2.1 gives it one.

## Files

```text
step_01_minimal_chat/
├── llm.py           one request, one reply: the whole program
├── test_step.py     offline tests: the script against a fake OpenAI client
└── README.md        this file
```

## Test

`python -m pytest test_step.py` (from this directory) runs the script with
a fake client and a canned prompt and checks the two messages that were
sent, that a missing usage block prints `None` instead of crashing, and
that an empty stdin exits cleanly.

## What the next step adds

Stage 2.1 passes one tool schema, `bash`, with the request, and runs the
command the model asks for.
