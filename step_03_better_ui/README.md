# Stage 3 - Better UI

The plain white command line gives way to a styled terminal interface.

**What this stage adds:** a presentation layer (`ui.py`, built on `rich`)
and an outer loop, so the program is a chat instead of a one-shot script.
No new agent capability.

## Files

```text
step_03_better_ui/
├── agent.py         the 2.4 loop, drawn by ui.py and wrapped in a chat
├── llm.py           call_llm, unchanged from 2.4
├── tools.py         tools, unchanged
├── ui.py            the rich presentation layer: everything that draws
├── test_step.py     offline test: two chat turns through the two loops
├── pyproject.toml   package metadata; version 0.3.0, depends on rich
└── README.md        this file
```

## The code, piece by piece

### 1. Two loops in `agent.py`

`agent.py`:

```python
ui.banner()

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_input = ui.ask()
    if not user_input:
        break

    messages.append({"role": "user", "content": user_input})

    while True:
        with ui.working():
            message, usage = call_llm(messages)

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = TOOLS[tool_call.function.name](**args)
            ui.tool(tool_call.function.name, args, result)
```

- The **outer** loop asks for the next message and appends it. `messages`
  is never reset, so turn two sees turn one. The transcript is the memory.
- The **inner** loop is stage 2.4 unchanged, with `print` replaced by
  `ui.*` calls and a spinner around the model call.

### 2. The presentation layer

`ui.py` knows nothing about models or tools. It receives strings and
dicts. Two methods carry the ideas:

`ui.py`:

```python
    def tool(self, name, args, result):
        header = Text.assemble((f"{name} ", f"bold {TOOL}"), (self._format_args(args), MUTED))
```

```python
    def _format_result(self, result):
        lines = result.strip().splitlines() or ["(no output)"]
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
output of the latest tool call. `summary()` prints the totals at exit.

One Windows detail: the constructor switches stdout to UTF-8, because the
default console code page cannot draw the box characters `rich` uses.

## Run it

```bash
pip install rich
python agent.py
> what does this repo do?
> and what is ui.py for?
```

The second question is answered from memory of the first turn.

## Diff from stage 2.4

```bash
diff ../step_02_4_agent_loop/agent.py agent.py
cat ui.py
```
