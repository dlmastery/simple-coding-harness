# Stage 3 - Better UI

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 2.4 - The agent loop](../step_02_4_agent_loop/README.md). Next: [Stage 4 - Skill discovery and reading](../step_04_skills/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

The plain white command line gives way to a styled terminal interface.

**What this stage adds:** a presentation layer (`ui.py`, built on `rich`)
and an outer loop, so the program is a chat instead of a one-shot script.
No new agent capability.

## Why an outer loop and a UI layer

Stage 2.4 answers one question and exits, and the transcript dies with
it. A follow-up question ("and what is `ui.py` for?") needs the previous
turn, so the message list has to outlive one question: that is the outer
loop. The UI layer exists so that `agent.py` stays a loop and nothing
else; every later stage adds to the loop, and none of them should have
to know how a panel is drawn.

## The code, piece by piece

### 1. Two loops in `agent.py`

`agent.py`:

```python
ui.banner()

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_input = ui.ask()
    if user_input is None or user_input in ("/exit", "/quit"):  # ctrl-d, ctrl-c, or asked to leave
        break
    if not user_input:  # an empty line is not a message
        continue

    messages.append({"role": "user", "content": user_input})

    try:
        for _ in range(MAX_CALLS):
            with ui.working():
                message, usage = call_llm(messages)

            messages.append(entry(message))
            ui.usage(usage)

            if message.content:
                ui.agent(message.content)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args, result = run_tool(tool_call)
                ui.tool(tool_call.function.name, args, result)
```

- The **outer** loop asks for the next message and appends it. `messages`
  is never reset, so turn two sees turn one. The transcript is the memory.
  `ui.ask()` returns `None` when there is no more input (ctrl-d, ctrl-z
  then enter on Windows, ctrl-c) and `""` for an empty line; only the
  first ends the chat, together with `/exit` and `/quit`.
- The **inner** loop is stage 2.4 unchanged, with `print` replaced by
  `ui.*` calls and a spinner around the model call.

### 2. Keeping the transcript valid when a turn is cut short

`agent.py`:

```python
        else:
            ui.note(f"stopped after {MAX_CALLS} model calls in one turn; say 'continue' to go on")
    except KeyboardInterrupt:  # ctrl-c mid-turn: keep the transcript valid and ask again
        repair(messages, "(interrupted before this tool ran)")
        ui.note("interrupted")
    except (openai.APIError, RuntimeError) as e:  # the user message stays; try again later
        ui.note(f"model call failed: {e}")
```

Now that the transcript outlives a turn, a turn that dies half-way must
not leave it in a state the API refuses. Three things can cut a turn
short, and each ends in a transcript the next request accepts:

- the cap of `MAX_CALLS` model calls, reached with every tool call already
  answered;
- ctrl-c, which can land between an assistant message with tool calls and
  their results. `repair` appends a `tool` message reading
  `(interrupted before this tool ran)` for every call that has none:

```python
def repair(messages, note):
    """Give every tool call at the end of the transcript that has no result one, so the
    next request is valid. Used when a turn is interrupted between a call and its result."""
    answered = {m["tool_call_id"] for m in messages if m["role"] == "tool"}
    last = next((m for m in reversed(messages) if m["role"] != "tool"), None)
    if last and last["role"] == "assistant":
        for call in last.get("tool_calls") or []:
            if call["id"] not in answered:
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": note})
```

- a failed model call (`openai.APIError`, or the `RuntimeError` that
  `call_llm` raises for an empty reply). Nothing was appended, so the
  transcript is as valid as it was; your message stays in it, and the
  next thing you type is sent after it.

### 3. The presentation layer

`ui.py` knows nothing about models or tools. It receives strings and
dicts. Two methods carry the ideas:

`ui.py`:

```python
    def tool(self, name, args, result):
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
```

```python
    def _format_result(self, result):
        lines = str(result).strip().splitlines() or ["(no output)"]
        shown = lines[:MAX_TOOL_OUTPUT_LINES]
        body = Text("\n".join(shown), style=MUTED)
        hidden = len(lines) - len(shown)
        if hidden > 0:
            body.append(f"\n… {hidden} more lines", style=f"italic {TOOL}")
        return body
```

A tool result is drawn in a panel showing only its first twelve lines.
That is a screen decision, not a context decision. The model still
receives the whole result. Stage 14 is where the model's copy gets
trimmed.

```python
    def usage(self, stats):
        """One line per call: prompt, completion, reasoning and cached tokens."""
        for key, value in stats.items():
            self._totals[key] = self._totals.get(key, 0) + (value or 0)
        parts = " · ".join(f"{value:,} {key.replace('_tokens', '')}" for key, value in stats.items() if value)
```

The usage line after every call is where prefix caching becomes visible.
A typical line shows a few thousand prompt tokens with most of them
cached. Only a few hundred new prompt tokens arrive, and those are the
output of the latest tool call. `summary()` prints the totals when you
leave.

One Windows detail: the constructor switches stdout to UTF-8, because the
default console code page cannot draw the box characters `rich` uses.

## Run it

bash:

```bash
pip install rich
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python agent.py
```

PowerShell:

```powershell
pip install rich
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python agent.py
```

Expected output:

```text
──────────────────────────── coding agent ────────────────────────────
  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> what does this repo do?

  ┌──────────────────────────────────────────────┐
  │ bash ls                                      │
  │ ──────────────────────────────────────────── │
  │ README.md                                    │
  │ agent.py                                     │
  │ …                                            │
  └──────────────────────────────────────────────┘

  1,204 prompt · 31 completion · 1,152 cached

  agent

  This directory holds stage 3 of a coding agent: ...

> and what is ui.py for?
```

The second question is answered from memory of the first turn.

## Error handling

- A bad tool call: an `Error: ...` panel, and the model gets the same text.
- A failing command: its stderr in the panel; `Error: command timed out after 60s` after a minute.
- ctrl-c during a turn: `interrupted`; unanswered tool calls get a placeholder result; you are back at the prompt with the transcript intact.
- A dead model call: `model call failed: ...`; your message stays, type again.
- More than 40 model calls in one turn: `stopped after 40 model calls in one turn; say 'continue' to go on`.
- Leaving: `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at the prompt. The totals are printed on the way out.

## Gotchas

- An empty line does nothing. In earlier versions it ended the chat; now
  only EOF, ctrl-c at the prompt and `/exit` do.
- Nothing is saved. Leave and the transcript is gone; stage 8 writes it to
  disk.
- The `bash` tool still runs `cmd.exe` on Windows, and nothing is
  sandboxed or confirmed.
- The spinner (`ui.working`) uses a `rich` live display; it does not work
  from a thread, which matters from stage 22.

## Files

```text
step_03_better_ui/
├── agent.py         the 2.4 loop, drawn by ui.py and wrapped in a chat; repair() for ctrl-c
├── llm.py           call_llm and entry, unchanged from 2.4
├── tools.py         tools, unchanged
├── ui.py            the rich presentation layer: everything that draws
├── test_step.py     offline tests: two turns; bad calls; ctrl-c and API errors; the cap
├── pyproject.toml   package metadata; version 0.3.0, depends on rich
└── README.md        this file
```

## Test

`python -m pytest test_step.py` runs two chat turns through both loops
and checks that turn two sees turn one, that empty lines are skipped and
`/exit` leaves, that bad tool calls each get a result, that ctrl-c inside
a tool leaves a valid transcript and a failed model call keeps the user
message, and that a model that never stops calling tools hits the cap.

## Diff from stage 2.4

```bash
diff ../step_02_4_agent_loop/agent.py agent.py
cat ui.py
```

## What the next step adds

Stage 4 gives the agent skills: `SKILL.md` files whose name and
description go into the system prompt and whose body is read on demand.

<!-- harness-learning-check -->
## Check your understanding

If the interface keeps earlier replies on screen, does the model necessarily see them?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

No. The next request must contain the intended history. Display state and model input are separate objects.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
