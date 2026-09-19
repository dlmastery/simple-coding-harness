"""Step 38 - decide() and run() never raise: broken arguments, an unknown
tool name and an exception inside a tool all come back as an "Error: ..."
result, so every tool call gets exactly one tool message and the loop goes
on. execute() and execute_all() take the `allowed` set of a subagent, so a
tool that was not offered cannot run by being named. SERIAL calls run one at
a time on the calling thread; APPROVE_LOCK keeps two prompts apart. The
rest is step 36: the agent tools join the
registry at import: agents.register()
runs after TOOLS and TOOL_SCHEMAS are built and adds one agent_<name> per
definition, the way the MCP tools join when their servers start. The rest
is step 35: ask_user joins the registry, and settle() reads the four
answers of the approve prompt: y runs the call, n declines it, a and never
are stored with permissions.remember and then act as y and n. execute_all
can fill a list the caller owns, one result at a time, so a caller that is
interrupted by Ctrl-C sees which calls finished; INTERRUPTED is the result
it records for the rest. The rest is step 32: deferred tools. A tool whose schema is over budget.DEFER_OVER
tokens is offered as a one-line stub with the same name and no parameters.
load_tool(name) returns the full schema and enables the tool for the rest
of the session. active_schemas() applies this to a list of full schemas -
TOOL_SCHEMAS by default - and appends the load_tool schema whenever a stub
is present. decide() answers a call to an unloaded tool with the same
advice, so a model that calls the stub anyway learns to load it first.

TOOLS is what can run; TOOL_SCHEMAS is what the main agent is offered in act
mode, and active_schemas() is the version that goes on the wire. The
browser tools are in the first and not the second: only the browse
subagent is offered them. The computer tools and the memory tools are in
both, and the MCP tools join both when their servers start.
"""

import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import agents, browser, budget, checkpoint, computer, durability, history, hooks, jobs, memory, permissions, plan, sandbox
from .ask_user import ASK_USER_SCHEMA, ask_user
from .browse import BROWSE_SCHEMA, browse
from .permissions import check
from .skills import read_skill
from .subagent import TASK_SCHEMA, task
from .todos import TODO_SCHEMA, write_todos


def bash(command: str) -> str:
    """Run a shell command and return its combined stdout and stderr."""
    try:
        result = sandbox.run(command)
    except subprocess.TimeoutExpired as expired:
        # A slow command is the model's problem to work around, not a reason
        # to take the session down. Hand the failure back as a result.
        partial = (sandbox.text(expired.stdout) + sandbox.text(expired.stderr)).strip()
        return f"Timed out after {expired.timeout}s and was killed. Output so far:\n{partial}"
    return history.cap((result.stdout + result.stderr) or "(no output)")


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return history.cap(f.read())


def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists. Parent directories are made."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return f"Wrote {path}"


def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    if not old_str:
        return "Error: old_str is empty; give the exact text to replace"
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Add surrounding lines to make it unique, "
            "or set allow_multi_edit to replace them all."
        )

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {path}"


# --- deferred tools ------------------------------------------------------------

LOADED = set()   # names of deferred tools the model loaded this session
STUBBED = set()  # names that went on the wire as a stub, so load_tool knows what is deferred

LOAD_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "load_tool",
        "description": (
            "Enable a deferred tool for the rest of the session and return its full "
            "schema. Call it before the first call to any tool whose description "
            "starts with 'deferred'."
        ),
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "The deferred tool's name"}},
            "required": ["name"],
        },
    },
}


def is_deferred(schema):
    """Whether a schema is too big to offer in full before it is loaded."""
    return budget.schema_tokens(schema) > budget.DEFER_OVER


def deferred_names(schemas=None):
    """The names of every deferred tool in schemas, loaded or not. Default: the registry."""
    return [s["function"]["name"] for s in (TOOL_SCHEMAS if schemas is None else schemas) if is_deferred(s)]


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
    """The schemas to put on the wire: full when small or loaded, a stub otherwise.

    Takes a list of full schemas that another filter already chose - the
    plan-mode tool set, a subagent's tool set - so it composes with them.
    load_tool is appended whenever at least one stub is present.
    """
    offered = []
    stubbed = False
    for schema in TOOL_SCHEMAS if schemas is None else schemas:
        if schema["function"]["name"] in LOADED or not is_deferred(schema):
            offered.append(schema)
        else:
            offered.append(stub(schema))
            STUBBED.add(schema["function"]["name"])
            stubbed = True
    if stubbed:
        offered.append(LOAD_TOOL_SCHEMA)
    return offered


def load_tool(name: str) -> str:
    """Enable a deferred tool and return its full schema."""
    schema = next((s for s in TOOL_SCHEMAS if s["function"]["name"] == name), None)
    if schema is None:
        return f"Error: no tool named '{name}'."
    if name not in STUBBED and not is_deferred(schema):
        return f"{name} is not deferred; call it directly."
    LOADED.add(name)
    return f"{name} is enabled for the rest of the session. Its schema:\n" + json.dumps(schema["function"], indent=2)


def reload_from(messages):
    """Rebuild LOADED from the load_tool calls of a resumed transcript, so the tools stay enabled."""
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            if call["function"]["name"] == "load_tool":
                name = durability.parse_args(call).get("name")
                if isinstance(name, str):
                    LOADED.add(name)


def load_first(name):
    """The result for a call to a deferred tool that was not loaded, or None."""
    if name in LOADED or (name not in STUBBED and name not in deferred_names()):
        return None
    return f"Error: {name} is deferred. Call load_tool('{name}') first, then call {name} again with its full arguments."


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "The shell command to run"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path to the file to read"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": "Open a skill by name and return its full instructions.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name of the skill to open"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a file, or overwrite it if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to write"},
                    "content": {"type": "string", "description": "The full contents"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace exact text in a file. old_str must appear exactly once, "
                "so include surrounding lines if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to edit"},
                    "old_str": {"type": "string", "description": "Exact text to find"},
                    "new_str": {"type": "string", "description": "Text to put in its place"},
                    "allow_multi_edit": {"type": "boolean", "description": "Replace every match instead of failing"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    TODO_SCHEMA,
    TASK_SCHEMA,
    BROWSE_SCHEMA,
    ASK_USER_SCHEMA,
    *computer.COMPUTER_SCHEMAS,
    *memory.MEMORY_SCHEMAS,
    *jobs.JOB_SCHEMAS,
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "read_skill": read_skill,
    "load_tool": load_tool,
    "write_todos": write_todos,
    "task": task,
    "browse": browse,
    "ask_user": ask_user,
    "submit_plan": plan.submit_plan,  # runnable, but offered only in plan mode
    **browser.TOOLS,  # runnable, but offered only to the browse subagent
    **computer.COMPUTER_TOOLS,
    **memory.MEMORY_TOOLS,
    **jobs.JOB_TOOLS,
}

agents.register()  # one agent_<name> tool per definition in .agents/agents, in TOOLS and TOOL_SCHEMAS


MAX_WORKERS = 4  # tool calls of one reply that may run at the same time

# calls that must run alone on the calling thread: they prompt, or they drive one browser or one desktop
SERIAL = {"task", "browse", "submit_plan", "ask_user", "handoff_to", "finish"}
APPROVE_LOCK = threading.Lock()  # one approve prompt at a time, however many threads want one

DENIED = "The user denied this tool call."
INTERRUPTED = "The user interrupted this call before it finished; nothing ran or its result is lost. Read the user's next message before retrying."


def serial(name):
    """Whether a call must run on the calling thread, one at a time."""
    return name in SERIAL or name.startswith("browser_") or name.startswith("computer_")


def decide(tool_call, allowed=None):
    """Parse the arguments and rate the call. Returns (args, action, reason).

    Nothing runs here. This is the half of execute() that must stay on the
    main thread, because an `ask` verdict turns into a prompt. The verdict
    is allow, ask or deny from the rules, `blocked` from a PreToolUse hook,
    or `error` when the arguments are not a JSON object. A denied call is
    not offered to the hooks: the rules said no first. A call to a deferred
    tool that was not loaded is `deferred`: it comes from a stub with no
    parameters, so the rules never see its arguments. `allowed`, when given,
    is the set of tool names this caller was offered; any other name is
    denied, so a subagent cannot run a tool by naming it.
    """
    name = tool_call.function.name
    args, problem = durability.parse_args(tool_call, why=True)
    if problem:
        return args, "error", f"Error: the arguments of {name} are not a JSON object: {problem}"
    if allowed is not None and name not in allowed:
        return args, "deny", f"{name} is not available to this agent"
    advice = load_first(name)
    if advice is not None:
        return args, "deferred", advice
    action, reason = check(name, args)
    if action == "deny":
        return args, action, reason
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": name, "tool_input": args})
    if outcome.blocked:
        return args, "blocked", outcome.reason
    return args, action, reason


def run(tool_call, args):
    """Run the tool with already-parsed arguments, then the PostToolUse hooks.

    No permission check here. The checkpoint capture happens first, now
    that the call is approved. A hook that answers with a result replaces
    what the tool returned; the model sees the hook's version, and a hook
    that blocks after the fact turns the result into "Blocked by hook". A
    tool that raises does not take the loop down: the exception becomes an
    Error: result the model can read, the way a failed command does, and so
    does a name that is not in the registry.
    """
    name = tool_call.function.name
    tool = TOOLS.get(name)
    if tool is None:
        result = f"Error: no tool named {name!r}."
    else:
        checkpoint.pre_tool_use({"tool_name": name, "tool_input": args})  # capture before the edit, after the approval
        try:
            result = tool(**args)
        except Exception as failed:  # noqa: BLE001 - a missing file or a wrong argument is the model's problem to fix
            result = f"Error: {type(failed).__name__}: {failed}"
    if not isinstance(result, str):
        result = "(no output)" if result is None else json.dumps(result, default=str)
    outcome = hooks.run_hooks("PostToolUse", {"tool_name": name, "tool_input": args, "tool_result": result, "ok": not result.startswith("Error")})
    if outcome.blocked:
        return f"Blocked by hook: {outcome.reason}"
    if outcome.result is not None:
        result = outcome.result if isinstance(outcome.result, str) else json.dumps(outcome.result)
    if outcome.context:
        result += f"\n<hook>\n{outcome.context}\n</hook>"
    return result


def settle(action, reason, name=None, args=None):
    """Turn a verdict into a result string, or None when the call may run.

    A `deny` never runs, and neither does a call a hook `blocked`, a
    `deferred` tool that was not loaded or an `error` in the arguments. An
    `ask` prompts the user: y runs the call, n declines it, a runs it and
    remembers allow for the tool - and the first word of a bash command -
    for the session, never declines it and remembers deny the same way.
    name and args are what remember() files the answer under.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if action == "deny":
        return f"Blocked by policy: {reason}"
    if action in ("deferred", "error"):
        return reason
    if action == "blocked":
        return f"Blocked by hook: {reason}"
    if action == "ask":
        with APPROVE_LOCK:  # subagents on threads ask too; one prompt at a time
            answer = ui.approve(reason)
            if answer in ("a", "never") and name is not None:
                ui.note("remembered: " + permissions.remember(name, args or {}, "allow" if answer == "a" else "deny"))
        if answer not in ("y", "a"):
            return DENIED
    return None


def execute(tool_call, allowed=None):
    """Run one tool call through the permission layer. Returns (args, result).

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. This is decide,
    settle and run in one step, for callers that want the direct path.
    """
    args, action, reason = decide(tool_call, allowed)
    result = settle(action, reason, tool_call.function.name, args)
    if result is not None:
        return args, result
    return args, run(tool_call, args)


def execute_all(tool_calls, outcomes=None, allowed=None):
    """Run every tool call of one reply. Returns [(args, result)] in the same order.

    One call takes the direct path. Several calls are decided first, one at a
    time on this thread, so the prompts appear in order. Then the allowed
    ones run together in a thread pool - unless one of them is SERIAL, in
    which case the whole reply runs one call at a time, in order, on this
    thread. A denied or declined call gets its message as the result and
    never runs.

    `outcomes`, when given, is the list the results go into, filled as they
    arrive: a (args, result) pair per call, with result None until the call
    has finished. A caller that catches KeyboardInterrupt reads it to see
    which calls have a result and records INTERRUPTED for the others. On a
    Ctrl-C the pool is shut down without waiting: a call that has not
    started never starts, and one that is running finishes on its own.
    `allowed` is passed through to decide().
    """
    outcomes = [] if outcomes is None else outcomes
    if len(tool_calls) == 1:
        outcomes.append(execute(tool_calls[0], allowed))
        return outcomes

    for tool_call in tool_calls:  # (args, result) per call; result is None until it has run
        args, action, reason = decide(tool_call, allowed)
        outcomes.append((args, settle(action, reason, tool_call.function.name, args)))

    pending = [i for i, (_, result) in enumerate(outcomes) if result is None]

    if any(serial(tool_calls[i].function.name) for i in pending):
        for i in pending:  # one at a time, on this thread: a prompt, a browser page or a nested loop needs it
            outcomes[i] = (outcomes[i][0], run(tool_calls[i], outcomes[i][0]))
        return outcomes

    def keep(i):
        """A callback that files the result of call i the moment it is in, on whichever thread ran it."""
        def done(future):
            if future.exception() is None:
                outcomes[i] = (outcomes[i][0], future.result())
        return done

    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = {i: pool.submit(run, tool_calls[i], outcomes[i][0]) for i in pending}
    for i, future in futures.items():
        future.add_done_callback(keep(i))
    try:
        for future in futures.values():
            future.result()  # re-raises the first failure, in call order
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # the queued calls never start; the running ones finish alone
        raise
    pool.shutdown(wait=True)
    return outcomes
