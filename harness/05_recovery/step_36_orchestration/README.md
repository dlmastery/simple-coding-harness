# Step 36 - Orchestration patterns

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Resume work without guessing**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 35 - Human in the loop](../step_35_human_in_the_loop/README.md). Next: [Step 37 - Production harness anatomy](../step_37_production_anatomy/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** subagents defined in Markdown files, and a
pipeline that chains three of them. A file `.agents/agents/<name>.md`
has a front matter with `name`, `description`, a `tools` list and a
`max_turns` cap, and a body that is the system prompt. Each definition
becomes a tool `agent_<name>` built on `subagent.loop`, registered at
import the way MCP tools are registered when their server starts, and
listed in the main system prompt. Three definitions ship: `planner`,
`worker` and `reviewer`. `/pipeline <task>` runs them in order: the
planner writes a numbered plan, the worker carries out each step, the
reviewer checks each step and answers PASS or FAIL, and a failed step is
worked once more with the reviewer's notes. Steps the plan marks
`[parallel]` run at the same time on the step 29 thread pool. A summary
table closes the run.

## Files

```text
step_36_orchestration/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; Ctrl-C anywhere in a turn steers it instead of killing it
│   ├── agents.py         agent definitions: subagents described in Markdown files; a bad file is a note
│   ├── ask_user.py       the ask_user tool: a question to the user, answer as result
│   ├── browse.py         the browse tool set over the step 23 browser subagent
│   ├── browser.py        browser tools: one Chromium page driven through Playwright
│   ├── budget.py         the context budget: where the window goes, when to warn
│   ├── checkpoint.py     workspace checkpoints: file copies taken before each approved edit
│   ├── commands.py       slash commands: /pipeline joins /undo, /rewind, /checkpoints
│   ├── compact.py        the compaction agent; its note is kept
│   ├── computer.py       computer use: the screen as a tool
│   ├── config.py         settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py        the late injection block: <env>, <plan>, <jobs>
│   ├── durability.py     the loop detector, parse_args and the crash-recovery scan
│   ├── evaluate.py       the evaluation harness; `isolated` auto-answers prompts
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events from hooks.json; PostToolUse carries `ok`
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs: commands that run while the chat goes on
│   ├── llm.py            the model call with retries; the prompt lists the agent definitions
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── permissions.py    which calls need a human; session rules from `a` and `never`
│   ├── pipeline.py       the plan, work, review pipeline behind /pipeline; verdict_of, missing_agents
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line; prompts go to stderr without a terminal
│   ├── sandbox.py        an OS sandbox for bash; the process-group timeout
│   ├── session.py        append-only JSONL session log, load() and --resume
│   ├── skills.py         skills, unchanged since stage 9
│   ├── subagent.py       the subagent loop; withheld() is enforced, gather() is the thread pool
│   ├── todos.py          the plan behind write_todos, validated before it replaces the list
│   ├── tools.py          the tool registry; agents.register() adds agent_<name> at import
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
├── AGENTS.md        project instructions the harness reads into its prompt
├── test_step.py     offline tests: definitions, enforcement, /pipeline and the loop on a fake model
├── pyproject.toml   package metadata; version 0.36.0
└── README.md        this file
```

## Why definitions and a pipeline

Step 15 gave the harness one subagent, the explorer behind `task`. It
has one prompt, one tool set and one turn cap, all fixed in code. Step
23 added a second one, the browser, the same way. Each new kind of
subagent was a new module. The prompt is the part that changes most, and
the part a user of the harness wants to change, so it belongs in a file
the user owns, like a skill.

A definition is that file. The harness reads it once, at import, and
builds a tool from it. The model sees `agent_planner` next to `task` and
`browse`, with the definition's description as the tool description, and
calls it the same way. The loop behind it is `subagent.loop`, unchanged:
an empty history, a tool set, a turn cap, and only the final message
comes back.

The pipeline is what the definitions are for. Plan, work, review is the
shape most multi-agent systems take, because it separates three jobs a
single context handles badly at once: deciding what to do, doing it, and
judging whether it was done. The planner never edits, so its plan is not
bent by what it has already changed. The worker sees one step, so it
cannot wander into the next. The reviewer sees the files, not the
worker's confidence. A retry with the reviewer's notes is the feedback
loop, and one retry is the cap: a step that fails twice is reported, not
tried until it passes.

## The code, piece by piece

### 1. Reading a definition

`harness/agents.py`:

```python
AGENT_DIRS = [
    Path.home() / ".agents" / "agents",  # your agents
    Path.cwd() / ".agents" / "agents",   # this project's agents
]

PREFIX = subagent.AGENT_PREFIX  # every agent tool is agent_<name>
DEFAULT_MAX_TURNS = 12          # the same cap as the exploration subagent
EDIT_TOOLS = ("write_file", "str_replace")  # withheld from the exploration subagent, but a definition may name them


FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)  # the block between the first two --- lines
NAME = re.compile(r"[A-Za-z0-9_-]{1,50}")  # agent_<name> has to be a tool name the API accepts


def parse(text):
    ...
    match = FRONT_MATTER.match(text)
    if not match:
        return None, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as broken:
        raise ValueError(f"front matter is not valid YAML: {broken}") from None
    if not isinstance(meta, dict):
        raise ValueError("front matter is not a mapping")
    return meta, text[match.end():].strip()
...
            try:
                meta, body = parse(path.read_text(encoding="utf-8-sig"))
                if meta is None:
                    continue
                name = str(meta.get("name") or path.stem)
                if not NAME.fullmatch(name):
                    raise ValueError(f"name {name!r} must match {NAME.pattern}")
                max_turns = int(meta.get("max_turns") or DEFAULT_MAX_TURNS)
            except (OSError, ValueError) as broken:
                _note(f"agent definition {path} skipped: {broken}")
                continue
...
AGENTS = find_agents()
```

`find_agents` globs `*.md` under both directories, the way
`skills.find_skills` globs `SKILL.md`. A project definition replaces a
personal one of the same name. The result is a dict of name to
definition: `description`, `tools` (a list, or `None` for every tool),
`max_turns`, `prompt` (the body) and `path`.

`AGENTS = find_agents()` runs at import, and `tools.py` imports this
module, so the definitions are read once, before the first system prompt
is built; a definition added mid-session is a tool from the next start.
For the same reason one bad file must not raise: it would stop the
harness from starting at all. A file without a front matter is skipped
quietly; a file with a broken one prints one line,
`agent definition <path> skipped: <reason>`, and the rest still load.

The front matter, field by field:

| field | type | meaning |
| --- | --- | --- |
| `name` | string matching `[A-Za-z0-9_-]{1,50}`; default: the file's stem | becomes the tool `agent_<name>`. A name with a space or a dot is a skipped file: the API rejects such a tool name on every call. |
| `description` | one line | the tool description, and the line under "The agents are:" in the main system prompt |
| `tools` | a YAML list, or a comma-separated string (`bash, read_file`) | the tools offered; absent means every tool the withheld list allows. A name that is withheld or unknown is left out without a note. |
| `max_turns` | positive integer; default 12 | the cap on the definition's loop. `0` means the default; `many` is a skipped file. |

The body after the closing `---` is the system prompt. A BOM from an
editor is ignored (`utf-8-sig`), and CRLF line ends are fine.

### 2. The tool set of a definition

`harness/agents.py`:

```python
def toolset(definition):
    """The schemas one definition is offered: its list, or everything, minus the withheld tools."""
    from .tools import TOOL_SCHEMAS, active_schemas

    wanted = definition.get("tools")
    chosen = []
    for schema in TOOL_SCHEMAS:
        name = schema["function"]["name"]
        if subagent.withheld(name, allow=EDIT_TOOLS):
            continue
        if wanted is None or name in wanted:
            chosen.append(schema)
    return active_schemas(chosen)
```

The definition names its tools, and the withheld list has the last
word. `subagent.withheld` is new: it is true for every name in
`WITHHELD` and for every name that starts with `agent_`, so a definition
that asks for `task`, `browse`, `ask_user` or another agent does not get
it. The nesting stays one level deep, and the question to the user still
goes through the lead agent. The two edit tools are the exception. The
explorer does without them, but a worker cannot, so a definition may
name them.

`harness/subagent.py`:

```python
AGENT_PREFIX = "agent_"  # the tools built from agent definitions; withheld like task, so agents do not nest


def withheld(name, allow=()):
    """Whether a tool is kept from subagents. allow names the withheld tools a caller lets through."""
    return name.startswith(AGENT_PREFIX) or (name in WITHHELD and name not in allow)
```

The explorer's own `toolset()` uses the same function with no
allowance, so it cannot start an agent either.

Withholding is enforced at execution, not only at the offer. A model
can call a tool it was not offered by naming it - the API does not stop
that - so `loop` hands `execute_all` the names it offered:

```python
    allowed = {s["function"]["name"] for s in tools}  # what it may run == what it was shown
```

```python
        outcomes = execute_all(message.tool_calls, allowed)
```

`decide()` answers any other name with the verdict
`("deny", f"{name} is not available to this agent")`, which `settle`
turns into `Blocked by policy: write_file is not available to this agent`.
So the planner cannot edit, the worker cannot ask the user, and a
definition that calls `agent_worker` from inside a worker gets a denial
back instead of a second level of agents - and its bill.

### 3. From a definition to a tool

`harness/agents.py`:

```python
def run(name, request, tag=None):
    """Run one named agent on one request and return its final message."""
    definition = AGENTS.get(name)
    if definition is None:
        return f"Error: no agent named '{name}'."
    return subagent.loop(
        system_prompt(definition),
        request,
        toolset(definition),
        definition["max_turns"],
        label=f"{name} working",
        tag=tag,
    )


def make_tool(name):
    """The callable behind agent_<name>: one request in, one report out."""

    def agent_tool(request: str) -> str:
        return run(name, request)

    agent_tool.__name__ = tool_name(name)
    agent_tool.__doc__ = f"Run the {name} agent on one request and return its report."
    return agent_tool
...
def register():
    """Add every definition to TOOLS and TOOL_SCHEMAS as agent_<name>. Returns the names."""
    from . import tools as registry  # here, not at the top: tools imports this module

    names = []
    for name in AGENTS:
        full = tool_name(name)
        registry.TOOLS[full] = make_tool(name)
        registry.TOOL_SCHEMAS[:] = [s for s in registry.TOOL_SCHEMAS if s["function"]["name"] != full]
        registry.TOOL_SCHEMAS.append(schema(name))
        names.append(full)
    return names
```

`system_prompt` is the body of the file followed by the working
directory line every subagent gets. `run` is the whole tool: the same
`subagent.loop` the explorer and the browser use, with the definition's
prompt, tool set and turn cap. `make_tool` wraps it as a function of one
argument, `request`, and `schema` builds the matching tool schema with
the definition's description in front. `register` puts both into the
registry. `tools.py` calls it on its last line, after `TOOLS` and `TOOL_SCHEMAS`
exist, so the agent tools are in the registry before the first system
prompt is built. This is the same shape as `mcp_client.register`, which
adds `mcp__<server>__<tool>` entries when a server connects. The main
system prompt lists them through `agents_section()` in `llm.py`, one
line per definition, under a paragraph on when to delegate.

### 4. The plan

`harness/pipeline.py`:

```python
STEP_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*\S)\s*$")     # "1. title" or "1) title"
PARALLEL_RE = re.compile(r"\s*\[parallel\]\s*", re.I)  # the tag that marks an independent step
...
def parse_plan(text):
    """The numbered lines of a plan, in order. Other lines are ignored."""
    steps = []
    for line in (text or "").splitlines():
        match = STEP_RE.match(line)
        if not match:
            continue
        title, tagged = PARALLEL_RE.subn(" ", match.group(2))
        steps.append(Step(int(match.group(1)), " ".join(title.split()), parallel=bool(tagged)))
    return steps


def waves(steps):
    """Group the steps into runs: consecutive [parallel] steps share a wave, every other step is its own."""
    grouped = []
    for step in steps:
        if step.parallel and grouped and grouped[-1][0].parallel:
            grouped[-1].append(step)
        else:
            grouped.append([step])
    return grouped
```

The planner's final message is text, and a program has to read it. The
contract is in the planner's prompt: one step per line, numbered, with
` [parallel]` on a step that does not depend on the one before it. Lines
that do not match are ignored, so a stray sentence does not break the
run, and a message with no numbered line stops the pipeline with the
planner's text on screen. `waves` turns the tags into a schedule: a run
of consecutive `[parallel]` steps is one wave that runs together, and
every other step is a wave of one.

### 5. Work, review, retry

`harness/pipeline.py`:

```python
def run_step(task, steps, step, tag=None):
    """Work one step, review it, and retry once on FAIL. Fills in the step and returns it."""
    notes = None
    for attempt in range(1 + RETRIES):
        step.attempts = attempt + 1
        report = agents.run("worker", work_request(task, steps, step, notes), tag=tag)
        step.reports.append(report)
        review = agents.run("reviewer", review_request(task, steps, step, report), tag=tag)
        step.verdict = verdict_of(review)
        step.notes = " ".join(review.split())
        if step.verdict == "PASS":
            break
        notes = review
    return step
```

One step is one worker run and one reviewer run. The worker's request
carries the task, the whole plan and the one step to do, and on a retry
the reviewer's notes - the whole review text, under "the reviewer
failed". The reviewer's request carries the same plus the worker's
report, and asks for PASS or FAIL as the first word. `RETRIES = 1`: a
FAIL sends the step back to the worker once, with the review as notes,
and a second FAIL stands.

```python
VERDICT_RE = re.compile(r"^\W*(?:verdict|result)?\W*(PASS|FAIL)\b", re.I)  # PASS, **PASS**, "Verdict: PASS"


def verdict_of(review):
    """PASS or FAIL from the first non-empty line of the review; anything else is FAIL."""
    lines = [line for line in (review or "").splitlines() if line.strip()]
    match = VERDICT_RE.match(lines[0]) if lines else None
    return "PASS" if match and match.group(1).upper() == "PASS" else "FAIL"
```

`verdict_of` reads the first non-empty line and accepts the word alone,
`**PASS**`, `PASS.`, `Verdict: PASS` or `Result - PASS`. Anything else
is a FAIL: "Looks fine to me", "The tests PASS but the docs are
missing", an empty review. A reviewer that hedges fails the step, and a
retry costs a worker run and a reviewer run, so the reviewer's prompt
asks for the word first.

### 6. Running the waves

`harness/pipeline.py`:

```python
def missing_agents():
    """The pipeline's agents that have no definition, so the command can stop before the first model call."""
    return [name for name in ("planner", "worker", "reviewer") if name not in agents.AGENTS]
...
def run(task):
    """Plan the task, work and review every step, and return (plan text, steps)."""
    missing = missing_agents()
    if missing:
        return f"Error: no agent named {', '.join(repr(m) for m in missing)}.", []
    plan = agents.run("planner", task, tag="planner")
    steps = parse_plan(plan)
    for wave in waves(steps):
        if len(wave) == 1:
            guarded_step(task, steps, wave[0], tag=f"step {wave[0].number}")
        else:
            subagent.gather([partial(guarded_step, task, steps, step, f"step {step.number}") for step in wave])
    return plan, steps
```

`subagent.gather` is the thread pool that has run parallel `task`
subagents since step 29, with the descriptions factored out: it takes
functions and returns their results in order, at most `MAX_PARALLEL` at
a time. `parallel` now calls it too. A wave of one runs on the calling
thread; a larger wave runs on the pool, each step through its own
worker and reviewer, retries included. `guarded_step` turns a crash in
one step into a FAIL row, so one failure does not sink the wave. The
three definitions are checked up front: with `worker.md` missing, every
step would otherwise fail twice on `Error: no agent named 'worker'`
without a model call.

`harness/subagent.py`:

```python
def gather(functions):
    """Call every function at the same time, MAX_PARALLEL at once; the results come back in order."""
    pool = ThreadPoolExecutor(max_workers=MAX_PARALLEL, thread_name_prefix="subagent")
    futures = [pool.submit(function) for function in functions]
    try:
        while not all(future.done() for future in futures):
            wait(futures, timeout=POLL)  # short waits: Windows delivers a Ctrl-C only between them
        results = [future.result() for future in futures]
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # a queued subagent never starts; a running one finishes alone
        raise
    pool.shutdown(wait=True)
    return results
```

A Ctrl-C during a wave lands on the main thread, which is waiting here.
The pool is dropped, not drained: the steps still queued never start,
the ones running finish on their own threads (their worker keeps
calling the model until its turn cap), and the interrupt goes up to
`chat`, which prints `command interrupted`. The files those workers
wrote stay; `/undo` takes them back.

### 7. The command

`harness/commands.py`:

```python
def run_pipeline(messages, task):
    """Plan, work and review a task with the shipped agents; print the summary table."""
    if not task:
        ui.note("usage: /pipeline <task>")
        return messages
    missing = pipeline.missing_agents()
    if missing:
        ui.note(f"the pipeline needs the {', '.join(missing)} definition(s) in .agents/agents; none ran")
        return messages
    checkpoint.begin_turn(len(messages))  # every edit of the run lands in one turn, so one /undo takes it all back
    plan_text, steps = pipeline.run(task)
    if not steps:
        ui.note(f"the planner returned no numbered steps:\n{plan_text.strip()}")
        return messages
    ui.pipeline(pipeline.summary(steps))
    passed = sum(1 for step in steps if step.verdict == "PASS")
    ui.note(f"pipeline: {len(steps)} step(s), {passed} passed, {len(steps) - passed} failed")
    return messages
```

The pipeline is a command, not a turn: the transcript is returned as it
was. The main agent does not see the plan or the reports; the files are
the result. The consequence: "now fix step 2" in the next turn means
nothing to the main agent, which never saw a step 2 - say what to fix in
terms of the files. What the command does borrow from a turn is a
checkpoint. `begin_turn` before the run puts every edit the workers make
under one turn number, so `/undo` after a bad pipeline restores every
file at once; the transcript cut of that `/undo` is a no-op, since the
run appended nothing. The summary table is one row per step: number,
title, tries, verdict and the reviewer's notes.

## Run it

Prerequisites: Python 3.10+, `API_KEY` in the environment or in
`~/.simple-harness/env`, and the three definitions in
`.agents/agents/` (they ship with this step). Run it from a directory
you are willing to let three agents edit; `/undo` is the way back.

```bash
cd harness/05_recovery/step_36_orchestration
pip install -e .
harness
> /pipeline add a --version flag to cli.py and a test for it
```

```powershell
cd harness/05_recovery/step_36_orchestration
pip install -e .
harness
> /pipeline add a --version flag to cli.py and a test for it
```

### Expected output

The planner's panel appears first, tagged `subagent planner`, and its
final message is the plan:

```text
  subagent planner  add a --version flag to cli.py and a test for it
  ...
  1. Add a --version flag to cli.py that prints the package version
  2. Add test_version.py with a test for the flag [parallel]
  3. Mention the flag in README.md [parallel]
```

Then one panel per worker and reviewer call, tagged `subagent step 1`,
`subagent step 2` and so on. Steps 2 and 3 are one wave, so their
panels interleave: a `step 2` `write_file`, a `step 3` `read_file`, a
`step 2` `bash`, in whatever order the threads finish. An approve prompt
from either one appears in between, with the other's panels around it.
The run ends with the table:

```text
                              pipeline
  ┌──────┬──────────────────────────┬───────┬─────────┬──────────────────┐
  │ step │ title                    │ tries │ verdict │ notes            │
  ├──────┼──────────────────────────┼───────┼─────────┼──────────────────┤
  │    1 │ Add the flag to cli.py   │     1 │ PASS    │ PASS the flag... │
  │    2 │ Add the test             │     2 │ PASS    │ PASS the test... │
  └──────┴──────────────────────────┴───────┴─────────┴──────────────────┘
pipeline: 2 step(s), 2 passed, 0 failed
```

`tries` is 2 where the reviewer failed the first attempt. Type
`/checkpoints`: the run is one turn,
`turn 1    from message 1         3 file(s)  cli.py, test_version.py, README.md`,
and `/undo` takes every file back.

The definitions are tools on their own too. Ask the main agent for a
plan and it calls `agent_planner`; ask it to check a change and it calls
`agent_reviewer`. Add a definition of your own in `.agents/agents/` and
it is a tool from the next start.

Run the offline tests from the repository root:

```bash
python run_tests.py 36
python check_snippets.py 36
```

## Error handling

- A missing definition: `/pipeline` prints
  `the pipeline needs the worker definition(s) in .agents/agents; none ran`
  and makes no model call. A broken definition file is one note at
  start-up and is not a tool.
- A plan with no numbered line: `the planner returned no numbered steps:`
  with the planner's text, and nothing runs.
- A worker or reviewer that crashes - a model call that fails after
  every retry, an exception - is a FAIL row whose notes say why;
  the other steps of the wave go on.
- A tool call inside any agent that has bad arguments, names a tool
  that does not exist, or raises, gets an `Error: ...` result and the
  agent's loop goes on; a call to a tool the agent was not offered gets
  `Blocked by policy: <name> is not available to this agent`. A failing
  command is its output; a command that runs over 60 s is killed with
  its output so far.
- A dead model call inside the pipeline is the note
  `model call failed 5 times, giving up (...)` from that agent, and its
  report reads `(the subagent stopped: ...)`; the reviewer then fails
  the step.
- Ctrl-C during `/pipeline`: `command interrupted`, back to the input
  line. The queued steps never start; the running ones finish on their
  own. `/undo` restores what the run wrote. Ctrl-C during a normal turn
  is the steer prompt of step 35.
- Leaving: `/exit`, `/quit`, Ctrl-D (Ctrl-Z then Enter on Windows) or
  Ctrl-C at the input line.

## Gotchas / What this is not

- The planner's and the reviewer's read-only-ness is prompt-only. Both
  are offered `bash`, and `echo x > app.py` matches no deny rule: it is
  rated `ask`, and `a` at that prompt allows every `echo` for the
  session. `python -c "open('a','w')"` runs after one `a` on `python`.
  The harness enforces the tool list, not what a tool does.
- `/pipeline` in plan mode fails every step: the worker's `write_file`
  goes through `permissions.check` with the mode on `plan`, and gets
  `Blocked by policy: plan mode: write_file is not available until the plan is approved`.
  Switch to `/act` first.
- Parallel steps share one workspace with no lock. Two workers running
  `pytest` at once race on the same files; the `[parallel]` tag is the
  planner's promise that the steps touch different files, and the
  harness does not check it. Their approve prompts come one at a time
  but out of any fixed order.
- A tool name in `tools:` that is withheld or misspelled is dropped
  without a note. `agents.toolset` shows what a definition ends up with.
- The bill: a pipeline of `n` steps is at most `10 + n × 2 × (20 + 10)`
  model calls - the planner's cap, then per step two worker runs of up
  to 20 and two reviewer runs of up to 10.
- The tool named `bash` runs `cmd.exe` on Windows, and there is no
  sandbox there; the workers' commands run with the user's rights.
- Nothing from the run enters the transcript, so `--resume` shows no
  trace of it; `/checkpoints` does.

## What to notice

- A definition is a file, not a module. The prompt, the tool list and
  the turn cap are the three things that differ between subagents, and
  all three are in the front matter or the body.
- The tool is built at import. `tools.py` ends with `agents.register()`,
  so the agent tools sit in `TOOLS` and `TOOL_SCHEMAS` before the first
  system prompt is built, like the MCP tools after `connect_all`.
- The withheld list is one function. `subagent.withheld` covers the
  fixed names and the `agent_` prefix, and both the explorer and the
  definitions use it. A definition can only widen it for the two edit
  tools. And it is enforced twice: the schemas say what is offered, the
  `allowed` set says what may run.
- The plan is parsed, not trusted. Only lines of the form `N. title`
  count. The planner's prompt states the format, and the parser
  tolerates everything else.
- PASS is the only pass. A review whose first line does not carry the
  verdict word is a FAIL, so an unsure reviewer sends the step back
  rather than letting it through.
- One retry. The loop is bounded, like `MAX_TURNS` and `MAX_CALLS`. A
  step that fails twice is a row in the table for the user to read.
- Parallel steps share the workspace. The tag is the planner's promise
  that the steps touch different files. The harness runs them together
  on that promise and does not check it.
- The pipeline is outside the transcript but inside the checkpoints. The
  main agent's context stays clean, and `/undo` still works.

## Diff from step 35

```bash
diff -r ../step_35_human_in_the_loop/harness harness
```

Added: `agents.py` (`AGENT_DIRS`, `PREFIX`, `DEFAULT_MAX_TURNS`,
`EDIT_TOOLS`, `parse`, `find_agents`, `AGENTS`, `tool_name`,
`agents_prompt`, `toolset`, `system_prompt`, `run`, `make_tool`,
`schema`, `register`), `pipeline.py` (`RETRIES`, `STEP_RE`,
`PARALLEL_RE`, `Step`, `parse_plan`, `waves`, `outline`, `verdict_of`,
`work_request`, `review_request`, `run_step`, `guarded_step`, `run`,
`summary`, `missing_agents`, `VERDICT_RE`), `.agents/agents/planner.md`,
`.agents/agents/worker.md`, `.agents/agents/reviewer.md`. Changed:
`subagent.py` (`AGENT_PREFIX`, `withheld`, `gather`, `toolset` and
`parallel` use them), `tools.py` (`agents.register()` at the end),
`llm.py` (`AGENTS_INTRO`, `agents_section`, listed in the system
prompt), `commands.py` (`/pipeline`, `run_pipeline`), `ui.py`
(`pipeline` table, `/pipeline` in the banner). Everything else is
unchanged from step 35.

## What the next step adds

Step 37 adds no code: it is a reading that sets this harness, mechanism
by mechanism, next to five production harnesses. Step 38 runs the
capstone task through it and grades the result.
