"""Step 36 - the agent tools join the registry at import: agents.register()
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
TOOL_SCHEMAS by default - records every stub it makes in STUBBED and
appends the load_tool schema whenever a stub is present. decide() answers
a call to an unloaded tool with the same advice, so a model that calls the
stub anyway learns to load it first. relearn() rebuilds LOADED from a
resumed transcript.

TOOLS is what can run; TOOL_SCHEMAS is what the main agent is offered in act
mode, and active_schemas() is the version that goes on the wire. The
browser tools are in the first and not the second: only the browse
subagent is offered them. The computer tools and the memory tools are in
both, and the MCP tools join both when their servers start.

Every tool returns a string. Nothing here raises: bad arguments, an unknown
tool name and an exception inside a tool all come back as the result string,
so the model always gets a result it can read.
"""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, wait

from . import agents, browser, budget, computer, history, hooks, jobs, memory, permissions, plan, sandbox
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
        partial = (expired.stdout or "") + (expired.stderr or "")
        return history.cap(f"Timed out after {expired.timeout}s and was killed. Output so far:\n{partial}")
    return history.cap((result.stdout + result.stderr) or "(no output)")


def read_file(path: str) -> str:
    """Read a file and return its contents."""
    if not os.path.isfile(path):
        return f"Error: {path} is not a file."
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return history.cap(f.read())


def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return f"Wrote {path}"


def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    if not old_str:
        return "Error: old_str is empty."
    if not os.path.isfile(path):
        return f"Error: {path} is not a file."
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

LOADED = set()  # names of deferred tools the model loaded this session
STUBBED = {}    # name -> full schema of every tool active_schemas() has sent as a stub

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
            STUBBED[schema["function"]["name"]] = schema  # so load_tool finds it, wherever the schema came from
            offered.append(stub(schema))
            stubbed = True
    if stubbed:
        offered.append(LOAD_TOOL_SCHEMA)
    return offered


def load_tool(name: str) -> str:
    """Enable a deferred tool and return its full schema.

    The schema comes from STUBBED first, so a tool that only a subagent or
    plan mode offers - submit_plan, the browser tools - loads the same way
    as one from the registry.
    """
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


def relearn(messages):
    """Rebuild LOADED from a resumed transcript: every load_tool call that succeeded.

    LOADED lives in memory, but the transcript still shows the model the
    schema it loaded; without this the first call after --resume would be
    told to load the tool again. Rebuilt, not added to: a tool loaded in a
    turn that /rewind cut away is deferred again.
    """
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
    "ask_user": ask_user,
    "browse": browse,
    "submit_plan": plan.submit_plan,  # runnable, but offered only in plan mode
    **browser.TOOLS,  # runnable, but offered only to the browse subagent
    **computer.COMPUTER_TOOLS,
    **memory.MEMORY_TOOLS,
    **jobs.JOB_TOOLS,
}

agents.register()  # one agent_<name> tool per definition in .agents/agents, in TOOLS and TOOL_SCHEMAS


MAX_WORKERS = 4  # tool calls of one reply that may run at the same time
POLL = 0.2       # seconds between looks at the pool, so a Ctrl-C is seen soon on every OS

DENIED = "The user denied this tool call."
INTERRUPTED = "The user interrupted this call before it finished; nothing ran or its result is lost. Read the user's next message before retrying."

PRE_CONTEXT = {}  # tool call id -> what its PreToolUse hooks added; run() appends it to the result

# Tools whose order matters, or that talk to the user themselves: a reply
# that holds one of these runs sequentially, on the calling thread. The
# browser is one page: open must finish before read, and a click before
# the screenshot that checks it. submit_plan asks the user to approve.
SERIAL = {"task", "browse", "submit_plan", "ask_user", *browser.TOOLS, *computer.COMPUTER_TOOLS}


def decide(tool_call, allowed=None):
    """Parse the arguments and rate the call. Returns (args, action, reason).

    Nothing runs here. This is the half of execute() that must stay on the
    main thread, because an `ask` verdict turns into a prompt. A fourth
    verdict, `error`, carries the message for a call that cannot be used:
    arguments that are not a JSON object, or a name not in the table. A
    fifth, `blocked`, comes from a PreToolUse hook. A denied call is not
    offered to the hooks: the rules said no first. A call to a deferred
    tool that was not loaded is `deferred`: it comes from a stub with no
    parameters, so the rules never see its arguments.
    """
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError("not an object")
    except ValueError as e:  # the model wrote broken JSON
        return {}, "error", f"Error: the arguments of {name} are not a JSON object: {e}"
    if allowed is not None and name not in allowed:  # offered set == executable set
        return args, "deny", f"{name} is not available to this agent"
    if name not in TOOLS:  # a name that is not in the table
        return args, "error", f"Error: no tool named {name!r}."
    advice = load_first(name)
    if advice is not None:
        return args, "deferred", advice
    action, reason = check(name, args)
    if action == "deny":
        return args, action, reason
    outcome = hooks.run_hooks("PreToolUse", {"tool_name": name, "tool_input": args})
    if outcome.blocked:
        return args, "blocked", outcome.reason
    if outcome.context:
        PRE_CONTEXT[tool_call.id] = outcome.context
    return args, action, reason


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


def run(tool_call, args):
    """Run the tool with already-parsed arguments, then the PostToolUse hooks.

    No permission check here. The event says whether the tool succeeded
    (`ok`: the result is not an Error:). A hook that answers with a result
    replaces what the tool returned; one that blocks cannot undo the tool,
    so the model is told the hook rejected the outcome; any context, from
    the hooks before or after the call, rides along in a <hook> block.
    """
    hooks.run_builtin("PreToolUse", {"tool_name": tool_call.function.name, "tool_input": args})  # the checkpoint capture, once the call is allowed
    result = call(tool_call, args)
    event = {"tool_name": tool_call.function.name, "tool_input": args, "tool_result": result, "ok": not result.startswith("Error")}
    outcome = hooks.run_hooks("PostToolUse", event)
    if outcome.blocked:
        result = f"Blocked by hook: {outcome.reason}"
    elif outcome.result is not None:
        result = as_text(outcome.result)
    context = "\n".join(c for c in (PRE_CONTEXT.pop(tool_call.id, ""), outcome.context) if c)
    if context:
        result += f"\n<hook>\n{context}\n</hook>"
    return result


def settle(action, reason, name=None, args=None):
    """Turn a verdict into a result string, or None when the call may run.

    A `deny` never runs, and neither does a call a hook `blocked`, or a
    `deferred` tool that was not loaded. An `ask` prompts the user: y runs
    the call, n declines it, a runs it and remembers allow for the tool -
    and the first word of a bash command - for the session, never declines
    it and remembers deny the same way. name and args are what remember()
    files the answer under. An `error` is already its own result.
    """
    from .ui import ui  # here, not at the top: ui imports todos, tools imports ui

    if action in ("error", "deferred"):
        return reason
    if action == "deny":
        return f"Blocked by policy: {reason}"
    if action == "blocked":
        return f"Blocked by hook: {reason}"
    if action == "ask":
        answer = ui.approve(reason)
        if answer in ("a", "never") and name is not None:
            ui.note("remembered: " + permissions.remember(name, args or {}, "allow" if answer == "a" else "deny"))
        if answer not in ("y", "a"):
            return DENIED
    return None


def execute(tool_call, allowed=None):
    """Turn one tool call into (args, result). Never raises: whatever goes
    wrong becomes the result string, so the model reads it and tries again.

    Shared by the main loop and by subagents, so a subagent is fenced in by
    exactly the same rules - it is not a way around them. `allowed` is the
    set of tool names the caller offered; a call outside it is denied. This
    is decide, settle and run in one step, for callers that want the direct path.
    """
    args, action, reason = decide(tool_call, allowed)
    result = settle(action, reason, tool_call.function.name, args)
    if result is not None:
        return args, result
    return args, run(tool_call, args)


def execute_all(tool_calls, allowed=None, outcomes=None):
    """Run every tool call of one reply. Returns [(args, result)] in the same order.

    One call takes the direct path, and so does a batch that holds a SERIAL
    tool: its order matters, or it asks the user itself, so it cannot share
    a pool. Otherwise the calls are decided first, one at a time on this
    thread, so the prompts appear in order. Then the allowed ones run
    together in a thread pool. A denied or declined call gets its message as
    the result and never runs.

    `outcomes`, when given, is the list the results go into, filled as they
    arrive: a (args, result) pair per call, with result None until the call
    has finished. A caller that catches KeyboardInterrupt reads it to see
    which calls have a result and records INTERRUPTED for the others. On a
    Ctrl-C the pool is shut down without waiting: a call that has not
    started never starts, and one that is running finishes on its own.
    """
    outcomes = [] if outcomes is None else outcomes
    if len(tool_calls) == 1 or any(c.function.name in SERIAL for c in tool_calls):
        for tool_call in tool_calls:
            outcomes.append(execute(tool_call, allowed))
        return outcomes

    for tool_call in tool_calls:  # (args, result) per call; result is None until it has run
        args, action, reason = decide(tool_call, allowed)
        outcomes.append((args, settle(action, reason, tool_call.function.name, args)))

    pending = [i for i, (_, result) in enumerate(outcomes) if result is None]

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
        while not all(future.done() for future in futures.values()):
            wait(futures.values(), timeout=POLL)  # short waits: Windows delivers a Ctrl-C only between them
        for future in futures.values():
            future.result()  # re-raises the first failure, in call order
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)  # the queued calls never start; the running ones finish alone
        raise
    pool.shutdown(wait=True)
    return outcomes
