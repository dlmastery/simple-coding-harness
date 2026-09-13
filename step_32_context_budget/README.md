# Step 32 - Context budget

**What this step adds:** a view of where the context window goes, and one
way to spend less of it. `budget.breakdown` estimates the tokens of the
next request in eight categories: system prompt, instruction files, skills
index, memory index, tool schemas, transcript text, tool results and
images. `/context` draws one bar per category and the share of the window
in use. The usage line prints the real prompt count next to the estimate.
A note warns at 50% and at 75% of the window, once each per session. A
tool whose schema is over 300 tokens is deferred: it goes out as a
one-line stub until the model calls `load_tool` with its name.

## Why a budget, and why deferred tools

Every request carries more than the conversation. The system prompt grew
with each step, the instruction files joined it in step 31, and every tool
schema rides along on every call. The model bills all of it. Up to now the
only number on screen was the total prompt count, which says how full the
window is and nothing about why. The breakdown says why. It is an estimate,
four characters to a token, so the usage line shows the real count next to
it; a drift between the two is information, not a bug to hide.

Tool schemas are the part the user cannot see and cannot edit. An MCP
server can add a tool with a schema of a thousand tokens, and that schema
goes out on every call whether the tool is used or not. A deferred tool
keeps its name and one line in the request. The full schema costs tokens
only after the model asks for it, and then only once per session.

## The code, piece by piece

### 1. The breakdown

`harness/budget.py`:

```python
def breakdown(messages):
    ...
    system = ""
    rest = messages
    if messages and messages[0].get("role") == "system":
        system = messages[0].get("content") or ""
        rest = messages[1:]
    instructions = part_of(system, instructions_prompt())
    skills = part_of(system, skills_prompt())

    text = results = images = 0
    for message in rest:
        content = message.get("content")
        if isinstance(content, list):
            images += IMAGE_TOKENS * sum(1 for part in content if part.get("type") == "image_url")
            text += sum(tokens(part.get("text", "")) for part in content)
        elif message.get("role") == "tool":
            results += tokens(json.dumps(message))
        else:
            text += tokens(json.dumps(message))

    counts = {
        "system prompt": tokens(system) - instructions - skills,
        "instruction files": instructions,
        "skills index": skills,
        "memory index": tokens(memory_index()),
        "tool schemas": sum(schema_tokens(s) for s in active_schemas()),
        "transcript text": text,
        "tool results": results,
        "images": images,
    }
    counts["total"] = sum(counts.values())
    counts["window"] = config.CONTEXT_WINDOW
    return counts
```

The system prompt is one string, so it is split by subtraction: the
instruction files and the skills index are measured on their own, and
"system prompt" is what remains. `part_of` counts a piece only when it is
inside the prompt, so a workspace without instruction files reports zero.
The memory index and the tool schemas are not in `messages` at all. They
are added to every request, so they are counted from their sources. The
estimate for a picture is the flat `IMAGE_TOKENS` from step 24.

### 2. The bars and the warnings

`harness/budget.py`:

```python
def render(messages):
    """The breakdown as text: one bar per category, then the share of the window used."""
    counts = breakdown(messages)
    largest = max(counts[category] for category in CATEGORIES) or 1
    lines = []
    for category in CATEGORIES:
        count = counts[category]
        bar = "#" * round(BAR * count / largest)
        lines.append(f"{category:<18} {count:>8,}  {bar}")
    used = 100 * counts["total"] / counts["window"]
    lines.append(f"{'total':<18} {counts['total']:>8,}  {used:.0f}% of the {counts['window']:,} token window")
    return "\n".join(lines)


def check(prompt_tokens):
    ...
    if not prompt_tokens:
        return None
    used = prompt_tokens / config.CONTEXT_WINDOW
    crossed = [t for t in THRESHOLDS if used >= t and t not in WARNED]
    if not crossed:
        return None
    WARNED.update(crossed)
```

The longest bar is the largest category, not the window: the point is to
compare the categories with each other, and the last line gives the share
of the window. `check` is given the real prompt count after every call.
`WARNED` remembers which lines were reported, so each fires once. A prompt
that jumps past both lines at once earns one warning, for the higher line.

### 3. The loop measures what it sends

`harness/agent.py`:

```python
        estimate = budget.breakdown(messages)["total"]  # what this request should cost
        with spinner:
            message, usage = call_llm(with_mode(messages) + [injection], tools=active_schemas(plan.toolset()), on_delta=on_delta)
        ...
        ui.usage(usage, estimate)
        warning = budget.check(usage.get("prompt_tokens") or estimate)
        if warning:
            ui.note(warning)
```

The estimate is taken before the call, of the messages about to go out.
The usage line gets both numbers. The warning uses the real count when the
model reported one and the estimate otherwise, so a fake model in a test
still triggers it. `plan.toolset()` chooses the tools for the mode, as in
step 28, and `active_schemas` turns the deferred ones into stubs on the
way to the wire.

### 4. The stub

`harness/tools.py`:

```python
def stub(schema):
    """The one-line stand-in for a deferred schema: same name, no parameters."""
    name = schema["function"]["name"]
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"deferred; call load_tool('{name}') to enable",
            "parameters": {"type": "object", "properties": {}},
        },
    }


def active_schemas(schemas=None):
    ...
    offered = []
    stubbed = False
    for schema in TOOL_SCHEMAS if schemas is None else schemas:
        if schema["function"]["name"] in LOADED or not is_deferred(schema):
            offered.append(schema)
        else:
            offered.append(stub(schema))
            stubbed = True
    if stubbed:
        offered.append(LOAD_TOOL_SCHEMA)
    return offered
```

A stub is a real function tool with the tool's own name, one line of
description and no parameters. The model can still call it, and gets a
result that says to load it first. `active_schemas` takes a list of full
schemas that another filter already chose: the plan-mode set, a subagent's
set, the browse set. `TOOL_SCHEMAS` stays the registry of full schemas and
`active_schemas()` is what goes on the wire. `load_tool` is offered only
when there is something to load.

### 5. Loading a tool

`harness/tools.py`:

```python
def load_tool(name: str) -> str:
    """Enable a deferred tool and return its full schema."""
    schema = next((s for s in TOOL_SCHEMAS if s["function"]["name"] == name), None)
    if schema is None:
        return f"Error: no tool named '{name}'."
    if not is_deferred(schema):
        return f"{name} is not deferred; call it directly."
    LOADED.add(name)
    return f"{name} is enabled for the rest of the session. Its schema:\n" + json.dumps(schema["function"], indent=2)


def load_first(name):
    """The result for a call to a deferred tool that was not loaded, or None."""
    if name in LOADED or name not in deferred_names():
        return None
    return f"Error: {name} is deferred. Call load_tool('{name}') first, then call {name} again with its full arguments."
```

`LOADED` is a set of names that lasts for the session. Once a name is in
it, `active_schemas` sends the full schema on every later call. The
schema comes back in the tool result too, so the model has it in the
transcript at once, before the next request offers it in full.

### 6. A call to a stub

`harness/tools.py`:

```python
    args = json.loads(tool_call.function.arguments)
    advice = load_first(tool_call.function.name)
    if advice is not None:
        return args, "deferred", advice
    action, reason = check(tool_call.function.name, args)
```

The check sits in `decide`, ahead of the permission rules. A stub has no
parameters, so a call to it arrives with empty arguments, and a rule that
reads `args["command"]` would fail on it. The `deferred` verdict never
runs, never asks, and never reaches a hook; `settle` turns it into the
advice as the tool result.

### 7. The system prompt lists the deferred tools

`harness/llm.py`:

```python
def deferred_section(schemas=None):
    """The names of the deferred tools, one per line, or empty when there are none."""
    names = deferred_names(schemas)
    if not names:
        return ""
    return DEFERRED_INTRO + "\n".join(f"- {name}" for name in names) + "\n"
```

`harness/agent.py`:

```python
    mcp_client.connect_all()  # external tools join the registry before the first turn
    hooks.session_start()     # SessionStart hooks; their context stays in the late block

    messages = [{"role": "system", "content": build_system_prompt()}]  # after connect_all: the deferred list is complete
```

The prompt says which tools are deferred and how to load one. It is built
after the MCP servers have started, because their tools are the ones most
likely to be deferred. The eval runner builds its own prompt per workspace,
as in step 30, and gets the same section.

### 8. The usage line

`harness/ui.py`:

```python
    def usage(self, stats, estimate=None):
        """One line per model call. estimate is the harness's count of the prompt it sent."""
        for key, value in stats.items():
            self._totals[key] = self._totals.get(key, 0) + (value or 0)
        parts = []
        for key, value in stats.items():
            if key == "prompt_tokens" and estimate is not None:
                parts.append(f"{value:,} prompt (estimate {estimate:,})" if value else f"estimate {estimate:,} prompt")
            elif value:
                parts.append(f"{value:,} {key.replace('_tokens', '')}")
```

`12,340 prompt (estimate 11,900)` is the shape. With no real count, the
estimate stands alone. Subagents call `usage` with one argument, as before.

## Run it

```bash
pip install -e .
harness
> /context
```

A panel titled `context budget` shows eight rows. On a fresh session the
system prompt and the tool schemas are the largest bars and the total is a
few percent of the window. Ask for something, and the usage line under the
reply reads `1,234 prompt (estimate 1,300) · 56 completion`. Run a few
commands with long output and type `/context` again: the `tool results`
bar grows.

To see a deferred tool, configure an MCP server with a large schema in
`.agents/mcp.json`, or lower the line for one session:

```bash
DEFER_OVER=100 harness
> remember that I prefer tabs
```

With the line at 100 tokens the `remember` tool is a stub. The model calls
`load_tool` with `remember`, the result shows the full schema, and the next
call to `remember` runs. The system prompt lists the deferred names under
"Some tools are deferred".

Keep chatting past half the window and one note appears: `context window
51% full: ...`. It does not repeat. A second note appears at 75%.

Run the offline tests from the repository root:

```bash
python run_tests.py 32
python check_snippets.py 32
```

## What to notice

- The estimate and the real count sit side by side on purpose. Four
  characters to a token is wrong for code, JSON and other languages, and
  the usage line shows how wrong, every call.
- The breakdown counts what the next request will carry, not what the
  transcript holds. The tool schemas and the memory index are not in the
  message list, and they are the parts a user can do the least about.
- A stub is a real tool. The model is not told that a tool is missing; it
  is told the tool exists and how to enable it. A call to the stub is
  answered with the same advice, so a model that skips the prompt still
  gets there in one round trip.
- `active_schemas` composes with the other filters instead of replacing
  them. Plan mode, the subagent set and the browse set each choose their
  tools as before, and the deferral is applied to the result.
- The deferred check runs before the permission rules. A stub has no
  parameters, and a rule that reads an argument must never see a call
  without one.
- `LOADED` is session-wide. A tool loaded by the main agent is loaded for
  the subagents too, and the other way round, because a session has one
  registry.

## Diff from step 31

```bash
diff -r ../step_31_instruction_files/harness harness
```

Added: `budget.py` (`CATEGORIES`, `DEFER_OVER`, `THRESHOLDS`, `WARNED`,
`tokens`, `schema_tokens`, `part_of`, `breakdown`, `render`, `check`).
Changed: `tools.py` (`LOADED`, `LOAD_TOOL_SCHEMA`, `is_deferred`,
`deferred_names`, `stub`, `active_schemas`, `load_tool`, `load_first`,
`load_tool` in `TOOLS`, the `deferred` verdict in `decide` and `settle`),
`llm.py` (`DEFERRED_INTRO`, `deferred_section`, `build_system_prompt`
takes `schemas`, `call_llm` defaults to `active_schemas()`), `agent.py`
(the estimate, `ui.usage` with it, `budget.check`, the system prompt built
after `connect_all`), `ui.py` (`usage` takes `estimate`, `context`),
`commands.py` (`/context`), `plan.py` (`load_tool` in `READ_ONLY`),
`subagent.py` and `browse.py` (`toolset` through `active_schemas`),
`evaluate.py` (the usage recorder takes the estimate). Everything else is
unchanged from step 31.
