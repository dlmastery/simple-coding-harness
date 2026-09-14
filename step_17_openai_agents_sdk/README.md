# Step 17 - The same harness on the OpenAI Agents SDK

**What this step adds:** the SDK owns the loop, sessions, approvals and
agents-as-tools. The coding tools are ours again. The stage 5 functions come
back verbatim and get *wrapped* instead of hand-registered. The late
injection and stripping logic becomes one request filter.

`pip install openai-agents`. It works against any OpenAI-compatible endpoint
through `OpenAIChatCompletionsModel`, so the same `BASE_URL` / `API_KEY` /
`MODEL` as stages 1-15.

## Files

```text
step_17_openai_agents_sdk/
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill, read by our read_skill tool
├── harness.py         Runner, SQLiteSession, wrapped stage 5 tools, approvals, the REPL
├── rules.py           the stage 11 allow / ask / deny table, unchanged
└── test_step.py       offline tests; the Runner is never invoked
```

## Concept map

| Step | We built | OpenAI Agents SDK | Who writes it now |
|-----:|----------|-------------------|-------------------|
| 1-2.4 | the two loops, `as_dict`, tool-result ids | `Runner.run(agent, input, session=...)` | SDK |
| 2.1-2.2, 5 | `bash`, `read_file`, `write_file`, `str_replace`, registry, `schema()` | `function_tool(fn)`: schema from the signature and docstring; errors become results | us (functions), SDK (schema, registry) |
| 3 | rich UI, usage | `RunHooks` (`on_tool_start`, `on_tool_end`, `on_llm_end` with `response.usage`) | us (`Console`) |
| 4 | skills | not an SDK concept; `read_skill` tool + index in `instructions` | us, unchanged |
| 6 | late-injected `<env>` | `RunConfig(call_model_input_filter=...)` appends to the request, never to the session | us (`shape_request`) |
| 7 | file freshness | same filter, same git hash diff | us |
| 8 | JSONL sessions, `/rewind` | `SQLiteSession(id, db_path)`; `session.pop_item()` for rewind | SDK; we wire `--resume`, `/sessions`, `/rewind` |
| 10 | `write_todos`, re-injected plan | `write_todos` tool with a `TypedDict` schema; re-injected by the filter | us |
| 11 | allow / ask / deny, timeouts | `tool_input_guardrails` (deny becomes the tool result), `needs_approval` (ask pauses the run: `result.interruptions`, `state.approve()`), `timeout=60` on the tool | us (rules), SDK (mechanics) |
| 14 | cap / strip / fit / compaction | strip in the filter; no built-in summariser (the SDK has session trimming settings, not a compaction agent) | us |
| 15 | `task` subagent | `explorer.as_tool(tool_name="task", max_turns=12)` - fresh run, own context, only `final_output` returns | SDK |

## The code, piece by piece

### 1. Tools are plain functions, wrapped

Stage 5 wrote each tool twice: the function and a schema dict. The SDK
primitive is `function_tool`. It reads the signature and the docstring and
builds the schema itself.

`harness.py`:

```python
async def _bash(command: str) -> str:
    """Run a shell command and return its stdout and stderr.

    Args:
        command: The command to run.
    """
    # async so the SDK can enforce `timeout=` on it (sync handlers cannot be timed out)
    result = await asyncio.to_thread(subprocess.run, command, shell=True, capture_output=True, text=True)
    return (result.stdout + result.stderr) or "(no output)"
```

The `Args:` section of the docstring becomes the parameter description.
The type hint becomes the JSON type. The function is async for one reason:
the SDK can only time out an async handler.

`harness.py`:

```python
bash = function_tool(_bash, name_override="bash", needs_approval=bash_needs_approval, tool_input_guardrails=[policy_gate], timeout=60)
read_file = function_tool(_read_file, name_override="read_file")
write_file = function_tool(_write_file, name_override="write_file", needs_approval=edit_needs_approval)
str_replace = function_tool(_str_replace, name_override="str_replace", needs_approval=edit_needs_approval)
read_skill = function_tool(_read_skill, name_override="read_skill")
write_todos = function_tool(_write_todos, name_override="write_todos")
```

Registration is decoration. This replaces the `TOOLS` dict and `schema()`
of stage 2.2. Policy hangs off the same call: a guardrail for structural
denies, a predicate for asks, and a timeout that turns a hang into a
result. The tool bodies, the skill loader and the todo list are still ours.
The SDK has no coding tools of its own.

### 2. Deny is a guardrail, ask is a predicate

Stage 11 made one decision per call inside `execute()`. The SDK splits it
into two primitives. A `tool_input_guardrail` runs before the tool and can
reject. A `needs_approval` predicate decides whether the run must pause.

`harness.py`:

```python
@tool_input_guardrail
def policy_gate(data: ToolInputGuardrailData):
    """Runs before the tool. A rejection becomes the tool's result - the model reads it."""
    raw = data.context.tool_arguments
    args = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
    verdict, reason = verdict_for(data.context.tool_name, args)
    if verdict == "deny":
        return ToolGuardrailFunctionOutput.reject_content(f"Blocked by policy: {reason}")
    return ToolGuardrailFunctionOutput.allow()
```

```python
async def bash_needs_approval(ctx, params, call_id) -> bool:
    return rules.check_bash(params.get("command", ""))[0] == "ask"


async def edit_needs_approval(ctx, params, call_id) -> bool:
    return rules.check_edit(params.get("path", ""))[0] == "ask"
```

`reject_content` makes the reason the tool result, so the model reads it
and moves on. This is the "errors as results" rule of stage 5 applied to
policy. Both functions call the same `rules.py` as stage 11. The verdict
table is ours. The SDK owns where in the call each check runs.

### 3. Approval is a pause, not a callback

Stage 11 prompted inline, inside the tool loop. Here the SDK primitive is
the interruption. When `needs_approval` returns true the run stops and
`result.interruptions` lists the pending calls.

`harness.py`:

```python
async def turn(agent, session, text, hooks, config):
    """One user message. Approvals pause the run; we answer and resume it."""
    result = await Runner.run(agent, text, session=session, hooks=hooks, run_config=config, max_turns=40)
    while result.interruptions:
        state = result.to_state()
        for item in result.interruptions:
            if await asyncio.to_thread(confirm, f"{item.name} {item.arguments}"):
                state.approve(item)
            else:
                state.reject(item, rejection_message="The user declined this tool call.")
        result = await Runner.run(agent, state, session=session, hooks=hooks, run_config=config, max_turns=40)
    return result.final_output
```

`Runner.run` is the loop of stage 2.4. `to_state()` freezes the run. We
approve or reject each item on that state and pass it back to `Runner.run`
to continue. The state serialises, so the approval could happen in another
process. That is the design difference from the inline prompt of stage 11.
The `confirm` function and the loop around interruptions are ours.

### 4. A subagent is an agent used as a tool

Stage 15 wrote a second loop with fewer tools and returned only its report.
The SDK primitive is `Agent.as_tool()`.

`harness.py`:

```python
explorer = Agent(name="explorer", instructions=SUBAGENT_PROMPT, tools=[bash, read_file, read_skill], model_settings=ModelSettings())
task = explorer.as_tool(
    tool_name="task",
    tool_description=(
        "Hand a self-contained exploration question to a fresh agent with its own "
        "context window and get back its findings. It cannot see this conversation; "
        "include every detail it needs. It reads and reports; it never edits."
    ),
    max_turns=12,
)
```

The four rules of stage 15 are arguments. The explorer has its own tool
list with no `write_file` and no `task`, so it cannot edit and cannot
recurse. Each call is a fresh run with its own context. `max_turns` is the
cap. Only `final_output` crosses back. The empty `ModelSettings()` is
explained in the caveats below.

### 5. One filter shapes every request

Stages 6, 7, 10 and 14 each touched the messages list in a different place.
The SDK primitive is `call_model_input_filter`. It sees a copy of the model
input on every call and returns what goes on the wire.

`harness.py`:

```python
def shape_request(data: CallModelData) -> ModelInputData:
    """call_model_input_filter: runs on every model call, sees a copy of the input.

    Two jobs from the hand-built harness, in one place:
      strip - older tool outputs shrink to a stub (step 14)
      inject - the late block goes on the end, and only on the wire (step 6)
    The session on disk is untouched; this is the request, not the record.
    """
    items = [dict(item) for item in data.model_data.input]
    outputs = [item for item in items if item.get("type") == "function_call_output"]
    for item in outputs[:-KEEP_FULL]:
        out = item.get("output")
        if isinstance(out, str) and len(out) > STUB:
            item["output"] = out[:STUB] + f"\n[output trimmed: {len(out) - STUB} more chars. Run the command again if you need them.]"
    # A system item, not a user message: when a run resumes after an approval
    # the reminder is the newest thing in the list, and as a user message the
    # model answers it instead of finishing the task it was approved for.
    items.append({"role": "system", "content": "Automated context, not a message from the user. Continue the current task.\n" + reminder()})
    return ModelInputData(input=items, instructions=data.model_data.instructions)
```

The first loop is `strip` from stage 14: old tool outputs shrink to a stub,
the newest three stay whole. The last line is the late injection of stage
6. `reminder()` builds the `<env>` block, the `<todos>` block of stage 10
and the changed-files note of stage 7. The session on disk never sees any
of it. That is the request-versus-record split the hand-built harness
enforced by hand. The filter body is entirely ours. The SDK only promises
to call it.

### 6. Presentation is a hooks subclass

Stage 3 drew each tool call and a usage line. The SDK primitive is
`RunHooks`: a class with one method per event.

`harness.py`:

```python
class Console(RunHooks):
    async def on_agent_start(self, context, agent):
        if agent.name == "explorer":
            print("      subagent · own context")

    async def on_tool_start(self, context, agent, tool):
        pad = "        " if agent.name == "explorer" else "  "
        args = getattr(context, "tool_arguments", None) or getattr(context, "tool_input", None)
        print(f"{pad}tool> {tool.name} {str(args or '')[:90]}")

    async def on_tool_end(self, context, agent, tool, result):
        pad = "        " if agent.name == "explorer" else "  "
        first = str(result).strip().splitlines()[:3]
        print(pad + "      " + (" / ".join(first)[:120] or "(no output)"))

    async def on_llm_end(self, context, agent, response):
        u = getattr(response, "usage", None)
        if u:
            print(f"  {u.input_tokens:,} in · {u.output_tokens:,} out")
```

The agent name tells us whether a call belongs to the subagent, so the
indent of stage 15 is one comparison. `on_llm_end` carries the usage. The
SDK fires the events. Every line printed is ours.

### 7. Sessions are SQLite rows; rewind pops them

Stage 8 wrote JSONL sessions and a `/rewind` that truncated the file. The
SDK primitive is `SQLiteSession`, and `pop_item()` removes the newest row.

`harness.py`:

```python
async def rewind(session):
    """Pop items until a user message goes: one whole turn undone."""
    popped = 0
    while True:
        item = await session.pop_item()
        if item is None:
            break
        popped += 1
        if item.get("role") == "user":
            break
    return popped
```

One turn is everything back to and including the last user message, so we
pop until one goes. The SDK stores and returns items. The definition of a
turn is ours. `last_session_id` and `all_session_ids` read the same
database directly to list sessions, because the SDK has no listing call.

## Run it

```bash
pip install openai-agents
export BASE_URL=... API_KEY=... MODEL=...
python harness.py
you> use the task tool to find where approvals are handled, then add a comment there
you> /rewind
```

Offline tests: `python -m pytest test_step.py` (tools, policy, the request
filter, rewind on a real `SQLiteSession`).

## Two things the live run taught

- **Inject as `system`, not `user`.** The first version appended the late
  block as a user message. After an approval pause the run resumes with
  that block as the newest item, and the model answered it instead of
  finishing the approved tool call. As a `system` item it is context, not
  a turn.
- **Give the subagent explicit `ModelSettings()`.** An `Agent` built
  without a model assumes the SDK default (GPT-5) and pre-fills
  `verbosity="low"` / `reasoning=none`; assigning a model later does not
  reset them, and `gpt-4.1-mini` rejects `verbosity` with a 400. The
  explorer also needs the same model bound, or its nested run falls back
  to the default client and `OPENAI_API_KEY`.

## What the SDK does not give you

Coding tools, skills, a compaction agent, and any opinion about the screen.
It is a general agent framework. The "coding" in coding agent is still your
tools and your prompt.
