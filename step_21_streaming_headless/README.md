# Step 21 - Streaming and headless mode

**What this step adds:** the model's reply appears on screen as it is
written, not after it is finished. The inner loop moves into a function,
`turn()`, that runs one user message to completion. And a print mode,
`harness -p PROMPT`, runs one turn without the chat and prints the answer
to stdout, so the harness can sit inside a script or a pipe.

## Files

```text
step_21_streaming_headless/
├── harness/
│   ├── llm.py         call_llm streams: text deltas, tool calls assembled chunk by chunk
│   ├── agent.py       turn() runs one user message; -p PROMPT runs one turn headless
│   ├── ui.py          stream_start / stream_delta / stream_end; headless() to stderr
│   ├── tools.py       the registry; execute() is the one permission-checked entry point
│   ├── commands.py    slash commands, unchanged since stage 14
│   ├── compact.py     the compaction agent from stage 14
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py     the late injection block, unchanged since stage 10
│   ├── history.py     keeps the transcript small: trims old tool output
│   ├── permissions.py allow / ask / deny rules; which tool calls need a human
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash
│   ├── session.py     append-only JSONL session log, unchanged since stage 14
│   ├── skills.py      skills, unchanged since stage 9
│   ├── subagent.py    exploration subagents with their own context window
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests against a fake streaming client
├── pyproject.toml     package metadata; version 0.21.0
└── README.md          this file
```

## Why stream

Up to step 15 the harness sent a request and waited. The spinner turned for
as long as the model took to write its whole reply, and then the reply
landed at once. For a short answer that is fine. For a long explanation,
or a model that thinks for a while first, the wait feels broken.

The chat completions API can send the reply in pieces. With `stream=True`
the response is not one object but a sequence of chunks. Each chunk holds a
small delta: a few characters of text, or a fragment of a tool call. The
harness prints the text deltas as they arrive and collects the tool call
fragments until the stream ends.

Streaming changes what the loop receives, not what the loop does. The
loop still needs one message with `.content` and `.tool_calls`, and one
usage dict. So `call_llm` assembles the chunks into exactly that shape and
returns it. The loop in `agent.py` does not know the reply was streamed.

The same rebuilt loop makes headless mode cheap. Once the inner loop is a
function that takes a message list and a prompt, calling it once from the
command line is three lines.

## The code, piece by piece

### 1. A message the loop already understands

`harness/llm.py`:

```python
@dataclass
class StreamedMessage:
    """The assembled reply. Same surface as the SDK's ChatCompletionMessage."""

    content: str | None = None
    tool_calls: list[StreamedToolCall] | None = None
    role: str = "assistant"

    def model_dump(self, exclude_none=True):
        """The dict the loop appends to the transcript."""
        entry = {"role": self.role, "content": self.content, "tool_calls": None}
        if self.tool_calls:
            entry["tool_calls"] = [
                {"id": c.id, "type": c.type, "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in self.tool_calls
            ]
        if exclude_none:
            entry = {k: v for k, v in entry.items() if v is not None}
        return entry
```

The SDK's non-streaming call returns a `ChatCompletionMessage`. The loop
reads three things from it: `.content`, `.tool_calls` and
`model_dump(exclude_none=True)`. This dataclass offers the same three. Each
tool call is a `StreamedToolCall` with `.id` and `.function.name` and
`.function.arguments`, which is what `tools.execute()` reads. The dict
from `model_dump` has the same keys as before, so the session file,
compaction and replay all keep working.

### 2. Reading the stream

`harness/llm.py`:

```python
    request = {"model": MODEL, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    stream = client.chat.completions.create(**request)

    parts = []          # text deltas, in order
    calls = {}          # tool call index -> StreamedToolCall
    final_usage = None  # arrives with the last chunk, which has no choices

    for chunk in stream:
        if getattr(chunk, "usage", None) is not None:
            final_usage = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue

        if delta.content:
            parts.append(delta.content)
            if on_delta:
                on_delta(delta.content)

        for piece in delta.tool_calls or []:
            call = calls.setdefault(piece.index, StreamedToolCall())
            if piece.id:
                call.id = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call.function.name = function.name
            if function.arguments:
                call.function.arguments += function.arguments
```

Two request fields turn streaming on. `stream=True` makes the call return
an iterator of chunks. `stream_options={"include_usage": True}` asks for
one extra chunk at the end that carries the token counts and has an empty
`choices` list.

Text is simple: each delta's `content` is appended to `parts` and handed
to `on_delta`. The caller decides what to do with it. The main loop prints
it. The subagent and the compaction agent pass no callback and just wait
for the assembled message.

Tool calls need more care. A reply can hold several calls, and each one
arrives in fragments. Every fragment carries an `index` that says which
call it belongs to. The first fragment of a call has its `id` and its
function name. Later fragments carry a few characters of the JSON
arguments. So the code keeps a dict keyed by index, and concatenates the
arguments string. When the stream ends, each entry holds one complete call.

### 3. The same usage dict

`harness/llm.py`:

```python
def usage_from(chunk_usage):
    """The same usage dict the non-streaming call produced. All None if no usage came."""
    if chunk_usage is None:
        return {"prompt_tokens": None, "completion_tokens": None, "reasoning_tokens": None, "cached_tokens": None}
    completion_details = getattr(chunk_usage, "completion_tokens_details", None)
    prompt_details = getattr(chunk_usage, "prompt_tokens_details", None)
    return {
        "prompt_tokens": chunk_usage.prompt_tokens,
        "completion_tokens": chunk_usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
    }
```

The usage keys do not change. `ui.usage()` prints them, and
`compact.needed()` reads `prompt_tokens` to decide when to compact. A
provider that sends no usage chunk gets a dict of `None` values, which
both callers already treat as zero.

### 4. Printing live

`harness/ui.py`:

```python
    def stream_start(self):
        """The header, printed once, when the first piece of text arrives."""
        if not self.live:
            return
        self.console.print(Padding(Text("agent", style=f"bold {ACCENT}"), (1, 0, 1, 2)))

    def stream_delta(self, text):
        """One piece of text, written raw and flushed. No markdown: it is not finished yet."""
        if not self.live:
            return
        self.console.out(text, end="", highlight=False)
        self.console.file.flush()

    def stream_end(self):
        """The reply is complete: end the line."""
        if not self.live:
            return
        self.console.out("")
```

Three calls: a header, then raw text, then a newline. The text is written
with `console.out`, which does no wrapping and no markup, and flushed after
every piece, so it appears immediately. Markdown cannot be rendered on a
half-finished reply, so the live view is plain text. `ui.agent()` stays as
it was and still renders markdown; `replay` uses it when a session is
resumed.

`harness/ui.py`:

```python
    def working(self, label="thinking"):
        """The spinner. Use it as a context manager; call .stop() to end it early."""
        return self.console.status(Text(label, style=MUTED), spinner="dots", spinner_style=ACCENT)
```

The spinner used to be a context manager built on a generator. Now it
returns the `rich` status object itself. That object is still a context
manager, so `with ui.working(...)` in the subagent and in `/compact`
keeps working. It also has a `.stop()` method, which the loop needs.

### 5. One turn, as a function

`harness/agent.py`:

```python
def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced.
    """
    debug = getattr(cli, "debug", False)
    messages.append({"role": "user", "content": user_input})

    while True:
        injection = reminder()
        ui.injection(injection["content"])

        if history.fit(messages):
            ui.note("dropped old tool output to make this request fit")

        spinner = ui.working(active_form())
        streamed = False

        def on_delta(text):
            nonlocal streamed
            if not streamed:
                spinner.stop()  # the wait is over: the first words are here
                ui.stream_start()
                streamed = True
            ui.stream_delta(text)

        with spinner:
            message, usage = call_llm(messages + [injection], on_delta=on_delta)

        messages.append(message.model_dump(exclude_none=True))
        session.save(messages)

        if streamed:
            ui.stream_end()
        elif message.content:
            ui.agent(message.content)  # a reply that did not stream, e.g. from a fake model
        ui.usage(usage)
...
    if compact.needed(usage):
        messages = commands.compact(messages)
    return messages
```

The body of the old `while True` is now `turn()`. It appends the user
message, loops over model calls and tool calls until the model stops
calling tools, then sweeps, strips and compacts. It returns the list
because compaction may replace it with a new one.

The spinner runs only until the first delta. `on_delta` closes over the
spinner and a flag. On its first call it stops the spinner and prints the
header. After that it just prints text. If the model calls tools without
saying anything, `on_delta` never fires and the spinner runs to the end of
the call as before.

### 6. Print mode

`harness/agent.py`:

```python
def last_reply(messages):
    """The text of the newest assistant message, or an empty string."""
    for message in reversed(messages):
        if message["role"] == "assistant" and message.get("content"):
            return message["content"]
    return ""
...
    parser.add_argument("-p", "--print", metavar="PROMPT", help="run one turn, print the answer, exit")
    cli = parser.parse_args()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if cli.print:
        ui.headless()
        messages = turn(messages, cli.print, cli)
        print(last_reply(messages))
        raise SystemExit(0)
```

`-p` skips the banner and the input loop. It runs one turn on the prompt
given on the command line, prints the last assistant message with a plain
`print`, and exits with status 0. Tool calls inside that turn still go
through the same permissions. A call rated `ask` still prompts on the
terminal.

`harness/ui.py`:

```python
    def headless(self):
        """Print mode: progress goes to stderr, so stdout carries only the answer."""
        self.console = Console(stderr=True)
        self.live = False
```

`headless()` moves the `rich` console to stderr and turns the live stream
off. Tool panels and token counts still show on stderr, so a person
watching the terminal sees progress. Stdout receives one thing: the
answer. That is what makes `harness -p "..." > answer.md` work.

## Run it

```bash
pip install -e .
harness
> explain what history.py does, in three paragraphs
```

The spinner turns briefly, then the `agent` header appears and the text
fills in word by word. The token line prints once the stream ends. Ask
for something that needs tools:

```bash
> list the python files here and count their lines
```

The spinner runs for the whole first call, because the model answers with
tool calls and no text. The tool panels print, then the final reply
streams in.

Print mode:

```bash
harness -p "what does harness/history.py do? one sentence" > answer.txt
cat answer.txt
```

Tool panels and token counts go to the terminal through stderr.
`answer.txt` holds only the reply.

Run the offline tests from the repository root:

```bash
python run_tests.py 21
```

## What to notice

- The loop did not change shape. Compare `turn()` with the body of the
  step 15 `while True`: the same append, call, append, execute, append.
  The streaming logic lives in `call_llm`, behind the same return type.
- Tool calls stream too, but nothing runs until the stream ends. A tool
  call is only complete when its arguments string is valid JSON, and that
  happens at the last fragment. So the loop waits for the whole reply,
  then executes.
- The subagent and the compaction agent call the same `call_llm` and pass
  no `on_delta`. Their replies are assembled silently. Only the main
  agent's text is worth streaming to the screen.
- `stream_options={"include_usage": True}` is an OpenAI extension that
  most gateways support. When a provider ignores it, the usage dict is
  all `None`, the token line is empty, and compaction never triggers on
  its own. `/compact` still works.
- Print mode keeps the permission rules. It is headless, not unattended.
  A denied command still returns "The user denied this tool call." to
  the model.

## Diff from step 15

```bash
diff -r ../step_15_subagents/harness harness
```

Changed: `llm.py` (streaming, `StreamedMessage`, `usage_from`,
`on_delta`), `ui.py` (`stream_start`, `stream_delta`, `stream_end`,
`headless`, `working` returns the status object), `agent.py` (`turn`,
`last_reply`, `-p`). Everything else is unchanged from step 15.
