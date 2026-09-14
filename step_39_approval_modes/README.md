# Step 39 - Approval modes

**What this step adds:** named permission policies. `harness/modes.py`
holds five modes: `default`, `accept-edits`, `read-only`, `auto` and
`plan`. A mode is a table that rewrites the verdict of the step 11 rules
before anyone is asked. `permissions.check` consults the mode first, then
the rules, then applies the table. `/mode` shows or switches the mode,
`--mode` starts the chat in one, and the banner and the `<env>` block of
the late injection show which one is in force. Plan mode is one of the
five: it delegates to step 28, and leaving it brings back the mode the
user had before. A `deny` rule and a session `never` from step 35 hold
in every mode, `auto` included.

## Files

```text
step_39_approval_modes/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; --mode starts the chat in an approval mode
│   ├── agents.py         agent definitions: subagents described in Markdown files
│   ├── ask_user.py       the ask_user tool: a question to the user, answer as result
│   ├── browse.py         the browse tool set over the step 23 browser subagent
│   ├── browser.py        browser tools: one Chromium page driven through Playwright
│   ├── budget.py         the context budget: where the window goes, when to warn
│   ├── checkpoint.py     workspace checkpoints: file copies taken before each edit
│   ├── commands.py       slash commands: /mode joins /pipeline, /undo, /rewind
│   ├── compact.py        the compaction agent; its note is kept
│   ├── computer.py       computer use: the screen as a tool
│   ├── config.py         settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py        the late injection block; <env> names the approval mode
│   ├── durability.py     the loop detector and the crash-recovery scan
│   ├── evaluate.py       the evaluation harness; run_suite(workspace=DIR) grades a copy
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events with a built-in list; checkpoint capture is one
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs: commands that run while the chat goes on
│   ├── llm.py            the model call with retries; the prompt lists the agent definitions
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── modes.py          named permission policies, one layer above the rules
│   ├── permissions.py    the rules, then modes.apply rewrites an allow or an ask
│   ├── pipeline.py       the plan, work, review pipeline behind /pipeline
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line
│   ├── sandbox.py        an OS sandbox for bash
│   ├── session.py        append-only JSONL session log, load() and --resume
│   ├── skills.py         skills, unchanged since stage 9
│   ├── subagent.py       the subagent loop; TASK_SCHEMA has no top-level anyOf
│   ├── todos.py          the plan behind write_todos
│   ├── tools.py          the tool registry; run() turns a raised exception into Error:
│   └── ui.py             rich panels; pipeline() draws the summary table
├── .agents/
│   ├── .gitignore                     ignores tool_log.txt, the PostToolUse hook's log
│   ├── hooks.json                     hook config: one PreToolUse and one PostToolUse hook
│   ├── block_env_writes.py            example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py                example PostToolUse hook: appends every tool name to a log
│   ├── mcp.json                       MCP config: one stdio server, echo
│   ├── mcp_echo_server.py             a tiny MCP server: two tools, stdio transport
│   ├── skills/explain-code/SKILL.md   the stage 4 skill
│   ├── agents/planner.md              definition: reads the code, returns a numbered plan
│   ├── agents/worker.md               definition: carries out one plan step with the edit tools
│   └── agents/reviewer.md             definition: checks one step, answers PASS or FAIL
├── evals/           three step 30 tasks: task.md, check.py or expect.txt, workspace/
├── capstone/        the end-to-end task, carried over from step 38
│   ├── task.md         the brief: a FastAPI todo API with SQLite, tests and a README
│   ├── run.py          the runner: one headless harness run, then the eval suite
│   ├── evals/          five checks, one folder each: task.md, check.py; _common.py helpers
│   ├── reference/      hand-written solution that proves the checks are passable
│   │   ├── app.py        the todo API: FastAPI on top of a SQLite file
│   │   ├── test_app.py   its tests; every test gets an empty database
│   │   └── README.md     its README, with the run section check 4 looks for
│   ├── report.json     the recorded run: calls, tokens, cost and the check results
│   ├── SCORECARD.md    the recorded run as a markdown scorecard, 4/5
│   └── transcript.md   the recorded run's messages, readable
├── AGENTS.md        project instructions the harness reads into its prompt
├── test_step.py     offline tests: every mode through permissions.check and the loop
├── pyproject.toml   package metadata; version 0.39.0
└── README.md        this file
```

## Why a mode above the rules

The rules of step 11 answer one question per call: does this call run,
ask or stop. The answer is fixed in `BASH_RULES` and in the checks for
edits, browser, computer and MCP tools. The user cannot change how much
the harness asks without editing the rules.

How much to ask is a decision about the session, not about one call. A
user who is reviewing a repository wants nothing written and no prompts
to say no to. A user who is refactoring wants edits to land and only
commands to ask. A user running an unattended batch wants no prompts at
all, with the dangerous commands still blocked. Each of these is a
policy, and a policy deserves a name.

A mode is that name. It sits above the rules and rewrites their answer.
The rules still rate every call, so the knowledge of which commands are
read-only and which are dangerous stays in one place. The mode only says
what happens to an `allow` and an `ask`. A `deny` never reaches the
table: `auto` runs everything the rules would ask about, and still stops
at `rm`, `sudo` and `git push`. The OS sandbox of step 12 wraps the
command after the verdict and enforces on its own, whatever the mode.

## The code, piece by piece

### 1. The modes and their tables

`harness/modes.py`:

```python
MODES = {
    "default": "the rules as they are: read-only commands run, edits inside the project run, the rest asks",
    "accept-edits": "edits inside the project never ask; the bash rules are unchanged",
    "read-only": "edits and every call the rules would ask about are denied; exploration runs",
    "auto": "nothing asks; deny rules, session nevers and the sandbox still apply",
    "plan": "read-only tools until a plan is approved (step 28)",
}

NAMES = tuple(MODES)

# mode -> category -> {rule verdict: final verdict}. Only allow and ask appear
# as keys: a deny is final and never reaches the table.
TABLE = {
    "default": {},
    "accept-edits": {
        "edit-inside": {"ask": "allow"},
    },
    "read-only": {
        "edit-inside": {"allow": "deny", "ask": "deny"},
        "edit-outside": {"allow": "deny", "ask": "deny"},
        "bash": {"ask": "deny"},
        "other": {"ask": "deny"},
    },
    "auto": {
        "edit-inside": {"ask": "allow"},
        "edit-outside": {"ask": "allow"},
        "bash": {"ask": "allow"},
        "other": {"ask": "allow"},
    },
    "plan": {},
}

CURRENT = "default"
```

`MODES` is the list the user sees: a name and one line. `TABLE` is what
the harness runs: for each mode, for each category of call, which rule
verdicts change and into what. A category the table does not name keeps
the verdict the rules gave. `default` and `plan` have empty tables:
`default` is the rules as they are, and `plan` is decided by step 28
before the table is reached.

With the shipped rules, an edit inside the project is already an
`allow`, so `default` and `accept-edits` give the same verdicts. The
`accept-edits` row is the promise that holds when the rules change: a
rule that rates an in-project edit `ask` is overruled by the mode and
stays in force in `default`.

### 2. Which mode is in force

`harness/modes.py`:

```python
def current():
    """The mode in force: plan while plan.MODE is plan, otherwise CURRENT."""
    return "plan" if plan.MODE == "plan" else CURRENT


def set_mode(name):
    ...
    global CURRENT
    if name not in MODES:
        raise ValueError(f"unknown mode {name!r}; one of: {', '.join(NAMES)}")
    if name == "plan":
        plan.set_mode("plan")
        return name
    CURRENT = name
    if plan.MODE == "plan":
        plan.set_mode("act")
    return name
```

Plan mode is not stored in `CURRENT`. It lives in `plan.MODE`, where
step 28 put it, and `current()` reports `plan` while that flag is set.
So `/mode plan`, `/plan` and an approved plan all compose: entering plan
mode leaves `CURRENT` alone, and when `plan.approve` flips `plan.MODE`
back to `act`, the mode the user had before is in force again. Picking
any other mode while in plan mode leaves plan mode.

### 3. Category and rewrite

`harness/modes.py`:

```python
def category(name, args, inside_project):
    """Which row of the table a call falls under."""
    if name in ("bash", "bash_background"):
        return "bash"
    if name in ("write_file", "str_replace"):
        return "edit-inside" if inside_project(args.get("path", "")) else "edit-outside"
    return "other"


def apply(mode, kind, action):
    """The verdict after the mode has its say. A deny stays a deny."""
    if action == "deny":
        return "deny"
    return TABLE[mode].get(kind, {}).get(action, action)
```

Four categories cover every tool: a bash command, an edit inside the
project, an edit outside it, and anything else, which is where
`browser_open`, `computer_act` and the MCP tools land. `apply` is two
dictionary lookups with a guard in front: a `deny` returns before the
table is read, so no mode can rewrite one.

### 4. The rules, then the mode

`harness/permissions.py`:

```python
def check(name, args):
    ...
    mode = modes.current()
    if mode == "plan" and not plan.offered(name):
        return "deny", f"plan mode: {name} is not available until the plan is approved"
    action, reason = rules(name, args)
    final = modes.apply(mode, modes.category(name, args, inside_project), action)
    if final != action:
        reason = f"{mode} mode: {reason or describe(name, args)}"
    return final, reason


def rules(name, args):
    """The verdict of the rules alone: (action, reason), as check() gave it before step 39."""
```

The body of the old `check` is now `rules`, unchanged: bash rules,
session rules, the project boundary for edits, the browser, computer and
MCP checks. `check` wraps it. The mode is read first, plan mode fences
the tool set as in step 28, the rules rate the call, and the table has
the last word. When the mode changed the verdict, the reason names the
mode, so the model reads `Blocked by policy: read-only mode: write_file
a.txt` and knows why nothing was written.

### 5. The command

`harness/commands.py`:

```python
def mode(messages, name):
    """Without a name, list the modes with the current one marked. With one, switch to it."""
    if not name:
        ui.note(modes.describe())
        return messages
    try:
        modes.set_mode(name)
    except ValueError as unknown:
        ui.note(str(unknown))
        return messages
    ui.note(f"{name} mode: {modes.MODES[name]}")
    return messages
```

`/mode` alone prints the five modes, one per line, with a star on the
current one. `/mode <name>` switches and confirms with the mode's one
line. An unknown name is reported and nothing changes. `/plan` and
`/act` stay: `/plan` enters plan mode, and `/act` leaves it and reports
the approval mode that is back in force.

### 6. The flag and the banner

`harness/agent.py`:

```python
    top.add_argument("--mode", choices=modes.NAMES, help="start in this approval mode (default: default)")
...
def chat(cli):
    if cli.mode:
        modes.set_mode(cli.mode)  # before the banner and the first check
    if cli.print:
        ui.headless()
    else:
        ui.banner(sandbox.name(), modes.current())
```

`--mode` takes one of the five names; argparse rejects any other. The
mode is set before the banner is drawn and before the first tool call is
checked, so `harness --mode auto -p "..."` runs a headless turn that
never prompts and `harness --mode read-only` opens a chat that cannot
write.

### 7. The late block

`harness/context.py`:

```python
            f"mode: {modes.current()}\n"
```

The `<env>` block used to say `act` or `plan`. It now names the approval
mode, so the model sees `read-only` or `auto` on every call and can
explain a blocked edit or skip asking whether it may run a command.

## Run it

```bash
pip install -e .
harness --mode read-only
```

The banner reads `mode: read-only`. Ask for a change and the model's
`write_file` comes back as `Blocked by policy: read-only mode:
write_file ...`; nothing on disk moves. Type `/mode`:

```text
  default       the rules as they are: read-only commands run, edits inside the project run, the rest asks
  accept-edits  edits inside the project never ask; the bash rules are unchanged
* read-only     edits and every call the rules would ask about are denied; exploration runs
  auto          nothing asks; deny rules, session nevers and the sandbox still apply
  plan          read-only tools until a plan is approved (step 28)
```

Type `/mode accept-edits` and ask for the same change: the edit lands
without a prompt, and a `python` command still asks. Type `/mode auto`
and nothing asks, but `rm -rf build` is still `Blocked by policy`.

A headless batch that must not stop for a prompt:

```bash
harness --mode auto -p "run the tests and fix the first failure"
```

Run the offline tests from the repository root:

```bash
python run_tests.py 39
python check_snippets.py 39
```

## What to notice

- The rules are untouched. `rules()` is the old `check()` under a new
  name, and `BASH_RULES` still knows which commands are safe and which
  are dangerous. The mode decides what to do with that knowledge.
- A mode is data. Four rows and two verdicts per row describe every
  mode, and adding a sixth is a new entry in `MODES` and `TABLE`.
- `deny` is final. `apply` returns before the table is read, so a deny
  rule, a session `never` and a hook block hold in every mode. `auto`
  means nothing asks, not everything runs.
- The sandbox is not a rule. It wraps the command after the verdict and
  enforces on its own, so `auto` inside the sandbox still cannot write
  outside the project or reach the network.
- Plan mode composes instead of competing. It stays in `plan.MODE`,
  `current()` reports it, and an approved plan brings back the mode the
  user had, not `default`.
- `read-only` denies what would have asked. Nobody is there to say no,
  so the safe answer is given for them, and the reason names the mode.
- With the shipped rules, `default` and `accept-edits` agree. The mode
  is the guarantee that survives a stricter rule, and the tests show the
  two rows part ways when one is added.

## Diff from step 38

```bash
diff -r ../step_38_capstone/harness harness
```

Added: `modes.py` (`MODES`, `NAMES`, `TABLE`, `CURRENT`, `current`,
`set_mode`, `category`, `apply`, `describe`). Changed: `permissions.py`
(`check` consults the mode, then `rules`, then `modes.apply`; the old
body is `rules`; `describe`), `commands.py` (`/mode`, `mode`, the
banner in `redraw` and `/act` report `modes.current()`), `agent.py`
(`--mode`, `chat` sets the mode and draws the banner from it),
`context.py` (`<env>` names `modes.current()`), `ui.py` (`/mode` in the
banner), `pyproject.toml` (version). The capstone, the agents, the evals
and everything else are unchanged from step 38.
