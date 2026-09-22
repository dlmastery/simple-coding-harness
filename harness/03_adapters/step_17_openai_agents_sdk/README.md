# Step 17 - The same harness on the OpenAI Agents SDK

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Separate the harness from its provider**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 16 - The same harness on the Claude Agent SDK](../step_16_claude_agent_sdk/README.md). Next: [Step 18 - The same harness on the Google Antigravity SDK](../step_18_google_antigravity_sdk/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** a general agent framework under a coding agent.
The SDK owns the loop, sessions, approvals and agents-as-tools. The coding
tools are ours again: the stage 5 functions come back verbatim and get
*wrapped* instead of hand-registered. The late injection and stripping
logic becomes one request filter.

`pip install openai-agents`. It works against any OpenAI-compatible endpoint
through `OpenAIChatCompletionsModel`, so the same `BASE_URL` / `API_KEY` /
`MODEL` as stages 1-15.

## Why

Step 16 handed everything to a vendor's coding agent. That is the most you
can delegate, and the least you can change: the tools are theirs, the prompt
preset is theirs. The other end of the range is a framework that knows
nothing about code. It gives you a loop, a session store, a pause-and-resume
for approvals and a way to nest agents, and leaves every tool to you.

Without this step you would not see which of the fifteen ideas are
*generic agent mechanics* (the loop, sessions, approvals, subagents) and
which are *coding-agent policy* (which commands run, what gets injected,
how output is trimmed). Here the split is exact: the SDK has the first
group, `harness.py` has the second, and the tools from stage 5 are copied
in unchanged.

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
| 11 | allow / ask / deny, timeouts | `tool_input_guardrails` (deny becomes the tool result), `needs_approval` (ask pauses the run: `result.interruptions`, `state.approve()`); the timeout is ours, in `run_command` | us (rules, timeout), SDK (mechanics) |
| 14 | cap / strip / fit / compaction | `cap` in the tools, `strip` in the filter; no built-in summariser (the SDK ships `ToolOutputTrimmer`, not a compaction agent) | us |
| 15 | `task` subagent | `explorer.as_tool(tool_name="task", max_turns=12, hooks=..., run_config=...)` - fresh run, own context, only `final_output` returns | SDK |

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
    # async so the SDK loop keeps serving hooks and approvals while it runs
    return await asyncio.to_thread(run_command, command)
```

The `Args:` section of the docstring becomes the parameter description.
The type hint becomes the JSON type. The function is async so the event
loop - which also serves approvals and hooks - is never blocked by a
running command. The command itself runs in `run_command`:

`harness.py`:

```python
def run_command(command):
    """The subprocess itself, with the timeout enforced here - the SDK's timeout
    only stops waiting; a child left running would keep a worker thread busy."""
    proc = subprocess.Popen(
        command, shell=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace", env=BASH_ENV, **NEW_GROUP,
    )
    try:
        out, err = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc.pid)
        proc.communicate()
        return f"Error: command timed out after {TIMEOUT}s"
    return cap((out + err) or "(no output)")
```

`function_tool` has a `timeout=` of its own, and the first version used it.
It stops *waiting* for the tool; it cannot stop a thread. A hung command
kept its worker thread, and after a few of them the thread pool was full and
the approval prompt - which also needs a thread - never appeared. So the
timeout lives with the process: a new process group, `kill_tree` on
expiry, and the result is an `Error:` string the model reads. `cap` is
stage 14's cap: ten thousand characters inline, the rest cut.

`harness.py`:

```python
bash = function_tool(_bash, name_override="bash", needs_approval=bash_needs_approval, tool_input_guardrails=[policy_gate])
read_file = function_tool(_read_file, name_override="read_file")
write_file = function_tool(_write_file, name_override="write_file", needs_approval=edit_needs_approval)
str_replace = function_tool(_str_replace, name_override="str_replace", needs_approval=edit_needs_approval)
read_skill = function_tool(_read_skill, name_override="read_skill")
write_todos = function_tool(_write_todos, name_override="write_todos")
```

Registration is decoration. This replaces the `TOOLS` dict and `schema()`
of stage 2.2. Policy hangs off the same call: a guardrail for structural
denies and a predicate for asks. The tool bodies, the skill loader and the
todo list are still ours. The SDK has no coding tools of its own.

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
table is ours. The SDK owns where in the call each check runs: the
predicate first, the guardrail after an approval, so a `deny` never asks.

### 3. Approval is a pause, not a callback

Stage 11 prompted inline, inside the tool loop. Here the SDK primitive is
the interruption. When `needs_approval` returns true the run stops and
`result.interruptions` lists the pending calls.

`harness.py`:

```python
async def turn(agent, session, text, hooks, config):
    """One user message. Approvals pause the run; we answer and resume it.

    Nothing raises past here: a model that never stops (MaxTurnsExceeded), broken
    tool JSON (ModelBehaviorError) or a dead endpoint end the turn with one line.
    """
    try:
        result = await Runner.run(agent, text, session=session, hooks=hooks, run_config=config, max_turns=40)
        while result.interruptions:
            state = result.to_state()
            for item in result.interruptions:
                if await asyncio.to_thread(confirm, f"{item.name} {item.arguments}"):
                    state.approve(item)
                else:
                    state.reject(item, rejection_message="The user declined this tool call.")
            result = await Runner.run(agent, state, session=session, hooks=hooks, run_config=config, max_turns=40)
    except AgentsException as failure:
        return f"(turn stopped: {type(failure).__name__}: {failure})"
    except Exception as failure:  # noqa: BLE001 - openai.APIError and friends: the endpoint, not us
        return f"(model call failed: {type(failure).__name__}: {failure})"
    return result.final_output
```

`Runner.run` is the loop of stage 2.4. `to_state()` freezes the run. We
approve or reject each item on that state and pass it back to `Runner.run`
to continue. The state serialises, so the approval could happen in another
process. That is the design difference from the inline prompt of stage 11.
The `confirm` function and the loop around interruptions are ours, and so
is the rule that a turn ends with a line, never a traceback.

### 4. A subagent is an agent used as a tool

Stage 15 wrote a second loop with fewer tools and returned only its report.
The SDK primitive is `Agent.as_tool()`.

`harness.py`:

```python
explorer = Agent(name="explorer", instructions=SUBAGENT_PROMPT, tools=[bash, read_file, read_skill], model_settings=ModelSettings())
# A nested run inherits nothing we do not pass: without hooks= its tool calls
# are invisible, and without run_config= it would inherit the parent's filter.
task = explorer.as_tool(
    tool_name="task",
    tool_description=(
        "Hand a self-contained exploration question to a fresh agent with its own "
        "context window and get back its findings. It cannot see this conversation; "
        "include every detail it needs. It reads and reports; it never edits."
    ),
    max_turns=12,
    hooks=CONSOLE,
    run_config=RunConfig(call_model_input_filter=shape_subagent_request),
)
```

The four rules of stage 15 are arguments. The explorer has its own tool
list with no `write_file` and no `task`, so it cannot edit and cannot
recurse. Each call is a fresh run with its own context. `max_turns` is the
cap. Only `final_output` crosses back. The empty `ModelSettings()` is
explained in the caveats below.

Two arguments are easy to leave out, and the first version did. A nested
run gets no hooks unless `hooks=` names them, so the explorer's tool calls
printed nothing. And when `run_config=` is missing the nested run inherits
the parent's, filter included - so the explorer received the main agent's
`<todos>` and file notes, and consumed the file-change diff meant for the
main agent. `shape_subagent_request` gives it the strip and nothing else.

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
    items = strip(data.model_data.input)
    # A system item, not a user message: when a run resumes after an approval
    # the reminder is the newest thing in the list, and as a user message the
    # model answers it instead of finishing the task it was approved for.
    items.append({"role": "system", "content": "Automated context, not a message from the user. Continue the current task.\n" + reminder()})
    return ModelInputData(input=items, instructions=data.model_data.instructions)
```

`strip` is stage 14's strip on a copy of the list: old tool outputs shrink
to a stub, the newest three stay whole. The last line is the late injection
of stage 6. `reminder()` builds the `<env>` block, the `<todos>` block of
stage 10 and the changed-files note of stage 7. The session on disk never
sees any of it. That is the request-versus-record split the hand-built
harness enforced by hand. The filter body is entirely ours. The SDK only
promises to call it - before *every* model call: the first one, the one
after an approval resumes the run, and, had we not given it its own, the
explorer's.

That last point has a consequence for side effects. The filter runs before
the request goes out, so anything it changes is changed even if the request
then fails. The file-change note used to move its baseline when it was
built; a rate-limited call lost the note for good.

`harness.py`:

```python
def changes_note():
    """Pure: computes the diff and remembers what it was against. mark_seen() commits it,
    so a request that fails after the filter ran does not lose the note."""
    global PENDING
    now = git_state()
    changed = {p: v[0] for p, v in now.items() if LAST.get(p) != v}
    PENDING = now
    if not changed:
        return ""
    lines = "\n".join(f"{LABELS.get(c, c)}: {p}" for p, c in changed.items())
    return f"\n<system-reminder>\nThese files changed since your last turn. Read them again before editing:\n{lines}\n</system-reminder>"


def mark_seen():
    global LAST, PENDING
    if PENDING is not None:
        LAST, PENDING = PENDING, None
```

`mark_seen()` is called from `on_llm_end`, which only fires once the model
has answered. A filter should compute; a hook should commit.

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
        if agent.name == "harness":
            mark_seen()  # the model saw the reminder; only now does the file baseline move
```

The agent name tells us whether a call belongs to the subagent, so the
indent of stage 15 is one comparison - provided the same `Console` instance
is handed to the nested run, which `CONSOLE` in `as_tool(hooks=...)` does.
`on_llm_end` carries the usage. The SDK fires the events. Every line
printed is ours.

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
The in-memory todo list is not rewound with the session; the next
`write_todos` replaces it anyway.

## Run it

Prerequisites: Python 3.10+, `pip install openai-agents` (brings `openai`),
and an OpenAI-compatible endpoint. Tracing is switched off in the file, so
no OpenAI account is needed for a third-party endpoint.

bash:

```bash
pip install openai-agents
export BASE_URL=https://openrouter.ai/api/v1 API_KEY=sk-or-... MODEL=openai/gpt-4.1-mini
python harness.py
```

PowerShell:

```powershell
pip install openai-agents
$env:BASE_URL = "https://openrouter.ai/api/v1"; $env:API_KEY = "sk-or-..."; $env:MODEL = "openai/gpt-4.1-mini"
python harness.py
```

Then:

```text
> use the task tool to find where approvals are handled, then add a comment there
> /rewind
```

### Expected output

```text
  simple coding harness · openai agents sdk · session 20260918-104201-3f9a1c · /sessions, /rewind
  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> use the task tool to find where approvals are handled, then add a comment there
  2,214 in · 41 out
  tool> task {"input": "In harness.py, find where tool approvals are handled…"}
      subagent · own context
        tool> bash {"command": "grep -n approve harness.py"}
              362:                    state.approve(item) / 358:async def turn(agent, …
  1,180 in · 62 out
        Approvals are handled in turn() at harness.py:358-366 …
  2,431 in · 88 out
  tool> str_replace {"path": "harness.py", "old_str": "async def turn(", "new_str": "# approvals…
        Replaced 1 occurrence(s) in harness.py
  2,602 in · 35 out

  agent> Added a comment above turn() explaining the interruption loop.
```

Indented lines are the explorer's. A command the rules rate as `ask` pauses
the run with `bash {"command": "python x.py"}` / `allow? (y/n)>`; `n` sends
`The user declined this tool call.` back to the model.

Offline tests: `python -m pytest test_step.py` (tools including the timeout
and UTF-8 round trip, policy, the two filters, the change-note baseline,
`turn()`'s error path, rewind on a real `SQLiteSession`).

## Error handling

- **A bad tool call.** `function_tool` validates the arguments against the
  schema; broken JSON or a missing argument becomes an error result the
  model reads. An exception inside a tool (a missing file, say) is turned
  into a result by the SDK's default `failure_error_function`.
- **A failing command.** stdout and stderr come back whatever the exit
  code; after 60 seconds the process group is killed and the result is
  `Error: command timed out after 60s`; output over 10,000 characters is
  capped.
- **A denied call.** The guardrail's `Blocked by policy: ...` or the
  rejection message is the tool result.
- **A dead model call, a runaway model.** `turn()` returns
  `(model call failed: ...)` or `(turn stopped: MaxTurnsExceeded: ...)` and
  the prompt is back. The SDK drops unanswered tool calls from the stored
  session on the next run, so the transcript stays valid.
- **ctrl-c at the approval prompt** answers no. **ctrl-c while the model
  runs** ends the harness with `interrupted` (the SDK's loop does not catch
  it, the entry point does); start again with `--resume` and the session
  picks up.
- **Leaving.** `/exit`, ctrl-d (ctrl-z then enter on Windows) or ctrl-c at
  the prompt. An empty line does nothing.

## Gotchas / what this is not

- **Inject as `system`, not `user`.** The first version appended the late
  block as a user message. After an approval pause the run resumes with
  that block as the newest item, and the model answered it instead of
  finishing the approved tool call. As a `system` item it is context, not
  a turn. Some OpenAI-compatible endpoints reject a system message that is
  not the first message (Mistral, some vLLM templates); for those, use
  `"role": "developer"` or a user item whose text starts with "Automated
  context".
- **Give the subagent explicit `ModelSettings()`.** An `Agent` built
  without a model assumes the SDK default (GPT-5) and pre-fills
  `verbosity="low"` / `reasoning=none`; assigning a model later does not
  reset them, and `gpt-4.1-mini` rejects `verbosity` with a 400. The
  explorer also needs the same model bound, or its nested run falls back
  to the default client and `OPENAI_API_KEY`.
- **Give the subagent its own `hooks=` and `run_config=`** (section 4).
- The tool named `bash` runs through `cmd.exe` on Windows and `/bin/sh`
  elsewhere. No sandbox on any platform in this step.
- Coding tools, skills, a compaction agent, and any opinion about the
  screen: none of it is the SDK's. It is a general agent framework. The
  "coding" in coding agent is still your tools and your prompt.

## What the next step adds

Step 18 rebuilds the harness on the Google Antigravity SDK, where the whole
runtime, coding tools included, lives in a binary that Python configures.
