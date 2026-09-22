# Step 28 - Plan mode and structured output

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 27 - Hooks](../step_27_hooks/README.md). Next: [Step 29 - Background jobs and parallel subagents](../step_29_jobs_parallel_subagents/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** a second mode. In plan mode the model is offered
only read-only tools, and anything else it names is refused. It explores,
then hands in a plan as a JSON object. The harness validates the plan
against a schema, draws it as a panel and asks `approve? (y/n)`. On yes
the steps become the todo list, the mode flips to act, and the plan rides
in the late block until every todo is completed. On no the model stays in
plan mode and gets the user's feedback. `/plan` and `/act` switch modes by
hand.

## Why a mode, and what breaks without it

Up to now the model could start editing the moment it had an idea. For a
small task that is right. For a large one it is a risk: the first edit
lands before the model has read the third file, and the user finds out
what the plan was by watching it happen. Ask the step 27 harness to "move
the config loading into its own module" and the first tool call may well
be a `write_file` of a module that does not yet match what the callers
expect; by the time the model has read the callers, two files are half
changed and the user is reviewing a diff nobody agreed to.

Plan mode separates reading from writing. The tool set offered to the
model shrinks to the read-only tools, so there is nothing to undo when the
plan turns out wrong. The permission layer enforces the same limit, so a
subagent or a parallel call cannot bypass it.

The plan itself is structured output. A plan written as prose is easy to
accept and hard to check. A plan with a `goal`, a list of `steps` that
each name their `files` and `actions`, and a list of `risks` can be
validated by code before a human reads it. The model gets a precise error
for a malformed plan instead of a vague one. Once approved, the steps
become todos with no extra work, because they already have the shape a
todo needs.

## The code, piece by piece

### 1. The mode and the read-only tool set

`harness/plan.py`:

```python
MODE = "act"

READ_ONLY = ("bash", "read_file", "read_skill", "recall", "task")  # offered in plan mode, in this order

PLAN = None     # the approved plan, kept until the todos are all completed
FEEDBACK = []   # what the user said to each rejected plan, newest last
```

```python
def offered(name):
    """Whether a tool may run in the current mode."""
    return MODE == "act" or name in READ_ONLY or name == "submit_plan"


def toolset():
    """The schemas to offer the model: everything in act mode, read-only plus submit_plan in plan mode."""
    from .tools import TOOL_SCHEMAS  # here, not at the top: tools imports this module

    if MODE == "act":
        return TOOL_SCHEMAS
    by_name = {s["function"]["name"]: s for s in TOOL_SCHEMAS}
    return [by_name[name] for name in READ_ONLY if name in by_name] + [SUBMIT_PLAN_SCHEMA]
```

`MODE` is a module variable, read at call time, like `todos.TODOS`. Act
mode offers the whole registry, including the MCP tools that joined it at
start-up. Plan mode offers five read-only tools and `submit_plan`.
`write_file`, `str_replace`, `write_todos`, `remember` and `forget` are
not on the list, so the model cannot call them. `task` stays, because a
subagent that only reads is still useful while planning, and `recall`
stays because the `<memory>` index is still in the late block: offering
the index without the tool that reads it would invite calls the harness
then refuses.

Some read-only tools are withheld all the same. The browser and computer
tools are not on the list (a click is not read-only), and neither are the
MCP tools, whose servers the harness cannot vouch for. A subagent started
from plan mode is offered the same list minus `task` and `submit_plan`:
`subagent.toolset()` filters through `plan.offered`, so it does not burn
its twelve turns on `remember` calls that are refused one by one.

### 2. The plan schema

`harness/plan.py`:

```python
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string", "minLength": 1, "description": "What the work achieves, one sentence"},
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "description": "The step, imperative: 'Add the parser'"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Files this step touches"},
                    "actions": {"type": "array", "items": {"type": "string"}, "description": "What is done to them"},
                },
                "required": ["title", "files", "actions"],
                "additionalProperties": False,
            },
        },
        "risks": {"type": "array", "items": {"type": "string"}, "description": "What could go wrong"},
    },
    "required": ["goal", "steps", "risks"],
    "additionalProperties": False,
}
```

The same schema does two jobs. It is the `parameters` of the `submit_plan`
tool, so the model sees it as the shape it must produce. And it is what
the harness validates against when the call arrives. One source of truth,
so the two cannot drift apart.

`harness/plan.py`:

```python
def validate(plan):
    """The problems with a plan, as strings; an empty list means it is valid."""
    try:
        import jsonschema
    except ImportError:
        return manual_check(plan)
    validator = jsonschema.Draft202012Validator(PLAN_SCHEMA)
    errors = sorted(validator.iter_errors(plan), key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in errors]
```

`jsonschema` is optional. With it, every problem is reported at once,
each with its path: `steps/0: 'actions' is a required property`. Without
it, `manual_check()` walks the object by hand and reports the same
problems in its own words. The tests run both and check they agree on
what is valid, so the fallback cannot quietly accept what the real
validator rejects.

### 3. Submitting a plan

`harness/plan.py`:

```python
def submit_plan(plan):
    """Validate the plan, show it, and ask the user. Returns the result for the model."""
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if MODE != "plan":
        return "Error: not in plan mode"  # a call remembered from an earlier transcript, not offered now
    problems = validate(plan)
    if problems:
        return "Error: the plan is invalid:\n" + "\n".join(f"- {p}" for p in problems)
    ui.plan(plan)
    approved, feedback = ui.approve_plan()
    if approved:
        approve(plan)
        return (
            "Plan approved. Mode is now act and every step is a todo. "
            "Work through them in order and mark each one completed."
        )
    FEEDBACK.append(feedback or "(no feedback given)")
    return f"Plan not approved. Still in plan mode. User feedback: {FEEDBACK[-1]}"
```

An invalid plan is a tool result that starts with `Error:`, the same
convention every other tool uses. The model reads the list and submits
again. A valid plan is drawn, then the question is asked. Both answers
come back as a result string, so the model learns what happened from the
transcript alone.

The first check guards act mode. `submit_plan` is in `TOOLS`, so it can
run whenever the model names it, and a model that has seen the call in an
earlier part of the transcript will sometimes name it again after the
plan was approved. Without the guard that call would draw a panel, ask
you a question and, on yes, overwrite the todo list mid-task.

`harness/plan.py`:

```python
def approve(plan):
    """The plan is accepted: its steps become the todos and the mode becomes act."""
    global MODE, PLAN
    PLAN = plan
    FEEDBACK.clear()
    MODE = "act"
    todos.write_todos([{"content": s["title"], "activeForm": s["title"], "status": "pending"} for s in plan["steps"]])
```

Approval is three assignments and one `write_todos` call. The step
titles become the todo list, all pending; the model marks them as it goes,
the way step 10 taught it to.

### 4. The approve prompt

`harness/ui.py`:

```python
    def approve_plan(self):
        """Step 28: the plan is on screen; ask for a yes, or a no with feedback.

        Returns (approved, feedback). Feedback is empty on yes, and on a no
        it is whatever the user typed at the second prompt.
        """
        try:
            answer = prompt.read("  approve? (y/n)> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False, ""
        if answer.lower().startswith("y"):
            return True, ""
        try:
            return False, prompt.read("  feedback> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False, ""
```

The question goes through `prompt.read`, the same path `approve()` uses
for a tool call. That matters for two reasons. The line editor, history
and the fallback to `input()` all apply. And the tests can script the
answers by replacing one function.

Because it asks a question, `submit_plan` is in `tools.SERIAL`, next to
`task` and the browser tools:

`harness/tools.py`:

```python
SERIAL = {"task", "browse", "submit_plan", *browser.TOOLS, *computer.COMPUTER_TOOLS}
```

A reply that carries `submit_plan` next to a `bash` call, which models
do, runs one call after the other on the main thread instead of on the
pool from step 22. The plan panel and the prompt come out in order, not
under the other call's output, and the prompt is read from the thread
that owns the terminal.

### 5. The permission layer enforces the mode

`harness/permissions.py`:

```python
def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if plan.MODE == "plan" and not plan.offered(name):
        return "deny", f"plan mode: {name} is not available until the plan is approved"

    if name == "bash":
        command = args.get("command", "")
        if not command:
            return "deny", "bash: missing argument 'command'"
        action = decide(command)
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {command}"
        return action, f"run: {command}"
```

Offering fewer tools is the first fence. This is the second. In plan mode
a `bash` command the rules would ask about is denied instead: the user is
not asked, because in plan mode the answer is always no. Any tool outside
the plan tool set is denied as well, which covers a subagent that was
offered `remember` before the mode changed and a parallel call that
arrived with an edit.

Be precise about what the second fence is: it is the bash rule table
from step 11, as hardened in step 25. A part the table rates `allow`
still runs. What keeps that honest is that the table rates as `ask`
anything that turns a read into a write - a redirection (`echo hi >
f.txt`), `tee`, `find -delete`/`-exec` - and anything it cannot see
into (`$(...)`, backticks). So in plan mode `ls -la` and `git status`
run, and `echo hi > f.txt`, `find . -delete`, `cat a | tee b` and
`python setup.py` are all `Blocked by policy: plan mode: ...`. The
guarantee is exactly as strong as that table; a command the table would
wrongly allow would run in plan mode too.

### 6. The late block and the prompt

`harness/context.py`:

```python
            f"mode: {plan.MODE}\n"
            "</env>" + todos_note() + plan.plan_note() + memory_note() + hooks_note(hook_context) + changes_note()
```

`harness/plan.py`:

```python
def plan_note():
    """The <plan> block for the late injection, or an empty string."""
    global PLAN
    if MODE == "plan":
        text = "You are in plan mode. Read, then call submit_plan. Nothing is written until the user approves."
        if FEEDBACK:
            text += "\nFeedback on rejected plans:\n" + "\n".join(f"- {f}" for f in FEEDBACK)
        return f"\n<plan>\n{text}\n</plan>"
    if PLAN is not None and done():
        PLAN = None  # every step is completed: the plan has served its purpose
    if PLAN is None:
        return ""
    return f"\n<plan>\napproved plan, follow it:\n{render(PLAN)}\n</plan>"
```

The `<env>` tag names the mode on every call. The `<plan>` tag has three
states. In plan mode it carries the instruction and any feedback from
rejected plans, so the feedback survives compaction. In act mode with an
approved plan it carries the plan, rendered as text, next to the todos
made from it. Once every todo is completed the plan is dropped and the tag
disappears.

`done()` is `all(...)` over the todo list, guarded against an empty one:
a `write_todos([])` from the model would otherwise count as "every step
completed" and drop the approved plan from the late block.

`harness/llm.py`:

```python
def with_mode(messages):
    """The messages to send: in plan mode the system prompt carries PLAN_PROMPT."""
    if plan.MODE != "plan" or not messages or messages[0].get("role") != "system":
        return messages
    first = dict(messages[0])
    first["content"] = first["content"] + PLAN_PROMPT
    return [first] + messages[1:]
```

`harness/agent.py`:

```python
                    message, usage = call_llm(with_mode(messages) + [injection], tools=plan.toolset(), on_delta=on_delta)
```

The plan-mode suffix is attached per request, not written into the
transcript. Both the suffix and the tool set are read at call time. An
approval in the middle of a turn changes the very next request: the
request that carried `submit_plan` was made in plan mode, the one after
its result is made in act mode with every tool.

### 7. Switching by hand

`harness/commands.py`:

```python
def set_mode(messages, mode):
    """Switch between plan and act; the late block carries the mode from the next call on."""
    plan.set_mode(mode)
    if mode == "plan":
        ui.note("plan mode: the model reads and proposes; nothing is written until you approve a plan")
    else:
        ui.note("act mode: every tool is available")
    return messages
```

`/plan` enters plan mode and clears any old plan and feedback. `/act`
leaves it without a plan; the model is trusted again from the next call.
The banner shows the mode, and so does every late injection panel.

## Run it

Prerequisites are those of step 27: Python 3.11+, `API_KEY` (and
`BASE_URL`/`MODEL` if not OpenRouter) in the environment or in
`~/.simple-harness/env`. `jsonschema` is optional; without it the manual
validator runs. Start from this directory so `.agents/` is found.

bash:

```bash
cd harness/04_tools/step_28_plan_mode
pip install -e .
harness
```

PowerShell:

```powershell
cd harness/04_tools/step_28_plan_mode
pip install -e .
harness
```

Then switch to plan mode before a task you want to see first:

```text
> /plan
> add a --version flag to the command line
```

### Expected output

```text
────────────────────────── coding agent ──────────────────────────
  mode: act  ·  sandbox: none  ·  /plan  /act  /sessions  /rewind  ·  alt-enter for a newline  ·  ctrl-d (ctrl-z then enter on Windows), ctrl-c or /exit to leave

> /plan

  plan mode: the model reads and proposes; nothing is written until you approve a plan

> add a --version flag to the command line

  ╭──────────────────────────────────────────────────────────────────╮
  │ read_file {"path": "harness/agent.py"}                           │
  │ ──────────────────────────────────────────────────────────────── │
  │ """Step 28 - every model call is made for the current mode. ...  │
  ╰──────────────────────────────────────────────────────────────────╯

  ╭──────────────────────────────────────────────────────────────────╮
  │ bash {"command": "python setup.py --help"}                       │
  │ ──────────────────────────────────────────────────────────────── │
  │ Blocked by policy: plan mode: only read-only commands run        │
  │ before the plan is approved: python setup.py --help              │
  ╰──────────────────────────────────────────────────────────────────╯

  ╭─ plan ───────────────────────────────────────────────────────────╮
  │ goal  Print the package version and exit when --version is given │
  │ 1.    Add the flag to the parser                                 │
  │       files: harness/agent.py                                    │
  │       - add_argument("--version", action="version", ...)         │
  │ 2.    Read the version from package metadata                     │
  │       files: harness/agent.py                                    │
  │       - importlib.metadata.version("simple-harness")             │
  │ risk  the package is not installed, so metadata is missing       │
  ╰──────────────────────────────────────────────────────────────────╯
  approve? (y/n)> y

  ╭──────────────────────────────────────────────────────────────────╮
  │ todos 0/2                                                        │
  │ [ ] Add the flag to the parser                                   │
  │ [ ] Read the version from package metadata                       │
  ╰──────────────────────────────────────────────────────────────────╯

  ╭──────────────────────────────────────────────────────────────────╮
  │ str_replace {"path": "harness/agent.py", "old_str": ...}         │
  │ ──────────────────────────────────────────────────────────────── │
  │ Replaced 1 match(es) in harness/agent.py                         │
  ╰──────────────────────────────────────────────────────────────────╯
```

The late injection panel carries `mode: plan` in `<env>` and a `<plan>`
block with the instruction. Answer `n` at the prompt and type feedback at
the `feedback>` prompt: the model gets it as its tool result and in the
`<plan>` block, and submits a new plan. Answer `y` and three things happen
at once: the `todos 0/N` panel appears, the next late injection panel
reads `mode: act` with the plan under `<plan>`, and the model starts
editing. When the last todo is marked completed the `<plan>` block is gone.

Run the offline tests from the repository root:

```bash
python run_tests.py 28
python check_snippets.py 28
```

## Error handling

- **An invalid plan** (a step without `actions`, an empty `steps` list) is
  the tool result `Error: the plan is invalid:` followed by one line per
  problem with its path; the model fixes it and submits again. Nothing is
  shown to you until a plan is valid.
- **`submit_plan` in act mode** returns `Error: not in plan mode`; no
  panel, no question, the todo list is untouched.
- **A write in plan mode** - `write_file`, `str_replace`, `remember`, an
  MCP tool, or a `bash` command the rules do not allow - is `Blocked by
  policy: plan mode: ...` and never runs. `PostToolUse` hooks do not run
  for it either.
- **ctrl-c or ctrl-d at `approve? (y/n)>`** counts as a no with no
  feedback: the model gets `Plan not approved. Still in plan mode. User
  feedback: (no feedback given)` and usually submits the same plan again.
  Type `n` and a sentence instead when you want it changed; use `/act` to
  leave plan mode without approving anything.
- **A tool call with broken arguments** is `Error: the arguments of
  <tool> are not a JSON object: ...`; an unknown tool `Error: no tool
  named '...'.`; a tool that raises `Error: <Type>: <message>`. One tool
  message per call, in every mode.
- **A failing command** returns its output and exit code; past 60s it is
  killed with its process tree: `Timed out after 60s and was killed.
  Output so far: ...`.
- **A dead model call** ends the turn with the note `model call failed:
  ...`; your message stays and the mode is unchanged.
- **ctrl-c mid-turn** answers the unfinished tool calls with
  `(interrupted before this tool ran)` and returns to the prompt. If it
  lands during `submit_plan`, the plan counts as not approved.
- **More than 40 model calls in one turn** stops the turn with a note; say
  `continue` to go on.

To leave: `/exit`, `/quit`, ctrl-d (ctrl-z then enter on Windows) or
ctrl-c at the prompt.

## Gotchas / What this is not

- **Plan mode is as read-only as the bash rules.** The offered tool set
  and `check()` keep every write-capable *tool* out. For `bash`, the
  only rule is "allow-rated parts run": the redirection, `tee`, `find
  -delete` and `$(...)` checks in `permissions.rate` are what stop an
  allow-listed command from writing. Nothing inspects what a command
  does, and there is no OS sandbox on Windows.
- **Mode, plan and feedback are process state.** They live in `plan.py`,
  not in the transcript. `--resume` and `/sessions` start in act mode
  with no plan; the todo list is rebuilt from the transcript, the plan
  is not. Compaction keeps them, because they were never in the
  transcript to lose.
- **`/rewind` does not rewind the mode.** Cut back to a message sent in
  plan mode and the next request is made in whatever the mode is now.
- **Read-only is not the same as offered.** `recall` is offered; the
  browser, computer and MCP tools are not, even the ones that only read.
  Step 29's `job_status` is not either.
- **`task` in plan mode is a read-only subagent.** It gets `bash`,
  `read_file`, `read_skill` and `recall`, and the same denials apply to
  every call it makes.
- **The approval is a `y`.** Anything else, including an empty line, is a
  no; the feedback prompt then takes one line.
- **`submit_plan` runs on the main thread.** It is in `SERIAL`, so a
  reply that batches it with other calls runs them one after another;
  the batch loses the step 22 parallelism for that reply.
- **`-p` mode is act mode.** There is no `/plan` on the command line, so
  a one-off run never plans; a `submit_plan` the model names anyway is
  `Error: not in plan mode`.
- **Windows:** the tool called `bash` runs `cmd.exe` (the banner says
  `sandbox: none`); the same rule table applies to what it is given.

## What to notice

- Two fences, one rule. The tool set offered is the first fence; the
  permission check is the second. A subagent, a parallel call and a
  hook-replaced result all pass through the second. The second fence is
  only as strict as the bash rule table, which is why step 25 made the
  table refuse redirections and hidden commands.
- The schema is shown to the model and used by the harness. The model
  produces the shape it was shown, and the harness rejects what does not
  match, with a path for every problem.
- Approval is cheap because todos already exist. A plan step and a todo
  have the same shape, so the approved plan becomes the plan the model
  follows, with no second representation to keep in sync.
- Nothing is written into the transcript to mark the mode. The suffix
  and the tool set are attached per request. Rewind to a message from
  plan mode and the request is made with whatever the mode is now.
- Feedback lives in the late block, not only in the tool result, so a
  compaction in the middle of a long planning round does not lose it.

## Files

```text
step_28_plan_mode/
├── harness/
│   ├── llm.py                        the model call; PLAN_PROMPT and with_mode() per request
│   ├── tools.py                      the registry; submit_plan can run but is offered only in plan mode
│   ├── agent.py                      the loop; tool set and system prompt read per call for the mode
│   ├── plan.py                       plan mode: MODE, toolset(), PLAN_SCHEMA, submit_plan, approval
│   ├── permissions.py                allow / ask / deny per tool call; plan mode denies writes
│   ├── context.py                    the late injection block; mode in <env>, a <plan> tag
│   ├── commands.py                   slash commands; /plan and /act switch the mode
│   ├── hooks.py                      hooks: reads hooks.json, runs commands and functions per event
│   ├── mcp_client.py                 MCP client: starts each server over stdio, registers its tools
│   ├── memory.py                     persistent memory: markdown files with front matter
│   ├── compact.py                    the compaction agent; its handoff note is kept
│   ├── history.py                    transcript trimming: cap, strip, fit, image messages
│   ├── subagent.py                   the subagent loop shared by task and browse; filtered by the mode
│   ├── browse.py                     the browser subagent
│   ├── browser.py                    browser tools: one Chromium page through Playwright
│   ├── computer.py                   computer use: screen size, screenshot, act
│   ├── todos.py                      the plan: write_todos and the todo list
│   ├── skills.py                     skills: SKILL.md discovery and index
│   ├── session.py                    append-only JSONL log, load() with repair, /rewind markers
│   ├── sandbox.py                    an OS sandbox for bash, and the process-group plumbing
│   ├── config.py                     settings: environment first, ~/.simple-harness/env fills gaps
│   ├── prompt.py                     the input line, through prompt_toolkit
│   ├── ui.py                         rich panels; the banner names the mode, plan() and approve_plan()
│   └── __init__.py                   package marker
├── .agents/
│   ├── hooks.json                    hook config: block .env writes, log every tool name
│   ├── block_env_writes.py           example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: appends every tool name to a log
│   ├── .gitignore                    ignores tool_log.txt, the log hook's output
│   ├── mcp.json                      MCP config: the echo server, started with python
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── skills/explain-code/SKILL.md  the stage 4 skill
├── test_step.py                      offline tests against a fake model
├── pyproject.toml                    package metadata; version 0.28.0
└── README.md                         this file
```

## What the next step adds

Step 29 adds background jobs (`bash_background`, `job_status`, `job_wait`,
`job_kill`) for commands that keep running, and lets one `task` call run
several subagents at once.

## Diff from step 27

```bash
diff -r ../step_27_hooks/harness harness
```

Added: `plan.py` (`MODE`, `READ_ONLY`, `PLAN_SCHEMA`, `SUBMIT_PLAN_SCHEMA`,
`offered`, `toolset`, `manual_check`, `validate`, `render`, `approve`,
`submit_plan`, `set_mode`, `done`, `plan_note`). Changed: `tools.py`
(`submit_plan` in `TOOLS` and in `SERIAL`), `permissions.py` (plan-mode
denials in `check`), `context.py` (`mode:` in `<env>`, `<plan>` after
`<todos>`), `commands.py` (`/plan`, `/act`, banner with the mode),
`llm.py` (`PLAN_PROMPT`, `with_mode`), `agent.py` (`call_llm` with
`with_mode` and `plan.toolset()`, banner with the mode), `ui.py` (`banner`
takes the mode, `plan`, `approve_plan`), `subagent.py` (`toolset` filtered
through `plan.offered`). Everything else is unchanged from step 27.
