# Step 43 - Extensions

**What this step adds:** one registry, and one way to add to the harness.
`harness/extensions.py` loads every `.agents/extensions/*.py` in the
project and every `~/.simple-harness/extensions/*.py` of the user. Each
file exports `apply(ctx)`, and `ctx` offers five registrations:
`ctx.tool(fn, schema)`, `ctx.command(name, help, fn)`, `ctx.hook(event,
fn, matcher="*")`, `ctx.prompt_section(text)` and `ctx.agent(definition)`.
Every registration is recorded, so `/extensions` lists what each
extension added, and a file that fails to import or raises inside
`apply` is skipped with a note and its partial registrations are taken
back. The four loaders the harness already had - skills from step 4,
hooks from step 27, MCP from step 26, agent definitions from step 36 -
are rewritten to go through the same five calls, so they are extensions
too. Two examples ship: `git_tools.py`, with a `git_diff_summary` tool
and a `/status` command, and `word_count.py`, with one paragraph for the
system prompt.

## Files

```text
step_43_extensions/
├── .agents/                          project config the harness loads at start
│   ├── .gitignore                    ignores tool_log.txt written by the PostToolUse hook
│   ├── agents/                       one .md per agent definition: front matter + prompt
│   │   ├── coder.md                  writes, changes and tests code; hands off to reviewer
│   │   ├── planner.md                returns a numbered plan without changing anything
│   │   ├── reviewer.md               checks the diff against one plan step: PASS or FAIL
│   │   ├── router.md                 picks the specialist and hands the conversation off
│   │   └── worker.md                 executes one plan step with the edit tools
│   ├── extensions/                   project extension files, one apply(ctx) each
│   │   ├── git_tools.py              example: a git_diff_summary tool and a /status command
│   │   └── word_count.py             example: one paragraph of the system prompt
│   ├── skills/explain-code/SKILL.md  the stage 4 skill
│   ├── hooks.json                    hook config: which script runs on which event
│   ├── mcp.json                      MCP config: the echo server, started with the chat
│   ├── block_env_writes.py           example PreToolUse hook: refuse to write a .env file
│   ├── log_tool_use.py               example PostToolUse hook: append every tool name to a log
│   ├── mcp_echo_server.py            a tiny MCP server: two tools, stdio transport
│   └── require_tests.py              example Stop hook: a .py edit must be followed by pytest
├── capstone/                         the step 38 capstone, carried forward
│   ├── evals/                        one folder per check: task.md, check.py; _common.py shared
│   ├── reference/                    a hand-written todo API: app.py, test_app.py, README.md
│   ├── run.py                        one headless harness run on the brief, then the eval suite
│   ├── task.md                       the brief: a small todo API in an empty directory
│   ├── report.json                   the recorded run: model, timing, per-check results
│   ├── SCORECARD.md                  the recorded run as a table, 4/5
│   └── transcript.md                 the recorded run's transcript
├── evals/                            one folder per task: task.md, check.py or expect.txt, optional workspace/
├── harness/                          the Python harness
│   ├── __init__.py                   package marker
│   ├── agent.py                      the loop; four ways a turn ends; the harness subcommands
│   ├── agents.py                     agent definitions as an extension; agent_<name> tools
│   ├── ask_user.py                   the ask_user tool: a question, numbered options, the answer
│   ├── browse.py                     the browse tool set, gated by active_schemas()
│   ├── browser.py                    browser tools: one Chromium page driven through Playwright
│   ├── budget.py                     the context budget: where the window goes, when to warn
│   ├── checkpoint.py                 workspace checkpoints: a copy of every file before an edit
│   ├── commands.py                   slash commands; /extensions; registry commands run here too
│   ├── compact.py                    the compaction agent; its note is kept
│   ├── computer.py                   computer use: the screen as a tool
│   ├── config.py                     settings; real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py                    the late injection block: <env>, <plan>, <jobs>, active agent
│   ├── durability.py                 the loop detector and the crash-recovery scan
│   ├── evaluate.py                   the eval runner; run_suite can grade one workspace
│   ├── extensions.py                 the registry: tool, command, hook, prompt_section, agent
│   ├── handoff.py                    handoffs: the conversation moves to another agent definition
│   ├── history.py                    cap / strip / fit: the transcript small enough to send
│   ├── hooks.py                      hooks as an extension; run_hooks over registry and config files
│   ├── instructions.py               project instruction files (AGENTS.md) into the prompt
│   ├── jobs.py                       background jobs: shell commands that keep running
│   ├── llm.py                        the model call; prompt sections come from the registry
│   ├── mcp_client.py                 MCP as an extension; servers start with the chat
│   ├── memory.py                     persistent memory
│   ├── modes.py                      named permission policies, one layer above the rules
│   ├── permissions.py                which tool calls need a human; modes sit above the rules
│   ├── pipeline.py                   the plan, work, review pipeline behind /pipeline
│   ├── plan.py                       plan mode: read-only tools, propose, act after approval
│   ├── prompt.py                     the input line
│   ├── sandbox.py                    an OS sandbox for bash
│   ├── session.py                    append-only JSONL log; handoff entries applied on load
│   ├── skills.py                     skills as an extension: read_skill and the prompt section
│   ├── stop.py                       stop conditions: finish(summary) and the turn budgets
│   ├── streaming.py                  streaming tool output: lines reach the screen as they arrive
│   ├── subagent.py                   subagents: task tool, nested loop with a live panel
│   ├── todos.py                      the plan
│   ├── tools.py                      core tools; TOOLS and TOOL_SCHEMAS filled through extensions
│   └── ui.py                         rich panels, live ToolStream panels for running tools
├── AGENTS.md                         project instructions read into the system prompt
├── test_step.py                      offline tests: extension files in a temp dir, a fake model
├── pyproject.toml                    package metadata; version 0.43.0
└── README.md                         this file
```

## Why one registry

Four steps taught the harness to load things from files. Each one wrote
its own way in. `skills.py` built an index, and `llm.py` called it from
inside the prompt template. `agents.register()` wrote into `TOOLS` and
`TOOL_SCHEMAS` by hand. `mcp_client.register()` did the same, with its
own loop. `hooks.py` kept a `BUILTIN` table next to the config files and
read both on every event. Each path worked. Each was different, and a
fifth kind of add-on would have needed a sixth path.

There are only five things an add-on can give the harness: a tool the
model may call, a command for the prompt line, a hook on an event, a
paragraph of the system prompt, and an agent definition. The registry
names those five and nothing else. A loader that goes through it does
not touch `TOOLS`, `COMMANDS` or the hook list itself; it hands the
registry a function and a name, and the registry files it where the
rest of the harness already looks.

The gain is not fewer lines. It is one place where the answer to "what
did this add?" lives. `/extensions` reads the records. A failed
extension is one row with its reason, and the tools it registered before
it failed are gone, because the record says what to remove. The built-in
loaders get the same treatment for free: `skills` is a row that says
`tool read_skill; section skills_section`, because that is what it
registered.

## The code, piece by piece

### 1. The context and the five registrations

`harness/extensions.py`:

```python
class Context:
    """What `apply(ctx)` receives: the five registrations, bound to one extension."""

    def __init__(self, extension):
        self.extension = extension

    def tool(self, fn, schema=None):
        """Register a tool. Without a schema, one is built from the signature and the docstring."""
        from . import tools as registry  # here, not at the top: tools imports this module

        schema = schema or schema_from(fn)
        name = schema["function"]["name"]
        previous = (registry.TOOLS.get(name), find_schema(name))  # what unload puts back
        registry.TOOLS[name] = fn
        for i, existing in enumerate(registry.TOOL_SCHEMAS):
            if existing["function"]["name"] == name:
                registry.TOOL_SCHEMAS[i] = schema  # in place: the tool keeps its position
                break
        else:
            registry.TOOL_SCHEMAS.append(schema)
        self.extension.record("tool", name, previous)
        return name
...
    def hook(self, event, fn, matcher="*"):
        """Register a hook for one event. fn(event) answers like a python hook: a dict or None."""
        entry = {"matcher": matcher, "function": fn, "source": self.extension.name}
        HOOKS.setdefault(event, []).append(entry)
        self.extension.record("hook", f"{event}:{matcher}", entry)
        return entry

    def prompt_section(self, text):
        """Register a paragraph of the system prompt: a string, or a function that returns one."""
        entry = (self.extension.name, text)
        PROMPT_SECTIONS.append(entry)
```

A `Context` is bound to one `Extension` record. Every call does two
things: it files the registration where the harness reads it, and it
records the registration on the extension. Tools go into `tools.TOOLS`
and `tools.TOOL_SCHEMAS`, the two tables every step since step 2 has
read. Commands, hooks and prompt sections live in the registry's own
tables, and the modules that use them read from there. `ctx.agent`
stores the definition in `agents.AGENTS` and then calls `ctx.tool` for
its `agent_<name>` tool, so an agent is one record plus one tool record.

A tool under a name that exists is replaced in place. The old function
and schema are kept in the record, and `unload` puts them back. That
makes an override safe: a project extension can wrap `read_file` and
the model sees it in the same position in the list.

`schema_from(fn)` builds a schema when `apply` passes none: the function
name, the first line of the docstring, and one property per parameter
typed from its annotation, with the parameters that have no default
marked required. The shipped `git_diff_summary` relies on it.

### 2. Loading, and what a failure does

`harness/extensions.py`:

```python
def apply_module(name, module, path=None):
    """Run one module's apply(ctx) as the extension `name`. Returns the Extension, loaded or failed."""
    if name in EXTENSIONS:
        unload(name)  # a reload replaces what the old copy registered
    extension = EXTENSIONS[name] = Extension(name, path)
    apply = getattr(module, "apply", None)
    if not callable(apply):
        return _failed(extension, "no apply(ctx) function")
    try:
        apply(Context(extension))
    except Exception as failed:  # noqa: BLE001 - one broken extension must not stop the harness
        return _failed(extension, f"{type(failed).__name__}: {failed}")
    return extension
...
def load(dirs=None):
    """Load every *.py under the extension dirs, user first, then project. Returns the extensions loaded."""
    loaded = []
    for directory in EXTENSION_DIRS if dirs is None else dirs:
        for path in sorted(Path(directory).glob("*.py")):
            if path.name.startswith("_"):
                continue  # _helpers.py and the like: imported by extensions, not one itself
            loaded.append(load_file(path))
    return loaded


def load_builtin():
    """Apply the harness's own loaders, in BUILTIN order. Returns the extensions."""
    return [apply_module(name, importlib.import_module(module)) for name, module in BUILTIN]
```

`load_file` imports one file under its own module name and hands the
module to `apply_module`. Three things can go wrong: the file does not
import, it has no `apply`, or `apply` raises. All three end in
`_failed`, which calls `unload` on the record, marks the status `failed:
<reason>`, keeps the row so `/extensions` can show it, and prints one
note. The tools the file registered before it raised are removed by the
same `unload` that a reload uses, so a half-applied extension leaves
nothing behind. The loader moves on to the next file.

The order is fixed. `BUILTIN` names the four harness loaders, and
`load_builtin` applies them first. Then `load` reads the user's
directory and then the project's. A later registration under the same
name wins, so a project extension can replace a user's, and either can
replace what a built-in registered.

### 3. The built-in loaders, before and after

Skills are the smallest loader, so they show the change best. Before
this step, three files knew about skills. `tools.py` imported the
function and listed its schema by hand; `llm.py` called the index from
inside the prompt template:

```text
# step 42, harness/tools.py
from .skills import read_skill
...
    "read_skill": read_skill,

# step 42, harness/llm.py
from .skills import skills_prompt
...
You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
```

After, `skills.py` owns both, and says so in one function.

`harness/skills.py`:

```python
def skills_section():
    """The skills paragraph of the system prompt: the introduction, then the index."""
    return SKILLS_INTRO + "\n\n" + skills_prompt()
...
def apply(ctx):
    """The skills extension: the read_skill tool, and the skill index in the system prompt."""
    ctx.tool(read_skill, READ_SKILL_SCHEMA)
    ctx.prompt_section(skills_section)  # a function: rendered when the prompt is built
```

`tools.py` no longer imports `skills`. `llm.py` no longer imports it
either; the template ends with `extensions.prompt_sections()`, which
renders every registered section in order. The section is passed as a
function, not a string, so the index is built when the prompt is built.

The other three loaders follow the same shape.

`harness/hooks.py`:

```python
def apply(ctx):
    """The hooks extension: the harness's own hooks, and the /hooks command."""
    for event, found in BUILTIN.items():
        for hook in found:
            ctx.hook(event, python_hook(hook["python"]), hook.get("matcher") or "*")
    ctx.command("/hooks", "list the hooks configured for each event", list_command)
...
    for hook in extensions.hooks_for(event_name) + load_config().get(event_name, []):
```

`BUILTIN` stays as the declaration of the checkpoint hook from step 33.
`apply` registers each entry as a function hook, and `run_hooks` runs
the registered hooks - the harness's own and every hook an extension
added - before the config files' hooks, in the order they were
registered. A registered hook is a plain function called with the event
dict, and it answers the way a `python` hook did: a dict or `None`.

`harness/agents.py`:

```python
def apply(ctx):
    """The agents extension: every definition file, as an agent and its agent_<name> tool."""
    for definition in list(AGENTS.values()):
        ctx.agent(definition)


def register():
    """Add every definition in AGENTS to the registry as agent_<name>. Returns the tool names."""
    ctx = extensions.context("agents")
    return [ctx.agent(definition) for definition in list(AGENTS.values())]
```

`find_agents` still reads the files. The tool-building code that
`register()` held - the name, the schema, the two table writes - is gone;
`ctx.agent` does it. `normalise` is new: one function that gives a
definition dict its shape, so a definition from a file and a definition
an extension builds by hand come out the same.

`harness/mcp_client.py`:

```python
def apply(ctx):
    """The MCP extension: the /mcp command now, the tools when connect_all() starts the servers."""
    global CONTEXT
    CONTEXT = ctx
    ctx.command("/mcp", "list the MCP servers, whether each started, and the tools they added", list_command)


def register(server, tools):
    """Add each tool to the registry as mcp__<server>__<tool>, through the mcp extension's context."""
    ctx = CONTEXT or extensions.context("mcp")
```

MCP is the one loader whose registrations arrive late. The servers start
when the chat starts, not when the registry is built, so `apply` keeps
its context and registers the command it can register now. When
`connect_all` has started a server, `register` adds the server's tools
through that same context, and `/extensions` shows them on the `mcp`
row.

### 4. Where the registry is filled

`harness/tools.py`:

```python
extensions.load_builtin()  # skills, hooks, agents, MCP: read_skill, the checkpoint hook, one agent_<name> tool per definition
extensions.load()          # .agents/extensions/*.py and ~/.simple-harness/extensions/*.py, after the built-in ones
```

Two lines at the end of `tools.py`, where `agents.register()` used to
be. `TOOLS` and `TOOL_SCHEMAS` are built from the core tools above them,
then the built-in loaders add theirs, then the extension files add
theirs. The registry is complete when the import ends, before the first
prompt is built, the same as it was for the agent tools.

### 5. The commands

`harness/commands.py`:

```python
def extension_list(messages):
    """One row per extension: its name, whether it loaded, where it came from, and what it registered."""
    rows = extensions.summary()
    ui.note("\n".join(rows) if rows else "no extensions loaded (see .agents/extensions)")
    return messages


def registered(command, messages):
    """Run a command an extension registered, or return None when none matches."""
    for name, (_, fn) in extensions.COMMANDS.items():
        if command == name or command.startswith(name + " "):
            result = fn(messages, command[len(name):].strip())
            return messages if result is None else result
    return None
```

`handle` checks its own table first, then `registered`. A registered
command gets the messages and the text after its name, and returns the
messages, or `None` to keep them. The `/hooks` and `/mcp` listings moved
out of `commands.py` into the modules that own them, and reach the
prompt line through this path. The help text merges both tables, so
`/status` from the shipped example is listed next to `/undo`.

### 6. The examples

`.agents/extensions/git_tools.py`:

```python
def git_diff_summary(staged: bool = False) -> str:
    """Summarise the uncommitted changes: one line per changed file with the lines added and removed."""
    output = git("diff", "--stat", *(["--cached"] if staged else []))
    return output or "no changes"


def status(messages, arg=""):
    """/status: the branch and the short git status."""
    from harness.ui import ui

    branch = git("branch", "--show-current") or "(detached)"
    ui.note(f"branch: {branch}\n" + (git("status", "--short") or "clean"))
    return messages


def apply(ctx):
    ctx.tool(git_diff_summary)  # the schema is built from the signature and the docstring
    ctx.command("/status", "show the git branch and the changed files", status)
```

No schema is written. `staged: bool = False` becomes a boolean property
that is not required, and the docstring becomes the description. The
command imports `ui` inside the function, because the extension is
imported while the harness is still importing itself.

`.agents/extensions/word_count.py` counts the words in the project's
text files once, in `apply`, and registers one sentence about it as a
prompt section. It is the smallest possible extension: one call.

## Run it

```bash
pip install -e .
harness
> /extensions
```

Six rows. The four built-in loaders come first, each with `built-in` as
its source and its registrations at the end of the row:

```text
skills       loaded   built-in                             tool read_skill; section skills_section
hooks        loaded   built-in                             command /hooks; hook PreToolUse:write_file|str_replace
agents       loaded   built-in                             tool agent_coder, agent_planner, agent_reviewer, agent_router, agent_worker; agent coder, planner, reviewer, router, worker
mcp          loaded   built-in                             command /mcp
git_tools    loaded   .agents/extensions/git_tools.py      tool git_diff_summary; command /status
word_count   loaded   .agents/extensions/word_count.py     section This project has...
```

Type `/status` and the branch and the changed files print. Ask the
model `what did I change?` and it calls `git_diff_summary`; the panel
shows the `--stat` lines. Ask `how big is this project?` and the answer
carries the file count from the prompt section.

Now break one. Create `.agents/extensions/bad.py` with a single line,
`import nothing_here`, and start the harness again. One note prints
before the banner: `extension 'bad' skipped: ModuleNotFoundError: No
module named 'nothing_here'`. `/extensions` shows the row as `bad
failed: ModuleNotFoundError: ...`, and everything else is there.

Run the offline tests from the repository root:

```bash
python run_tests.py 43
python check_snippets.py 43
```

## What to notice

- Five verbs are enough. A tool, a command, a hook, a prompt section
  and an agent cover every add-on the harness has grown since step 4,
  and each one is a single method on `ctx`.
- The built-in loaders are not special. They are applied first and from
  a fixed list, and that is the whole difference. `skills` has a row in
  `/extensions` because it registered things, the same as `git_tools`.
- The record is what makes failure safe. `unload` reads the same list
  that `/extensions` prints, so a half-applied extension is taken back
  registration by registration, and nothing it touched is left over.
- `read_skill` moved. It was the third tool in the list because
  `tools.py` listed it there; now it joins after the core tools, when the
  skills extension registers it. The model does not care about the
  order. The tests that check the order of a definition's tools see it
  in its new place.
- Override is in place, and reversible. A tool registered under an
  existing name keeps that name's position, and the old function comes
  back on `unload`. The table the model sees never gains a duplicate.
- MCP registers late, and the context makes that fine. A context is a
  handle to an extension's record; whoever holds it can register at any
  time, and the row shows the result.
- An extension is trusted code, like a hook script. It runs in the
  harness process, at import. Permissions still apply to every tool it
  registers, through `permissions.check` like any other tool.

## Diff from step 42

```bash
diff -r ../step_42_streaming_tool_output/harness harness
```

Added: `extensions.py` (`EXTENSION_DIRS`, `BUILTIN`, `KINDS`, `TYPES`,
`EXTENSIONS`, `COMMANDS`, `HOOKS`, `PROMPT_SECTIONS`, `Registration`,
`Extension`, `Context`, `find_schema`, `schema_from`, `context`,
`apply_module`, `load_file`, `load`, `load_builtin`, `unload`,
`hooks_for`, `prompt_sections`, `label`, `summary`),
`.agents/extensions/git_tools.py`, `.agents/extensions/word_count.py`.
Changed: `skills.py` (`READ_SKILL_SCHEMA`, `SKILLS_INTRO`,
`skills_section`, `apply`), `hooks.py` (`apply`, `python_hook`,
function hooks in `run_hook`, `run_hooks` reads `extensions.hooks_for`,
`list_command`), `agents.py` (`normalise`, `apply`, `register` through
the context), `mcp_client.py` (`CONTEXT`, `apply`, `register` through
the context, `list_command`), `tools.py` (`read_skill` and its schema
removed from the core tables, `extensions.load_builtin()` and
`extensions.load()` in place of `agents.register()`), `llm.py`
(`extensions.prompt_sections()` ends the template; no `skills` import),
`commands.py` (`/extensions`, `extension_list`, `registered`, the
`/hooks` and `/mcp` handlers moved to their modules, the help merges the
registered commands). Everything else, `capstone/` included, is
unchanged from step 42.
