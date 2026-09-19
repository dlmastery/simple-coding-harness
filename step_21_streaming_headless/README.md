# Step 21 - Streaming and headless mode

**What this step adds:** the model's reply appears on screen as it is
written, not after it is finished. The inner loop moves into a function,
`turn()`, that runs one user message to completion. And a print mode,
`harness -p PROMPT`, runs one turn without the chat and prints the answer
to stdout, so the harness can sit inside a script or a pipe.

This step forks from **step 15**, not from step 20. Steps 16 to 20 were
tours of other people's harnesses and of OpenRouter; the hand-built
harness continues from where step 15 left it. If you come here from step
20 looking for `/models` and `/route`, they are not in this tree.

## Why stream, and what breaks without it

Up to step 15 the harness sent a request and waited. The spinner turned for
as long as the model took to write its whole reply, and then the reply
landed at once. For a short answer that is fine. For a long explanation,
or a model that thinks for a while first, the wait feels broken: a minute
of spinner, then a screenful of text, and no way to tell a slow model from
a hung one.

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
command line is a few lines. Without it, there is no way to use the
harness from cron, from a Makefile or from another program: the only
entry point is an interactive prompt that waits for a keyboard.

## The code, piece by piece

### 1. A message the loop already understands

`harness/llm.py`:

```python
@dataclass
class StreamedToolCall:
    """One tool call. Same attributes as the SDK's ChatCompletionMessageToolCall."""

    id: str = ""
    type: str = "function"
    function: StreamedFunction = field(default_factory=StreamedFunction)

    def model_dump(self, exclude_none=True):
        """The dict entry() stores for this call: id, type and the function."""
        return {"id": self.id, "type": self.type, "function": {"name": self.function.name, "arguments": self.function.arguments}}


@dataclass
class StreamedMessage:
    """The assembled reply. Same surface as the SDK's ChatCompletionMessage."""

    content: str | None = None
    tool_calls: list[StreamedToolCall] | None = None
    role: str = "assistant"

    def model_dump(self, exclude_none=True):
        """The same three keys entry() keeps - there is nothing else to drop."""
        return entry(self)
```

The SDK's non-streaming call returns a `ChatCompletionMessage`. The loop
reads three things from it: `.content`, `.tool_calls` and, through
`entry()`, each tool call's `model_dump(exclude_none=True)`. These
dataclasses offer the same three. Each tool call is a `StreamedToolCall`
with `.id` and `.function.name` and `.function.arguments`, which is what
`tools.execute()` reads. `entry()` is unchanged from step 15: the dict it
stores has exactly three keys - `role`, `content` and, when there are any,
`tool_calls` - so the session file, compaction and replay all keep
working, and nothing a provider adds to its replies (reasoning text,
annotations) is ever echoed back in the next request. `--debug` shows the
reply through `model_dump`, which for a streamed message is `entry()` again.

### 2. Reading the stream

`harness/llm.py`:

```python
    request = {"model": MODEL, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
    if EXTRA_BODY:
        request["extra_body"] = EXTRA_BODY
    schemas = TOOL_SCHEMAS if tools is None else tools
    if schemas:
        request["tools"] = schemas
    stream = client.chat.completions.create(**request)

    parts = []           # text deltas, in order
    calls = {}           # tool call index -> StreamedToolCall
    final_usage = None   # arrives with the last chunk, which has no choices
    finish_reason = None

    for chunk in stream:
        if getattr(chunk, "error", None):  # a gateway can answer an error as a chunk
            raise RuntimeError(f"model call failed: {chunk.error}")
        if getattr(chunk, "usage", None) is not None:
            final_usage = chunk.usage
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        finish_reason = getattr(choice, "finish_reason", None) or finish_reason
        delta = choice.delta
        if delta is None:
            continue

        if delta.content:
            parts.append(delta.content)
            if on_delta:
                on_delta(delta.content)

        for piece in delta.tool_calls or []:
            # fragments of one call share an index; a provider that sends none gets keyed by id
            key = piece.index if getattr(piece, "index", None) is not None else piece.id or len(calls)
            call = calls.setdefault(key, StreamedToolCall())
            if piece.id:
                call.id = piece.id
            function = getattr(piece, "function", None)
            if function is None:
                continue
            if function.name:
                call.function.name = function.name
            if function.arguments:
                call.function.arguments += function.arguments

    if finish_reason == "length" and calls:
        # the arguments stopped mid-JSON: no call is safe to run, say so instead
        calls = {}
        parts.append(f"\n{CUT_OFF}")
        if on_delta:
            on_delta(f"\n{CUT_OFF}")
```

Two request fields turn streaming on. `stream=True` makes the call return
an iterator of chunks. `stream_options={"include_usage": True}` asks for
one extra chunk at the end that carries the token counts and has an empty
`choices` list. `EXTRA_BODY` is only set when the base URL is OpenRouter;
it asks for the price of the call in the same usage chunk.

Text is simple: each delta's `content` is appended to `parts` and handed
to `on_delta`. The caller decides what to do with it. The main loop prints
it. The subagent and the compaction agent pass no callback and just wait
for the assembled message.

Tool calls need more care. A reply can hold several calls, and each one
arrives in fragments. Every fragment carries an `index` that says which
call it belongs to. The first fragment of a call has its `id` and its
function name. Later fragments carry a few characters of the JSON
arguments. So the code keeps a dict keyed by index, and concatenates the
arguments string. When the stream ends, each entry holds one complete
call. Some gateways send no `index` at all, or `0` for every call; then
the `id` is the key, so two calls do not get merged into one.

Two things can go wrong on the way, and both are handled here rather than
in the loop. A gateway that fails mid-stream sends a chunk with an
`error` field instead of a delta; that becomes a `RuntimeError`, which the
loop reports as a failed call. And a reply that hits `max_tokens` has
`finish_reason == "length"`: its tool-call arguments stop mid-JSON, so
they are thrown away and the text ends with `(reply cut off by
max_tokens)`. The model sees that note on its next turn and can try again
with a shorter reply.

### 3. The same usage dict

`harness/llm.py`:

```python
def usage_from(usage):
    """Token counts as a plain dict. Some proxies send no usage at all."""
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "reasoning_tokens": getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None),
        "cached_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
        "cost": getattr(usage, "cost", None),  # OpenRouter, in dollars; None everywhere else
    }
```

`usage_from` is the step 15 function with one more key: `cost`, which
OpenRouter fills in dollars when asked and every other provider leaves
`None`. `ui.usage()` prints the counts and the cost, and
`compact.needed()` reads `prompt_tokens` to decide when to compact. A
stream that sends no usage chunk hands `usage_from` a `None`, and every
`getattr` on it gives a dict of `None` values, which both callers already
treat as zero.

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
resumed, which is why a resumed chat looks tidier than the live one did.

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
Nothing in this step runs off the main thread; step 22 does, and adds the
guard for it.

### 5. One turn, as a function

`harness/agent.py`:

```python
def turn(messages, user_input, cli=None):
    """One user message, every model call and tool call it leads to.

    Returns the message list, which compaction may have replaced. Returns
    it early, with every tool call answered, when the model call fails or
    the turn is interrupted.
    """
    debug = getattr(cli, "debug", False)
    messages.append({"role": "user", "content": user_input})
    session.save(messages)
    usage = {}

    try:
        for _ in range(MAX_CALLS):
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

            try:
                with spinner:
                    message, usage = call_llm(messages + [injection], on_delta=on_delta)
            except (openai.APIError, RuntimeError) as failed:
                # the user message stays, nothing dangles: the next turn can retry
                if streamed:
                    ui.stream_end()
                ui.note(f"model call failed: {failed}")
                break

            messages.append(entry(message))
            session.save(messages)

            if streamed:
                ui.stream_end()
            elif message.content:
                ui.agent(message.content)  # a reply that did not stream, e.g. from a fake model
            ui.usage(usage)
...
            for tool_call in message.tool_calls:
                args, result = execute(tool_call)
                ui.tool(tool_call.function.name, args, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
                session.save(messages)  # after every message, so a crash loses nothing
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
    except KeyboardInterrupt:
        # ctrl-c mid-turn: answer the tool calls that never ran, so the
        # transcript stays valid, and go back to the prompt.
        session.repair(messages, INTERRUPTED)
        session.save(messages)
        ui.note("interrupted")

    history.sweep()          # the turn is over: bin its temp files...
    history.strip(messages)  # ...and shrink the tool output it produced

    if compact.needed(usage, messages):
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

Three things bound the turn, and all three leave the transcript in a state
the API will accept again:

- `MAX_CALLS = 40` model calls. A model that keeps calling tools is
  looping, not working; the loop stops, says so, and the user can type
  `continue`.
- A failed model call (`openai.APIError` for anything the SDK raises, the
  `RuntimeError` from an in-stream error chunk) ends the turn with a note.
  The user message stays, no tool call is left unanswered, and the next
  turn simply retries.
- ctrl-c during a call or a tool run. `session.repair()` gives every tool
  call of the last reply that has no result yet a tool message,
  `INTERRUPTED` - `(interrupted before this tool ran)` - so the assistant
  message is not orphaned. Then the prompt comes back.

`harness/session.py`:

```python
def repair(messages, note):
    """Answer every tool call in the last reply that has no result. Returns how many.

    A crash or ctrl-c between a reply and its tool results leaves a transcript
    the API refuses; a placeholder result per unanswered call makes it valid.
    """
    last = next((m for m in reversed(messages) if m["role"] != "tool"), None)
    if not last or last["role"] != "assistant" or not last.get("tool_calls"):
        return 0
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    missing = [call["id"] for call in last["tool_calls"] if call["id"] not in answered]
    for call_id in missing:
        messages.append({"role": "tool", "tool_call_id": call_id, "content": note})
    return len(missing)
```

The same `repair()` runs in `session.load()`, with a different note, for
a transcript an older crash left behind. The ctrl-c path is the step 15
one; only the note has a name now, so the tests can check for it.

### 6. Tool calls that cannot run are results, not exceptions

`harness/tools.py`:

```python
def execute(tool_call, allowed=None):
    """Turn one tool call into (args, result). Never raises: whatever goes
    wrong becomes the result string, so the model reads it and tries again.

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. `allowed` is the
    set of tool names the caller offered; a call outside it is denied, so a
    subagent cannot run a withheld tool just by naming it.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:  # the model wrote broken JSON
        return {}, f"Error: the arguments of {name} are not a JSON object: {e}"
    if allowed is not None and name not in allowed:  # offered set == executable set
        action, reason = "deny", f"{name} is not available to this agent"
    elif name not in TOOLS:  # a name that is not in the table
        return args, f"Error: no tool named {name!r}."
    else:
        action, reason = check(name, args)
    if action == "deny":
        return args, f"Blocked by policy: {reason}"
    if action == "ask" and not ui.approve(reason):
        return args, "The user denied this tool call."
    try:
        result = TOOLS[name](**args)  # name -> function, JSON -> kwargs
    except Exception as e:  # wrong arguments, missing file, anything the tool raises
        return args, f"Error: {type(e).__name__}: {e}"
    if not isinstance(result, str):  # a tool message must be text
        result = "(no output)" if result is None else json.dumps(result, default=str)
    return args, result
```

`execute()` is unchanged from step 15, and it matters more now: a
streamed reply can end with a call whose arguments are broken JSON, and a
failed call must still get its tool message before the next request goes
out. It never raises. Arguments that are not a JSON object, a tool
name that does not exist, a missing required argument, a file that is not
there: each comes back as an `Error: ...` string and goes into the
transcript as that call's result. That is not politeness. The API refuses
a transcript in which an assistant message has a `tool_calls` entry with
no matching tool message, so a crash between the two would leave a
session that cannot be resumed. The `allowed` set is for subagents: what
they may run is exactly what they were offered.

### 7. Print mode

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
        if cli.resume:
            messages = resume_last(messages)
        else:
            session.PERSIST = False  # a one-off run leaves no session behind
        messages = turn(messages, cli.print, cli)
        reply = last_reply(messages)
        print(reply)
        raise SystemExit(0 if reply else 1)  # empty answer or a failed turn: tell the caller
```

`-p` skips the banner and the input loop. It runs one turn on the prompt
given on the command line, prints the last assistant message with a plain
`print`, and exits. The exit code is 0 when there is an answer and 1 when
there is none - the model ended with tool calls and no text, or the model
call failed - so a script can tell the two apart. Tool calls inside that
turn still go through the same permissions.

A one-off run leaves no session file behind (`session.PERSIST = False`),
so `harness --resume` afterwards still opens your last interactive chat.
`-p` together with `--resume` does the opposite on purpose: it opens the
newest saved chat, runs one more turn in it, and saves that turn.

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

`harness/ui.py`:

```python
    def approve(self, reason):
        """Stage 11: stop and ask before a tool call the rules rate as 'ask'.

        In print mode nothing may reach stdout, and without a terminal there
        is nobody to ask: the call is denied and stderr says so.
        """
        if not self.live and not sys.stdin.isatty():
            self.note(f"denied, no terminal to ask on: {reason}")
            return False
        self.console.print(Padding(Text(reason, style=f"bold {TOOL}"), (1, 0, 0, 2)))
        try:
            if self.live:
                answer = prompt.read("  allow? (y/n)> ").strip()
            else:
                sys.stderr.write("  allow? (y/n)> ")
                sys.stderr.flush()
                answer = input().strip()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.lower().startswith("y")
```

The one thing in print mode that could still write to stdout is the
approval prompt, so it is handled here. With a terminal on stdin the
question goes to stderr and the answer is read from stdin. Without one -
cron, CI, `< /dev/null` - there is nobody to ask, so the call is denied
and stderr says which one and why. The model gets "The user denied this
tool call." either way.

## Run it

Bash:

```bash
pip install -e .
harness
```

PowerShell:

```powershell
pip install -e .
harness
```

Then:

```text
> explain what history.py does, in three paragraphs
```

The spinner turns briefly, then the `agent` header appears and the text
fills in word by word. The token line prints once the stream ends. Ask
for something that needs tools:

```text
> list the python files here and count their lines
```

The spinner runs for the whole first call, because the model answers with
tool calls and no text. The tool panels print, then the final reply
streams in.

Print mode, bash:

```bash
harness -p "what does harness/history.py do? one sentence" > answer.txt
cat answer.txt
```

PowerShell:

```powershell
harness -p "what does harness/history.py do? one sentence" > answer.txt
Get-Content answer.txt
```

Tool panels and token counts go to the terminal through stderr.
`answer.txt` holds only the reply.

Run the offline tests from the repository root:

```bash
python run_tests.py 21
```

### Expected output

```text
──────────────────────────── coding agent ─────────────────────────────
  sandbox: none  ·  /sessions  /rewind  ·  alt-enter for a newline  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> list the python files here and count their lines

  ┌─────────────────────────────────────────────────────────────┐
  │ bash {"command": "wc -l harness/*.py"}                      │
  │ ─────────────────────────────────────────────────────────── │
  │   183 harness/agent.py                                      │
  │   ...                                                       │
  └─────────────────────────────────────────────────────────────┘

  agent

  There are 16 Python files under harness/, 1,900 lines in total. The
  largest is llm.py ...

  1,842 prompt · 96 completion
```

And in print mode:

```text
$ harness -p "what does harness/history.py do? one sentence" > answer.txt
  1,650 prompt · 31 completion            <- stderr
$ cat answer.txt
It keeps the transcript small: caps fresh tool output, stubs it once the turn is over, and drops it whole when a request would not fit.
$ echo $?
0
```

## Error handling

- **A bad tool call.** Arguments that are not a JSON object give
  `Error: the arguments of bash are not a JSON object: ...`; a name the
  registry does not know gives `Error: no tool named 'nope'.`; a missing
  required argument gives `Blocked by policy: bash: missing argument
  'command'` (from `permissions.check`) or `Error: TypeError: ...` (from
  the tool itself). Each is that call's result; the loop goes on.
- **A failing command.** `bash` returns the combined output and, on a
  timeout, `Timed out after 60s and was killed. Output so far: ...`. The
  command and everything it started are killed, not just the shell.
- **A dead model call.** Any `openai.APIError` - wrong key, 429, 5xx, a
  network error - or an error chunk in the stream ends the turn with
  `model call failed: ...`. Nothing is lost: the user message is in the
  transcript, and the next turn retries. In print mode this exits 1.
- **ctrl-c.** During a model call or a tool run, the turn ends with every
  pending tool call answered `(interrupted before this tool ran)` and the
  prompt comes back. A second ctrl-c at the empty prompt leaves.
- **Leaving.** `/exit` or `/quit`, ctrl-d, or on Windows ctrl-z then
  enter. An empty line does nothing.
- **A session cut short.** If the process died between a reply and its
  tool results, `session.load()` appends `(the harness stopped before this
  tool ran; no result was recorded)` for each missing one, so `--resume`
  still works.

## Gotchas / What this is not

- **The tool named `bash` runs `cmd.exe` on Windows.** `sandbox.run` uses
  `shell=True`, and there is no sandbox on Windows: the banner says
  `sandbox: none`. Only the permission rules stand between the model and
  the disk.
- **Print mode is headless, not unattended.** Without a terminal every
  `ask` is denied; with one, the question appears on stderr. There is no
  `--yes` flag. If a scripted run needs a command the rules rate `ask`,
  add the pattern to `BASH_RULES` or give the model a way that is
  already allowed.
- **Print mode saves nothing** unless `--resume` is given. A cron job
  will not fill `~/.simple-harness/sessions` with one file per run.
- **Reasoning is not shown.** Providers that stream `reasoning` deltas
  (OpenRouter, DeepSeek) get them dropped: the spinner keeps turning until
  the first `content` delta, so thinking time looks like latency. The
  transcript never echoes reasoning back either, which some providers
  require for multi-step tool use; if a model degrades after the first
  tool call, that is why.
- **The live view is plain text; replay is markdown.** A resumed session
  looks different from the live one. That is a display difference only.
- **`stream_options={"include_usage": True}`** is an OpenAI extension
  that most gateways support. When a provider ignores it, the usage dict
  is all `None`, the token line is empty, and compaction never triggers
  on its own. `/compact` still works.
- **Not a retry layer.** A failed call ends the turn; retrying is the
  user's choice. Step 34 adds retries.

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
- Every failure has a place in the transcript. A crash mid-turn used to
  mean a session file with an orphaned tool call, which the API refused
  on resume. Now a tool error is a tool result, a dead call ends the turn
  cleanly, and `session.load` repairs what an older crash left behind.

## Files

```text
step_21_streaming_headless/
├── harness/
│   ├── llm.py         call_llm streams: text deltas, tool calls assembled chunk by chunk
│   ├── agent.py       turn() runs one user message; -p PROMPT runs one turn headless
│   ├── ui.py          stream_start / stream_delta / stream_end; headless() to stderr
│   ├── tools.py       the registry; execute() is the one permission-checked entry point
│   ├── commands.py    slash commands: /rewind /sessions /compact /exit
│   ├── compact.py     the compaction agent from stage 14
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py     the late injection block, unchanged since stage 10
│   ├── history.py     keeps the transcript small: caps, strips and drops old tool output
│   ├── permissions.py allow / ask / deny rules; which tool calls need a human
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash; kills the whole process tree on timeout
│   ├── session.py     append-only JSONL session log; load() repairs a cut-off turn
│   ├── skills.py      skills, unchanged since stage 9
│   ├── subagent.py    exploration subagents with their own context window
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests against a fake streaming client
├── pyproject.toml     package metadata; version 0.21.0
└── README.md          this file
```

## Diff from step 15

```bash
diff -r ../step_15_subagents/harness harness
```

Changed: `llm.py` (streaming, `StreamedMessage`, `cost` in `usage_from`,
`on_delta`, `finish_reason`), `ui.py` (`stream_start`, `stream_delta`,
`stream_end`, `headless`, `working` returns the status object,
`approve` in print mode, cost in the token line), `agent.py` (`turn`,
`INTERRUPTED`, `last_reply`, `resume_last`, `-p`), `session.py`
(`PERSIST`). Everything else is the step 15 file.

## What the next step adds

Step 22 runs the tool calls of one reply side by side: `execute()` splits
into `decide()` and `run()`, and a thread pool runs the allowed calls
together.
