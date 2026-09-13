# Step 28 - Plan mode and structured output

**What this step adds:** a second mode. In plan mode the model can read
but not write. It explores, then hands in a plan as a JSON object. The
harness validates the plan against a schema, draws it as a panel and asks
`approve? (y/n)`. On yes the steps become the todo list, the mode flips to
act, and the plan rides in the late block until every todo is completed.
On no the model stays in plan mode and gets the user's feedback. `/plan`
and `/act` switch modes by hand.

## Why a mode, and why a schema

Up to now the model could start editing the moment it had an idea. For a
small task that is right. For a large one it is a risk: the first edit
lands before the model has read the third file, and the user finds out
what the plan was by watching it happen.

Plan mode separates reading from writing. The tool set offered to the model
shrinks to the read-only tools, so there is nothing to undo when the plan
turns out wrong. The permission layer enforces the same limit, so a
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

READ_ONLY = ("bash", "read_file", "read_skill", "task")  # offered in plan mode, in this order

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
start-up. Plan mode offers four read-only tools and `submit_plan`.
`write_file`, `str_replace`, `write_todos`, `remember` and `forget` are
not on the list, so the model cannot call them. `task` stays, because a
subagent that only reads is still useful while planning.

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
what is valid.

### 3. Submitting a plan

`harness/plan.py`:

```python
def submit_plan(plan):
    """Validate the plan, show it, and ask the user. Returns the result for the model."""
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

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

### 5. The permission layer enforces the mode

`harness/permissions.py`:

```python
def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if plan.MODE == "plan" and not plan.offered(name):
        return "deny", f"plan mode: {name} is not available until the plan is approved"

    if name == "bash":
        action = decide(args["command"])
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {args['command']}"
        return action, f"run: {args['command']}"
```

Offering fewer tools is the first fence. This is the second. In plan mode
a `bash` command the rules would ask about is denied instead: the user is
not asked, because in plan mode the answer is always no. `ls`, `grep`,
`git diff` and the rest of the allow list still run. Any tool outside the
plan tool set is denied as well, which covers a subagent that was offered
`remember` and a parallel call that arrived with an edit.

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

Start the harness and switch to plan mode before a task you want to see
first:

```bash
pip install -e .
harness
> /plan
> add a --version flag to the command line
```

The banner reads `mode: plan`. The late injection panel carries a
`<plan>` block with the instruction. The model reads with `bash` and
`read_file`; a command such as `python setup.py` comes back as
`Blocked by policy: plan mode: ...`. When it has seen enough it calls
`submit_plan`, a panel titled `plan` appears, and the prompt asks:

```text
  approve? (y/n)>
```

Answer `n` and type feedback at the next prompt. The model gets the
feedback as its tool result and submits a new plan. Answer `y` and three
things happen at once: a `todos 0/N` panel appears, the next late
injection panel reads `mode: act` with the plan under `<plan>`, and the
model starts editing. When the last todo is marked completed the `<plan>`
block is gone.

Run the offline tests from the repository root:

```bash
python run_tests.py 28
python check_snippets.py 28
```

## What to notice

- Two fences, one rule. The tool set offered is the first fence; the
  permission check is the second. A subagent, a parallel call and a
  hook-replaced result all pass through the second.
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

## Diff from step 27

```bash
diff -r ../step_27_hooks/harness harness
```

Added: `plan.py` (`MODE`, `READ_ONLY`, `PLAN_SCHEMA`, `SUBMIT_PLAN_SCHEMA`,
`offered`, `toolset`, `manual_check`, `validate`, `render`, `approve`,
`submit_plan`, `set_mode`, `done`, `plan_note`). Changed: `tools.py`
(`submit_plan` in `TOOLS`), `permissions.py` (plan-mode denials in
`check`), `context.py` (`mode:` in `<env>`, `<plan>` after `<todos>`),
`commands.py` (`/plan`, `/act`, banner with the mode), `llm.py`
(`PLAN_PROMPT`, `with_mode`), `agent.py` (`call_llm` with `with_mode` and
`plan.toolset()`, banner with the mode), `ui.py` (`banner` takes the mode,
`plan`, `approve_plan`). Everything else is unchanged from step 27.
