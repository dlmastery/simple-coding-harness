# Step 43 - Extensions

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Make a run inspectable**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 42 - Streaming tool output](../step_42_streaming_tool_output/README.md). Next: [Step 44 - Replay and trace viewer](../step_44_replay_trace/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** one registry, and one way to add to the harness.
`harness/extensions.py` loads every `.agents/extensions/*.py` in the
project and every `~/.simple-harness/extensions/*.py` of the user. Each
file exports `apply(ctx)`, and `ctx` offers five registrations:
`ctx.tool(fn, schema=None, permission="ask")`, `ctx.command(name, help,
fn)`, `ctx.hook(event, fn, matcher="*")`, `ctx.prompt_section(text)` and
`ctx.agent(definition)`. Every registration is recorded, so `/extensions`
lists what each extension added, and a file that fails to import or
raises inside `apply` is skipped with a note and its partial
registrations are taken back. The four loaders the harness already had -
skills from step 4, hooks from step 27, MCP from step 26, agent
definitions from step 36 - are rewritten to go through the same five
calls, so they are extensions too. Two examples ship: `git_tools.py`,
with a `git_diff_summary` tool and a `/status` command, and
`word_count.py`, with one paragraph for the system prompt.

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
│   ├── durability.py                 parse_args, the loop detector and the crash-recovery scan
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

### What breaks without it

Without a record, an add-on that half-applies leaves debris. Say a
project file registers a tool, then raises while registering its
command. Before this step, that tool would stay in `TOOLS` with no row
saying where it came from, offered to the model on every call, and the
only way to find out why the harness had grown a tool would be to grep
the config directories. With the registry, the file's row reads `failed:
KeyError: ...`, the tool is gone, and the rest of the harness is as it
was. The same record is what lets a project extension *replace*
`read_file` for one session and hand the original back on `unload`.

## The code, piece by piece

### 1. The context and the five registrations

`harness/extensions.py`:

```python
class Context:
    """What `apply(ctx)` receives: the five registrations, bound to one extension."""

    def __init__(self, extension):
        self.extension = extension

    def tool(self, fn, schema=None, permission="ask"):
        """Register a tool. Without a schema, one is built from the signature and the docstring.

        permission is how the rules rate a call: "ask" (the default: the
        user approves each call) or "allow" for a tool that only reads.
        """
        from . import tools as registry  # here, not at the top: tools imports this module

        if permission not in ("ask", "allow"):
            raise ValueError(f"permission must be 'ask' or 'allow', not {permission!r}")
        schema = schema or schema_from(fn)
        name = schema["function"]["name"]
        previous = (registry.TOOLS.get(name), find_schema(name), PERMISSIONS.get(name))  # what unload puts back
        registry.TOOLS[name] = fn
        PERMISSIONS[name] = permission
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
read, and their permission into `PERMISSIONS`, which the rules consult.
Commands, hooks and prompt sections live in the registry's own tables,
and the modules that use them read from there. `ctx.agent` stores the
definition in `agents.AGENTS` and then calls `ctx.tool` for its
`agent_<name>` tool, so an agent is one record plus one tool record.

A tool under a name that exists is replaced in place. The old function,
schema and permission are kept in the record, and `unload` puts them
back. That makes an override safe: a project extension can wrap
`read_file` and the model sees it in the same position in the list.

What each call takes and gives:

| Call | What it registers | What the function gets and returns |
|---|---|---|
| `ctx.tool(fn, schema=None, permission="ask")` | a tool the model may call | `fn(**args)` with the call's arguments as keywords; returns a `str`. Anything else is turned into JSON by `tools.run`, `None` into `(no output)`. `permission="allow"` skips the approval prompt; the default asks for every call. |
| `ctx.command(name, help, fn)` | a slash command | `fn(messages, arg)`, `arg` being the text after the name; returns the new message list, or `None` to keep it. |
| `ctx.hook(event, fn, matcher="*")` | a hook on one of `hooks.EVENTS` | `fn(event)` with the event dict - the keys in `hooks.EVENT_KEYS`: `tool_name`, `tool_input`, `tool_result` and `ok` for the tool events, `prompt` for `UserPromptSubmit`, `answer`, `calls`, `blocks`, `ended_by` for `Stop`; returns `None`, `{"block": reason}`, `{"result": ...}` or `{"context": ...}`, as a `python` hook from step 27 does. `matcher` is a `|`-separated list of tool-name globs. |
| `ctx.prompt_section(text)` | a paragraph of the system prompt | a string, or a function called with no arguments each time the prompt is built, so the text can be computed late. |
| `ctx.agent(definition)` | an agent definition and its `agent_<name>` tool | a dict with `name`, `prompt`, and optional `description`, `tools`, `handoffs`; it goes through `agents.normalise`. |

`schema_from(fn)` builds a schema when `apply` passes none: the function
name, the first line of the docstring, and one property per parameter
typed from its annotation, with the parameters that have no default
marked required. It resolves string annotations through
`typing.get_type_hints`, so `from __future__ import annotations` at the
top of an extension does not turn every parameter into a string, and it
skips `*args` and `**kwargs`. An annotation it does not know
(`Optional[int]`, a class of yours) becomes `"string"`; pass a schema by
hand for those. The shipped `git_diff_summary` relies on it.

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


def load_file(path):
    """Import one extension file and apply it. Its name is the file's stem.

    The file's directory is on sys.path while it imports, so it can import a
    `_helpers.py` next to it, and the module is registered in sys.modules
    under `harness_extension_<name>`, as a real import would. A stem that
    names a built-in loader is refused: the record of the real one stays.
    """
    name = path.stem
    if name in RESERVED:
        return _failed(Extension(path.name, path), f"name reserved: {name} is a built-in loader; rename the file")
    module_name = f"harness_extension_{name}"
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as failed:  # noqa: BLE001 - a file that does not import is a failed extension
        sys.modules.pop(module_name, None)
        return _failed(Extension(name, path), f"{type(failed).__name__}: {failed}")
    finally:
        sys.path.remove(str(path.parent))
    return apply_module(name, module, path)


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
module to `apply_module`. While the file imports, its directory is at
the front of `sys.path`, so `from _helpers import X` finds a
`_helpers.py` next to it; `load` skips files that start with `_`, so a
helper is never applied as an extension of its own. The module is put in
`sys.modules` before it runs, as a real import would, so dataclasses,
`pickle` and `typing.get_type_hints` on things it defines work.

Three things can go wrong: the file does not import, it has no `apply`,
or `apply` raises. All three end in `_failed`.

`harness/extensions.py`:

```python
def _failed(extension, why):
    """Mark an extension failed, drop what it registered so far, and say so.

    Only the failed record's own registrations go: an older extension of
    the same name that is still loaded is left alone, and the failed row
    is filed under its file name next to it.
    """
    if EXTENSIONS.get(extension.name) is extension:
        unload(extension.name)
    extension.status = f"failed: {why}"
    extension.registrations = []
    key = extension.name if extension.name not in EXTENSIONS else extension.source
    EXTENSIONS[key] = extension
    _note(f"extension {extension.name!r} skipped: {why}")
    return extension
```

It calls `unload` on the record - only that record, never an older
extension that happens to share the name - marks the status `failed:
<reason>`, keeps the row so `/extensions` can show it, and prints one
note. The tools the file registered before it raised are removed by the
same `unload` that a reload uses, so a half-applied extension leaves
nothing behind. The loader moves on to the next file.

Names collide in two ways, and each has a rule. A project or user file
whose stem is one of the built-in loaders - `skills.py`, `hooks.py`,
`agents.py`, `mcp.py` - is refused before it imports, with the row
`skills.py failed: name reserved: ...`; the real loader, `read_skill`
and the skills index stay. Any other name a later file shares with an
earlier one *replaces* it: `apply_module` unloads the old record first,
so a project file replaces a user file of the same stem, and a second
`load()` replaces every file with its current contents. That second
`load()` is the reload; there is no `/reload` command and no watch on
the files, so after editing an extension, restart the harness.

The order is fixed. `BUILTIN` names the four harness loaders, and
`load_builtin` applies them first. Then `load` reads the user's
directory and then the project's. A later registration under the same
tool name wins, so a project extension can replace a user's, and either
can replace what a built-in registered.

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
    ctx.tool(read_skill, READ_SKILL_SCHEMA, permission="allow")  # reads a file the project shipped: no prompt
    ctx.prompt_section(skills_section)  # a function: rendered when the prompt is built
```

`tools.py` no longer imports `skills`. `llm.py` no longer imports it
either; the template ends with `extensions.prompt_sections()`, which
renders every registered section in order. The section is passed as a
function, not a string, so the index is built when the prompt is built.
`read_skill` says `permission="allow"`: it reads a file the project
shipped, so a prompt per call would be noise.

The other three loaders follow the same shape.

`harness/hooks.py`:

```python
def apply(ctx):
    """The hooks extension: the /hooks command. BUILTIN runs from tools.run(), not as a registered hook."""
    ctx.command("/hooks", "list the hooks configured for each event", list_command)
...
    for hook in extensions.hooks_for(event_name) + load_config().get(event_name, []):
```

`BUILTIN` stays what step 33 made it: the checkpoint capture, run by
`run_builtin` from `tools.run`, after the permission check and the
approval, so a declined edit captures nothing. It is not registered
through the context on purpose: `run_hooks("PreToolUse")` fires in
`decide`, before the approval, and a capture there would be the bug step
33 removed. `apply` registers the `/hooks` command, and `run_hooks` runs
the registered hooks - every hook an extension added, in the order they
were registered - before the config files' hooks. A registered hook is a
plain function called with the event dict, and it answers the way a
`python` hook did: a dict or `None`. A `PostToolUse` event carries `ok`,
`False` when the tool answered with an `Error:` result, so a hook can
tell a failed call from a good one before it replaces the result.
`/hooks` lists the registered hooks with their source, then the built-in
ones, then the config files'.

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
an extension builds by hand come out the same. It also checks the name
(`[A-Za-z0-9_-]`, at most 50 characters, because it becomes a tool
name) and accepts `tools: bash, read_file` as a comma string.

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

That placement has a consequence worth saying plainly: an extension
file runs when `harness.tools` is imported, which is before the banner,
in every mode - `read-only`, `--print`, `harness eval` included. A
cloned repository with a `.agents/extensions/` directory runs that code
on `harness` start. Read what is there before you run it, as you would
a `hooks.json`.

### 5. How an extension tool is run

`harness/permissions.py`:

```python
    if extensions.PERMISSIONS.get(name) == "ask":  # an extension tool that did not declare itself read-only
        return "ask", f"call {name} with {json.dumps(args)[:200]}"
```

The rules have never seen an extension tool, so they cannot rate what it
does. The default is to ask, with the call's arguments in the prompt;
`permission="allow"` is the extension's word that the tool only reads.
Either way the tool runs in the harness process with the harness's
privileges: it is not wrapped in the OS sandbox the way `bash` is, and
`read-only` mode only turns an `ask` into a `deny`, so a tool that says
`allow` and writes anyway is not stopped by the mode. A `PreToolUse`
hook can still refuse it by name.

`harness/tools.py`:

```python
def as_text(result):
    """A tool message must be text; a hook's replacement result goes through this too."""
    if isinstance(result, str):
        return result
    return "(no output)" if result is None else json.dumps(result, default=str)


def call(tool_call, args):
    """Call the tool itself. Never raises: a broken tool is a result, not a crash."""
    name = tool_call.function.name
    if name not in TOOLS:  # decide() refuses these first; call() alone must not raise either
        return f"Error: no tool named {name!r}."
    try:
        return as_text(TOOLS[name](**args))  # name -> function, JSON -> kwargs
    except Exception as e:  # wrong arguments, missing file, anything the tool raises
        return f"Error: {type(e).__name__}: {e}"
```

`call` calls the function with the arguments as keywords, so a tool with
the wrong parameter names gets a `TypeError` and the model reads it as
an `Error:` result. A tool is expected to return a string; one that
returns a dict or a list gets it serialised to JSON, and `None` becomes
`(no output)`, so a forgetful extension cannot break the loop after its
tool ran.

Extension tools land in `TOOL_SCHEMAS`, which is also where the
exploration subagent and every agent definition without a `tools:` list
take their tool set from. So a subagent is offered `git_diff_summary`
too; "the subagent only reads" is true of the built-in tool set, and of
an extension tool only if the extension made it so.

### 6. The commands

`harness/commands.py`:

```python
def extension_list(messages):
    """One row per extension: its name, whether it loaded, where it came from, and what it registered."""
    rows = extensions.summary()
    ui.note("\n".join(rows) if rows else "no extensions loaded (see .agents/extensions)")
    return messages


def registered(command, messages):
    """Run a command an extension registered, or return None when none matches.

    A command that raises is a note, not the end of the chat: the messages
    come back as they were.
    """
    for name, (_, fn) in extensions.COMMANDS.items():
        if command == name or command.startswith(name + " "):
            try:
                result = fn(messages, command[len(name):].strip())
            except Exception as failed:  # noqa: BLE001 - an extension's bug must not take the loop down
                ui.note(f"command {name} failed: {type(failed).__name__}: {failed}")
                return messages
            return messages if result is None else result
    return None
```

`handle` checks its own table first, then `registered`. A registered
command gets the messages and the text after its name, and returns the
messages, or `None` to keep them. A command that raises prints one note
and the chat goes on. The `/hooks` and `/mcp` listings moved out of
`commands.py` into the modules that own them, and reach the prompt line
through this path. The help text merges both tables, so `/status` from
the shipped example is listed next to `/undo`.

### 7. The examples

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
    ctx.tool(git_diff_summary, permission="allow")  # the schema is built from the signature and the docstring; read-only, so no prompt
    ctx.command("/status", "show the git branch and the changed files", status)
```

No schema is written. `staged: bool = False` becomes a boolean property
that is not required, and the docstring becomes the description. The
tool declares `permission="allow"` because `git diff --stat` changes
nothing. The command imports `ui` inside the function, because the
extension is imported while the harness is still importing itself. Its
`git()` helper decodes the output as UTF-8 and turns a missing `git`
into an `Error:` string, so a machine without git gets a result, not a
traceback.

`.agents/extensions/word_count.py` counts the words in the project's
text files once, in `apply`, and registers one sentence about it as a
prompt section. It is the smallest possible extension: one call. It
walks the tree with `os.walk` and prunes `.git`, `node_modules`, `.venv`
and `__pycache__` before descending, so start-up does not grow with what
the project vendors.

## Run it

Prerequisites: Python 3.10+, `API_KEY` (and `BASE_URL`, `MODEL` for a
server other than the default) in the environment or in
`~/.simple-harness/env`. The `/mcp` row needs `pip install mcp` for the
echo server to start; without it the row stays `command /mcp`.

bash:

```bash
pip install -e .
harness
```

PowerShell:

```powershell
pip install -e .
harness
```

Then, at the prompt:

```text
> /extensions
```

Six rows. The four built-in loaders come first, each with `built-in` as
its source and its registrations at the end of the row:

```text
skills       loaded   built-in                             tool read_skill; section skills_section
hooks        loaded   built-in                             command /hooks
agents       loaded   built-in                             tool agent_coder, agent_planner, agent_reviewer, agent_router, agent_worker; agent coder, planner, reviewer, router, worker
mcp          loaded   built-in                             command /mcp; tool mcp__echo__echo, mcp__echo__add
git_tools    loaded   .agents/extensions/git_tools.py      tool git_diff_summary; command /status
word_count   loaded   .agents/extensions/word_count.py     section This project has...
```

The `mcp` row has two states. At import it says `command /mcp`; the two
`mcp__echo__*` tools join it when `connect_all` has started the echo
server at the top of the chat, which is before the first `>` prompt, so
this is the row you see. Without the `mcp` package the server does not
start and the row keeps its first state.

Type `/status` and the branch and the changed files print. Ask the
model `what did I change?` and it calls `git_diff_summary`; the panel
shows the `--stat` lines. Ask `how big is this project?` and the answer
carries the file count from the prompt section:

```text
> what did I change?

  ┌ git_diff_summary {} ──────────────────────────────────────────────
  │  harness/tools.py | 12 ++++++-----
  │  1 file changed, 7 insertions(+), 5 deletions(-)
  └────────────────────────────────────────────────────────────────────

  agent

  One file has uncommitted changes: harness/tools.py, 7 lines added and
  5 removed.

  1,842 prompt (estimate 1,790) · 61 completion · $0.0021
```

Now break one. Create `.agents/extensions/bad.py` with a single line,
`import nothing_here`, and start the harness again. One note prints
before the banner: `extension 'bad' skipped: ModuleNotFoundError: No
module named 'nothing_here'`. `/extensions` shows the row as `bad
failed: ModuleNotFoundError: ...`, and everything else is there. Name
the same file `skills.py` instead and the note reads `extension
'skills.py' skipped: name reserved: skills is a built-in loader; rename
the file`; `read_skill` is still in the tool list.

Run the offline tests from the repository root:

```bash
python run_tests.py 43
python check_snippets.py 43
```

```powershell
python run_tests.py 43
python check_snippets.py 43
```

## Error handling

Nothing in this step crashes the loop; every failure is a string the
model or the user reads.

- **A tool call with broken arguments** (`{not json`, or a JSON array):
  `decide()` answers with the result `Error: the arguments of <name> are
  not a JSON object: ...` and the call never runs. An unknown tool name
  gets `Error: no tool named 'x'.`; a tool that raises gets `Error:
  <ExceptionType>: <message>`; `bash` without a `command` gets `Blocked by
  policy: bash: missing argument 'command'`. Each of them is one tool
  message, so the transcript stays valid and the model's next call reads
  the reason.
- **A failing command** comes back as its output and exit status inside
  the result; a command that runs past `TIMEOUT` (60 s) is killed with
  its process group and the result starts `Timed out after 60s and was
  killed. Output so far:`.
- **An extension that fails** at start is one note and one `failed` row;
  an extension command that raises is one note (`command /x failed:
  ...`) and the messages are unchanged; an extension tool that raises
  or returns a non-string is an `Error:` result or JSON, as above.
- **Ctrl-C** during a model call or the tool calls reads a steering line;
  every call that had no result by then gets `INTERRUPTED` as its result
  before the prompt appears, and the transcript is saved. A second
  Ctrl-C within two seconds leaves the chat. Ctrl-C at the `>` prompt
  leaves too.
- **A dead model call** (no network, a bad key, a 5xx that outlasts the
  four retries) prints `model call failed and will not be retried (...)`
  and ends the turn; the user message stays in the transcript and the
  next line starts a new turn. A budget crossing - `MAX_TURN_CALLS`
  model calls in one turn, `MAX_SESSION_COST`, `MAX_TURN_SECONDS` -
  prints `stopped after ...; say continue to go on`.
- **Leaving:** `/exit`, ctrl-d (ctrl-z then enter on Windows), or ctrl-c
  at the prompt. The transcript is on disk after every message, and
  `harness --resume` opens it; a run that died between a reply and its
  tool results has those calls run on resume (`recover`). A one-shot
  `harness -p "..."` writes no session file unless `--resume` is given.

## Gotchas / What this is not

- **Trust.** An extension is arbitrary Python that runs at start, in
  every mode, from a cloned repository. Its tools run in the harness
  process, outside the OS sandbox `bash` gets, and `read-only` mode
  cannot stop a tool that declares `permission="allow"`. The only fences
  are the approval prompt (the `ask` default), a `PreToolUse` hook that
  refuses the name, and reading the file first.
- **Subagents see extension tools.** Anything in `TOOL_SCHEMAS` that is
  not in `subagent.WITHHELD` is offered to the exploration subagent and
  to agent definitions without a `tools:` list.
- **No reload.** Editing an extension needs a restart. `load()` a second
  time replaces the files in place, and the tests do that, but no
  command exposes it.
- **Name collisions are silent between files.** A project file named
  like a user file replaces it without a note; only the built-in stems
  are refused.
- **`schema_from` is small.** It knows `str`, `int`, `float`, `bool`,
  `list` and `dict`; everything else is a string, and an `Optional[int]`
  is not unwrapped. Pass a schema for anything richer.
- **Windows.** The tool named `bash` runs the command through `cmd.exe`
  when no OS sandbox exists (there is none on Windows), and `git_tools`
  calls `git` directly: without git on the PATH the tool returns `Error:
  git did not run: ...`.
- **This is not a plugin system with isolation.** No versions, no
  dependencies, no separate process. It is one registry and five verbs,
  enough to make the built-in loaders and a project's own additions the
  same kind of thing.

## Diff from step 42

```bash
diff -r ../step_42_streaming_tool_output/harness harness
```

Added: `extensions.py` (`EXTENSION_DIRS`, `BUILTIN`, `RESERVED`,
`KINDS`, `TYPES`, `EXTENSIONS`, `COMMANDS`, `HOOKS`, `PROMPT_SECTIONS`,
`PERMISSIONS`, `Registration`, `Extension`, `Context`, `find_schema`,
`schema_from`, `context`, `apply_module`, `load_file`, `load`,
`load_builtin`, `unload`, `hooks_for`, `prompt_sections`, `label`,
`summary`), `.agents/extensions/git_tools.py`,
`.agents/extensions/word_count.py`. Changed: `skills.py`
(`READ_SKILL_SCHEMA`, `SKILLS_INTRO`, `skills_section`, `apply`),
`hooks.py` (`apply`, `python_hook`, function hooks in `run_hook`,
`run_hooks` reads `extensions.hooks_for`, `list_command`; `BUILTIN`
still holds the checkpoint capture, run by `run_builtin` from
`tools.run`),
`agents.py` (`normalise`, `apply`, `register` through the context),
`mcp_client.py` (`CONTEXT`, `apply`, `register` through the context,
`list_command`), `tools.py` (`read_skill` and its schema removed from
the core tables, `extensions.load_builtin()` and `extensions.load()` in
place of `agents.register()`), `permissions.py` (the
`extensions.PERMISSIONS` rule at the end of `rules`), `llm.py`
(`extensions.prompt_sections()` ends the template; no `skills` import),
`commands.py` (`/extensions`, `extension_list`, `registered`, the
`/hooks` and `/mcp` handlers moved to their modules, the help merges the
registered commands). Everything else, `capstone/` included, is
unchanged from step 42.

## What the next step adds

Step 44 stamps every entry of the session log with the time it was
written and saves the usage, seconds and cost of every model call next
to the reply it produced. Two subcommands read that back: `harness
replay <id>` draws a session again at the recorded pace, and `harness
trace <id> --html FILE` writes it as one page, one row per model call.
