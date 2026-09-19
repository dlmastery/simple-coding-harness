# Step 32 - Context budget

**What this step adds:** a view of where the context window goes, and one
way to spend less of it. `budget.breakdown` estimates the tokens of the
next request in eight categories: system prompt, instruction files, skills
index, memory index, tool schemas, transcript text, tool results and
images. `/context` draws one bar per category and the share of the window
in use. The usage line prints the real prompt count next to the estimate.
A note warns at 50% and at 75% of the window, once each per session. A
tool whose schema is over 300 tokens is deferred: it goes out as a
one-line stub until the model calls `load_tool` with its name. With the
shipped registry nothing crosses that line (the largest built-in, `task`,
is 298 tokens); the mechanism is there for MCP tools and for a lower
`DEFER_OVER`.

## Files

```text
step_32_context_budget/
├── harness/
│   ├── llm.py                        the model call; lists the deferred tools, offers active_schemas()
│   ├── tools.py                      the registry; deferred tools, load_tool(), active_schemas()
│   ├── agent.py                      the loop; measures each request, warns at 50% and 75%
│   ├── budget.py                     the context budget: breakdown(), render(), check()
│   ├── plan.py                       plan mode; load_tool joins the read-only tools
│   ├── commands.py                   slash commands; /context draws one bar per category
│   ├── evaluate.py                   the eval harness; the usage recorder takes the estimate
│   ├── instructions.py               finds AGENTS.md / CLAUDE.md from home and git root down
│   ├── jobs.py                       background jobs: Popen through the sandbox, a job table, kill_all
│   ├── subagent.py                   the subagent loop; task runs one subagent per description
│   ├── permissions.py                allow / ask / deny; a job is rated by the bash rules
│   ├── context.py                    the late injection block, with a <jobs> tag
│   ├── hooks.py                      hooks: reads hooks.json, runs commands and functions per event
│   ├── mcp_client.py                 MCP client: starts each server over stdio, registers its tools
│   ├── memory.py                     persistent memory: markdown files with front matter
│   ├── compact.py                    the compaction agent; its handoff note is kept
│   ├── history.py                    transcript trimming: cap, strip, fit, image messages
│   ├── browse.py                     the browser subagent
│   ├── browser.py                    browser tools: one Chromium page through Playwright
│   ├── computer.py                   computer use: screen size, screenshot, act
│   ├── todos.py                      the plan: write_todos and the todo list
│   ├── skills.py                     skills: SKILL.md discovery and index
│   ├── session.py                    append-only JSONL log, load(), /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash
│   ├── config.py                     settings: environment first, ~/.simple-harness/env fills gaps
│   ├── prompt.py                     the input line, through prompt_toolkit
│   ├── ui.py                         rich panels; usage() shows the estimate, context() the breakdown
│   └── __init__.py                   package marker
├── .agents/
│   ├── hooks.json                    hook config: block .env writes, log every tool name
│   ├── block_env_writes.py           example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: appends every tool name to a log
│   ├── .gitignore                    ignores tool_log.txt, the log hook's output
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── evals/                            one folder per task: task.md, a checker, optional workspace/
├── AGENTS.md                         the project instruction file the harness reads at start
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.32.0
└── README.md                         this file
```

## Why a budget, and what breaks without one

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

### What breaks without it

Connect an MCP server that exposes forty tools with verbose schemas and
every request carries 30,000 tokens of JSON before the conversation
starts. The usage line reads `31,400 prompt` from the first turn, the
window fills in a fraction of the turns it used to, `/compact` fires early
and often, and nothing on screen says why, because the tool schemas are
not in the transcript and not on the screen. The breakdown names the
cost; the stub removes most of it until the tool is wanted.

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
    instructions = part_of(system, render(LOADED))  # the files the prompt was built from; no new discovery here
    skills = part_of(system, skills_prompt())

    text = results = images = 0
    for message in rest:
        content = message.get("content")
        if isinstance(content, list):
            images += IMAGE_TOKENS * sum(1 for part in content if part.get("type") == "image_url")
            text += sum(tokens(part.get("text", "")) for part in content)
        elif message.get("role") == "tool":
            results += tokens(json.dumps(message, ensure_ascii=False))  # as sent: a non-ASCII char is not six
        else:
            text += tokens(json.dumps(message, ensure_ascii=False))

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
"system prompt" is what remains. The instruction text is rendered from
`instructions.LOADED`, the files the prompt was built from, so the
breakdown never discovers files again and never counts a file the model
does not have. `part_of` counts a piece only when it is inside the prompt,
so a workspace without instruction files reports zero. The memory index
and the tool schemas are not in `messages` at all. They are added to every
request, so they are counted from their sources. The estimate for a
picture is the flat `IMAGE_TOKENS` from step 24. Messages are measured as
the JSON the request carries, with `ensure_ascii=False` so a line of
box-drawing or CJK text counts as its characters, not as six ASCII
characters each.

What the estimate leaves out: the late injection block from step 12 (the
todo list, the plan, the jobs, the hook context and the git changes, built
after the estimate is taken), the plan-mode prompt, and the difference
between `active_schemas()` and the tool set of the mode. On a plain turn
in act mode the difference is a few hundred tokens; the usage line shows
the real count beside the estimate, so the gap is visible every call.

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
        schemas = active_schemas(plan.toolset())
        allowed = {s["function"]["name"] for s in schemas}  # what the model was offered is all it may run
        estimate = budget.breakdown(messages)["total"]  # what this request should cost
        with spinner:
            try:
                message, usage = call_llm(with_mode(messages) + [injection], tools=schemas, on_delta=on_delta)
            except openai.APIError as failed:
                if streamed:
                    ui.stream_end()  # a stream that broke may have shown part of a reply
                ui.note(f"model call failed: {failed}")  # the user message stays; the transcript is still valid
                break
        calls += 1
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
way to the wire. The names in that list are also the names the model may
run this call (`allowed`, from step 15's rule that the offered set is the
runnable set): a stub is in the list, so a call to it is answered by the
deferral advice below, not by a permission verdict.

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
            STUBBED[schema["function"]["name"]] = schema  # so load_tool finds it, wherever the schema came from
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

`STUBBED` is the contract between the two halves. `submit_plan` lives in
`plan.py` and the `browser_*` schemas in `browser.py`; neither is in
`TOOL_SCHEMAS`, yet plan mode and the browse subagent pass them through
`active_schemas`. Every stub is recorded where it is made, under its name,
so `load_tool` can find the full schema whatever list it came from.

### 5. Loading a tool

`harness/tools.py`:

```python
def load_tool(name: str) -> str:
    ...
    schema = STUBBED.get(name) or next((s for s in TOOL_SCHEMAS if s["function"]["name"] == name), None)
    if schema is None:
        return f"Error: no tool named {name!r}."
    if not is_deferred(schema):
        return f"{name} is not deferred; call it directly."
    LOADED.add(name)
    return f"{name} is enabled for the rest of the session. Its schema:\n" + json.dumps(schema["function"], indent=2)


def load_first(name):
    """The result for a call to a deferred tool that was not loaded, or None."""
    if name in LOADED or (name not in STUBBED and name not in deferred_names()):
        return None
    return f"Error: {name} is deferred. Call load_tool('{name}') first, then call {name} again with its full arguments."
```

`LOADED` is a set of names that lasts for the process. Once a name is in
it, `active_schemas` sends the full schema on every later call. The
schema comes back in the tool result too, so the model has it in the
transcript at once, before the next request offers it in full.

`harness/tools.py`:

```python
def relearn(messages):
    ...
    LOADED.clear()
    results = {m.get("tool_call_id"): m.get("content") or "" for m in messages if m.get("role") == "tool"}
    for message in messages:
        for call in message.get("tool_calls") or []:
            if call["function"]["name"] != "load_tool":
                continue
            try:
                name = json.loads(call["function"]["arguments"]).get("name")
            except (ValueError, AttributeError):
                continue
            if name and results.get(call["id"], "").startswith(f"{name} is enabled"):
                LOADED.add(name)
    return LOADED
```

The set lives in memory, but the transcript still shows the model the
schema it loaded. After `--resume`, `/sessions` or `/rewind` the set is
rebuilt from the `load_tool` results the transcript holds, so the model is
not told to load a tool it can see it has loaded, and a tool loaded in a
turn that `/rewind` cut away is deferred again. The eval runner clears the
set per task.

### 6. A call to a stub

`harness/tools.py`:

```python
    advice = load_first(name)
    if advice is not None:
        return args, "deferred", advice
    action, reason = check(name, args)
```

The check sits in `decide`, after the argument parsing and the name
checks and ahead of the permission rules. A stub has no parameters, so a
call to it arrives with empty arguments, and a rule that reads
`args["command"]` would fail on it. The `deferred` verdict never runs,
never asks, and never reaches a hook; `settle` turns it into the advice as
the tool result. In plan mode this means a deferred write tool is answered
"load it first" rather than "not available in plan mode"; loading it is
allowed (`load_tool` is read-only), and the call after that is denied by
the mode as usual.

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

Prerequisites: as step 31. `DEFER_OVER` in the environment lowers the
deferral line for one session.

bash:

```bash
pip install -e .
harness
> /context
```

PowerShell:

```powershell
pip install -e .
harness
> /context
```

### Expected output

A fresh session in this directory, before the first question:

```text
> /context

  context budget
  system prompt         1,193  ##################
  instruction files       474  #######
  skills index            247  ####
  memory index              0
  tool schemas          2,029  ##############################
  transcript text           0
  tool results              0
  images                    0
  total                 3,943  3% of the 128,000 token window
```

The tool schemas are the largest bar on a fresh session, and the total is
a few percent of the window. Ask for something, and the usage line under
the reply reads `4,120 prompt (estimate 3,960) · 56 completion`. Run a few
commands with long output and type `/context` again: the `tool results`
bar grows.

With the line at 300 no built-in tool is deferred: the largest schema,
`task`, is 298 tokens, then `remember` at 226 and `computer_act` at 214.
To see a deferred tool, configure an MCP server with a large schema in
`.agents/mcp.json`, or lower the line for one session:

```bash
DEFER_OVER=100 harness
> remember that I prefer tabs
```

```powershell
$env:DEFER_OVER = "100"; harness
> remember that I prefer tabs
```

```text
  load_tool: name=remember
  remember is enabled for the rest of the session. Its schema:
  {
    "name": "remember",
    ...
  remember: name=editor-preference ...
  Remembered editor-preference.
```

With the line at 100 tokens `remember`, `task`, `computer_act`,
`write_todos`, `browse` and `str_replace` are stubs. The model calls
`load_tool` with `remember`, the result shows the full schema, and the
next call to `remember` runs. The system prompt lists the deferred names
under "Some tools are deferred". At 100 the plan-mode `submit_plan` (174
tokens) and the browse subagent's `browser_type` (111) are stubs too, and
load the same way.

Keep chatting past half the window and one note appears: `context window
51% full: ...`. It does not repeat until a `/compact` has freed the
window. A second note appears at 75%.

Run the offline tests from the repository root:

```bash
python run_tests.py 32
python check_snippets.py 32
```

## Error handling

The guards of step 31 (one tool message per call, `Error:` strings for a
bad tool call, a note for a dead model call, ctrl-c, `/exit`) are
unchanged. New in this step:

- **A call to a stub.** `Error: remember is deferred. Call
  load_tool('remember') first, then call remember again with its full
  arguments.` The call does not run, does not prompt and does not reach a
  hook.
- **`load_tool` with a name that is not a tool.** `Error: no tool named
  'x'.`; with a tool that is not deferred: `x is not deferred; call it
  directly.` Both are results, not exceptions.
- **A model that reports no usage.** `budget.check` is given the estimate
  instead, so the warnings still fire; the usage line reads
  `estimate 3,960 prompt`.
- **An empty transcript or a fake model in tests.** `breakdown` accepts a
  list without a system message; every category is then zero except the
  schemas and the memory index.

## Gotchas / What this is not

- **At 300, nothing built-in is deferred.** The line sits just above
  `task` (298 tokens) on purpose: `task` is the tool plan mode relies on,
  and a stub for it would cost a round trip on the first exploration of
  every session. Two more characters in its description would flip it;
  the test suite pins the shipped sizes. The mechanism earns its keep with
  MCP tools, whose schemas the harness does not control.
- **The estimate is four characters to a token.** Wrong for code, JSON and
  most languages other than English, in both directions. The usage line
  shows the real count next to it; a drift is information, not a bug to
  hide.
- **The estimate leaves things out.** The late block, the plan-mode
  prompt and the per-mode tool set (see section 1). It is a view of the
  stable parts of the request, not a bill.
- **`LOADED` is per process.** It is rebuilt from the transcript on
  `--resume`, `/sessions` and `/rewind`, and cleared per eval task. It is
  shared by the main agent and every subagent, because a session has one
  registry: a tool the main agent loaded is loaded for a subagent too.
- **The warnings fire once per compaction, not once per session.**
  `/compact` clears `WARNED`, so the 50% and 75% notes come back as the
  window fills again.
- **The deferred check runs before the permission rules.** A stub has no
  parameters, and a rule that reads an argument must never see a call
  without one. In plan mode this puts "load it first" ahead of "not
  available in plan mode" for a deferred write tool; the mode still
  denies the loaded call.
- **Not a tokenizer.** No model-specific counting, no cache accounting.
  The provider's usage report is the truth; this is the map that says
  where to look.

## What to notice

- The estimate and the real count sit side by side on purpose. Four
  characters to a token is wrong for code, JSON and other languages, and
  the usage line shows how wrong, every call.
- The breakdown counts the stable parts of the next request, not what the
  transcript holds. The tool schemas and the memory index are not in the
  message list, and they are the parts a user can do the least about.
- A stub is a real tool. The model is not told that a tool is missing; it
  is told the tool exists and how to enable it. A call to the stub is
  answered with the same advice, so a model that skips the prompt still
  gets there in one round trip.
- `active_schemas` composes with the other filters instead of replacing
  them. Plan mode, the subagent set and the browse set each choose their
  tools as before, the deferral is applied to the result, and `STUBBED`
  makes every stub loadable whichever list it came from.
- The deferred check runs before the permission rules. A stub has no
  parameters, and a rule that reads an argument must never see a call
  without one.
- `LOADED` is one set for the process. A tool loaded by the main agent is
  loaded for the subagents too, and the other way round, because a session
  has one registry; `relearn` rebuilds it from the transcript whenever a
  transcript is opened or cut.

## Diff from step 31

```bash
diff -r ../step_31_instruction_files/harness harness
```

Added: `budget.py` (`CATEGORIES`, `DEFER_OVER`, `THRESHOLDS`, `WARNED`,
`tokens`, `schema_tokens`, `part_of`, `breakdown`, `render`, `check`).
Changed: `tools.py` (`LOADED`, `LOAD_TOOL_SCHEMA`, `is_deferred`,
`STUBBED`, `deferred_names`, `stub`, `active_schemas`, `load_tool`, `load_first`, `relearn`,
`load_tool` in `TOOLS`, the `deferred` verdict in `decide` and `settle`),
`llm.py` (`DEFERRED_INTRO`, `deferred_section`, `build_system_prompt`
takes `schemas`, `call_llm` defaults to `active_schemas()`), `agent.py`
(the estimate, `ui.usage` with it, `budget.check`, the system prompt built
after `connect_all`), `ui.py` (`usage` takes `estimate`, `context`),
`commands.py` (`/context`, `WARNED` cleared by `/compact`, `relearn` in `redraw`), `plan.py` (`load_tool` in `READ_ONLY`),
`subagent.py` and `browse.py` (`toolset` through `active_schemas`),
`evaluate.py` (the usage recorder takes the estimate; `WARNED` and `LOADED` reset per task). Everything else is
unchanged from step 31.

## What the next step adds

Step 33 copies every file before an edit tool changes it, so `/undo` and
`/rewind` put the workspace back along with the transcript.
