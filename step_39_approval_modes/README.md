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
in every mode, `auto` included. The mode is written to the session log,
so `--resume` comes back in it. With the shipped rules, `default` and
`accept-edits` give the same verdicts: `accept-edits` is a promise that
holds when a stricter rule is added, not a change you can see today.

## Files

```text
step_39_approval_modes/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; --mode starts the chat (or an eval) in an approval mode
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
│   ├── sandbox.py        an OS sandbox for bash; popen() and kill_tree() for a timeout
│   ├── session.py        append-only JSONL session log; {"mode": name} entries, load() and --resume
│   ├── skills.py         skills, unchanged since stage 9
│   ├── subagent.py       the subagent loop; TASK_SCHEMA has no top-level anyOf
│   ├── todos.py          the plan behind write_todos
│   ├── tools.py          the tool registry; decide() and run() never raise
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
├── test_step.py     offline tests: every mode through permissions.check, the loop, the log, headless
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

### What breaks without it

Without a mode, "review this repository without touching it" is a
sentence the user has to enforce by hand. Step 38's rules allow an edit
inside the project, so the first `write_file` lands before the user can
say no; the only defence is to watch every prompt and answer `n`, and
an `allow`-rated call never prompts at all. The other direction is as
bad: a batch run with `-p` stops at the first `python` command and, with
no terminal to answer on, that call is denied and the run ends with half
the work done. `--mode read-only` and `--mode auto` are the two
sentences a user could not say before.

## The code, piece by piece

### 1. The modes and their tables

`harness/modes.py`:

```python
MODES = {
    "default": "the rules as they are: read-only commands run, edits inside the project run, the rest asks",
    "accept-edits": "edits inside the project never ask; the bash rules are unchanged",
    "read-only": "edits, memory writes and every call the rules would ask about are denied; exploration runs",
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
stays in force in `default`. The test
`test_accept_edits_keeps_its_promise_when_the_rules_would_ask` adds such
a rule and shows the two rows part ways.

### 2. Which mode is in force, and the log

`harness/modes.py`:

```python
def current():
    """The mode in force: plan while plan.MODE is plan, otherwise CURRENT."""
    return "plan" if plan.MODE == "plan" else CURRENT


def set_mode(name, log=True):
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
    if log:
        session.mode(name)
    return name
```

Plan mode is not stored in `CURRENT`. It lives in `plan.MODE`, where
step 28 put it, and `current()` reports `plan` while that flag is set.
So `/mode plan`, `/plan` and an approved plan all compose: entering plan
mode leaves `CURRENT` alone, and when `plan.approve` flips `plan.MODE`
back to `act`, the mode the user had before is in force again. Picking
any other mode while in plan mode leaves plan mode.

Every switch is one line in the session log. `harness/session.py`:

```python
def mode(name):
    """Record that the approval mode is `name` from here on."""
    append({"mode": name})
```

and `session.load` replays it with `modes.set_mode(entry["mode"], log=False)`
(a name this version does not know is skipped), so `--resume` opens the
chat in the mode it was in when it ended. Plan mode is not logged: a plan
that was never approved does not survive the session either.

### 3. Category and rewrite

`harness/modes.py`:

```python
def category(name, args, inside_project):
    """Which row of the table a call falls under.

    remember and forget write files too - under the harness home, not the
    project - so they count as an edit inside: read-only denies them.
    """
    if name in ("bash", "bash_background"):
        return "bash"
    if name in ("write_file", "str_replace"):
        return "edit-inside" if inside_project(args.get("path", "")) else "edit-outside"
    if name in ("remember", "forget"):
        return "edit-inside"
    return "other"


def apply(mode, kind, action):
    """The verdict after the mode has its say. A deny stays a deny."""
    if action == "deny":
        return "deny"
    return TABLE[mode].get(kind, {}).get(action, action)
```

Four categories cover every tool: a bash command, an edit inside the
project, an edit outside it, and anything else, which is where
`browser_open`, `computer_act` and the MCP tools land. The memory
tools `remember` and `forget` write files under `~/.simple-harness`, so
they are filed as edits: `read-only` denies them, `recall` still runs.
`apply` is two dictionary lookups with a guard in front: a `deny`
returns before the table is read, so no mode can rewrite one.

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

`read-only` is only as read-only as the bash rules are honest. `cat` is
on the allow list; `cat a.txt > b.txt` writes a file. So `rate()` looks
at what an allowed command does with its output:

```python
def writes(part):
    """Whether an otherwise read-only command would write: a redirection, tee, or find that deletes or execs."""
    if unquoted(part, ">") or first_word(part) == "tee":
        return True
    return first_word(part) == "find" and any(w in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for w in part.split())
```

An allowed part that writes becomes an `ask`, and a command the rules
cannot read at all - a `$(...)`, a backtick, a `<(...)` - is an `ask`
whatever its first word (`opaque`). In `default` those ask; in
`read-only` and in plan mode the table turns the ask into a deny. The
session rules of step 35 (`a` = always) are not consulted in those two
modes either: an `always` given in act mode must not unlock a command
where the answer is always no.

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
    if cli.print:
        headless()
        session.ENABLED = bool(cli.resume)  # a one-off question leaves no session behind
    if cli.mode:
        modes.set_mode(cli.mode)  # before the banner and the first check; logged, so --resume comes back in it
    if not cli.print:
        ui.banner(sandbox.name(), modes.current())
```

`--mode` takes one of the five names; argparse rejects any other. The
mode is set before the banner is drawn and before the first tool call is
checked, so `harness --mode auto -p "..."` runs a headless turn that
never prompts and `harness --mode read-only` opens a chat that cannot
write. `harness --mode read-only eval evals` applies the mode too:
`main()` sets it before the suite runs, without a log entry, since an
eval keeps no chat log.

### 7. The late block

`harness/context.py`:

```python
            f"mode: {modes.current()}\n"
```

The `<env>` block used to say `act` or `plan`. It now names the approval
mode, so the model sees `read-only` or `auto` on every call and can
explain a blocked edit or skip asking whether it may run a command.

## Run it

Prerequisites: Python 3.10+, `API_KEY` (and optionally `BASE_URL`,
`MODEL`) in the environment or in `~/.simple-harness/env`.

```bash
pip install -e .
harness --mode read-only
```

```powershell
pip install -e .
harness --mode read-only
```

### Expected output

The banner reads `mode: read-only`. Ask for a change:

```text
> add a hello() function to app.py

  ╭──────────────────────────────────────────────────────╮
  │ write_file path=app.py                               │
  │ ──────────────────────────────────────────────────── │
  │ Blocked by policy: read-only mode: write_file app.py │
  ╰──────────────────────────────────────────────────────╯

  2,143 prompt (estimate 2,101) · 96 completion

I cannot write in read-only mode. Here is the function to add: ...
```

Nothing on disk moves. Type `/mode`:

```text
  default       the rules as they are: read-only commands run, edits inside the project run, the rest asks
  accept-edits  edits inside the project never ask; the bash rules are unchanged
* read-only     edits, memory writes and every call the rules would ask about are denied; exploration runs
  auto          nothing asks; deny rules, session nevers and the sandbox still apply
  plan          read-only tools until a plan is approved (step 28)
```

Type `/mode accept-edits` and ask for the same change: the edit lands
without a prompt, and a `python app.py` command still asks. Type `/mode
auto` and nothing asks, but `rm -rf build` is still `Blocked by policy`.
Leave with `/exit`, and `harness --resume` opens the chat in `auto`.

A headless batch that must not stop for a prompt:

```bash
harness --mode auto -p "run the tests and fix the first failure"
```

Run the offline tests from the repository root:

```bash
python run_tests.py 39
python check_snippets.py 39
```

```powershell
python run_tests.py 39
python check_snippets.py 39
```

## Error handling

- **A bad tool call.** `tools.decide` parses the arguments itself:
  `{broken` or `[1, 2]` becomes the result `Error: the arguments of bash
  are not a JSON object: ...`, a name that is not a tool becomes `Error:
  no tool named 'foo'.`, a missing `command`/`path`/`url` is a deny
  `bash: missing argument 'command'`, and a tool that raises hands back
  `Error: FileNotFoundError: ...`. Every tool call gets exactly one tool
  message, so the transcript is always valid and the loop goes on.
- **A failing command.** Its output and exit text come back as the
  result. A command that runs past 60 s is killed with its whole process
  tree (`taskkill /T` on Windows, the process group on POSIX) and the
  result is `Timed out after 60s and was killed. Output so far:` with what
  it printed.
- **Ctrl-C.** During a model call or a tool batch, the steer prompt
  opens: type to steer, enter to go on, ctrl-c again to leave. Every
  tool call already has a result (`INTERRUPTED` for the ones that did
  not run), and the transcript is saved.
- **A dead model call.** `call_llm` retries a transport error, a 5xx
  and a 429 with a note per try; when it gives up, the reply comes back
  with a `failed` reason, the turn ends on `model call failed ... giving
  up` and nothing half-made goes in the transcript. The user message
  stays, so `--resume` can ask again.
- **A crash mid-turn.** `--resume` runs `recover()`: the tool calls left
  without a result run again, and if that fails they get an `Error:`
  result, so the transcript can always be sent.
- **Leaving.** `/exit`, `/quit`, ctrl-d, or ctrl-z then enter on
  Windows. An empty line is ignored.

## Gotchas / What this is not

- `default` and `accept-edits` are the same today. The difference only
  shows once a rule rates an in-project edit `ask`.
- `read-only` means no project edits, no memory writes, and no asks. It
  does not mean no side effects: `pytest` is on the allow list and runs
  the tests, which may write caches and temp files, and an MCP tool
  matched by `MCP_ALLOW` or `computer_act` with `COMPUTER_AUTO=1` is an
  `allow` in the `other` row, which read-only leaves alone. On Windows
  there is no OS sandbox (`sandbox.name()` says `none`), so the rules
  are the only fence.
- `/mode read-only`, then `/plan`, then approve the plan: you are back
  in `read-only`, and the approved plan's edits are denied. Switch with
  `/mode default` first, or approve from `default`.
- `-p` without a terminal on stdin (a pipe, a CI job) answers every ask
  with `n` and a note on stderr, and the run exits 1 when there is no
  answer. `--mode auto` or `--mode read-only` is the sane headless
  choice; `default -p` works only when a person is at the keyboard.
- `-p` writes no session file unless `--resume` is given: a one-off
  question leaves nothing behind.
- The mode is per session, not per project: there is no config file for
  a default mode. `--mode` or `/mode` each time, or `--resume`.
- The tool named `bash` runs `cmd.exe` on Windows: the rules match the
  command text, not the shell.

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
- The mode is a module global, so it binds subagents and `/pipeline`
  too: a worker agent in `read-only` has its `write_file` denied by the
  same table.

## Diff from step 38

```bash
diff -r ../step_38_capstone/harness harness
```

Added: `modes.py` (`MODES`, `NAMES`, `TABLE`, `CURRENT`, `current`,
`set_mode`, `category`, `apply`, `describe`). Changed: `permissions.py`
(`check` consults the mode, then `rules`, then `modes.apply`; the old
body is `rules`; `describe`; `session_rules_apply` skips plan and
read-only), `commands.py` (`/mode`, `mode`, the banner in `redraw` and
`/act` report `modes.current()`), `agent.py` (`--mode`, `chat` and
`main` set the mode), `session.py` (`mode()` entries, replayed by
`load`), `context.py` (`<env>` names `modes.current()`), `ui.py`
(`/mode` in the banner), `pyproject.toml` (version). The capstone, the
agents, the evals and everything else are unchanged from step 38.

## What the next step adds

Step 40 lets an agent definition hand the whole conversation to another
one: `handoff_to`, `/handoff`, and a `{"handoff": name}` log entry next
to this step's `{"mode": name}`.
