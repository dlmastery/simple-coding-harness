"""Step 39 - a mode sits above the rules. check() asks modes.current()
first: plan mode fences the tool set as before, then the rules rate the
call as they always did (that part is now rules()), and modes.apply
rewrites an allow or an ask the way the mode's table says. A deny is
never rewritten, so a deny rule and a session `never` hold in every
mode, auto included.
The rest is step 35: which tool calls need a human, and which answers to remember.
The session rules are described at the end. The rest is step 29: a
background job is rated by the same bash rules as a foreground command;
the job tools that only look at a job, wait for it or stop it are allowed.

An allow list names the commands the agent may run on its own: ls, pwd,
echo and other read-only commands it uses to gather information. Every
other command stops and asks the user. If the user approves, the tool call
runs.

The allow / ask design comes from OpenCode. A third verdict, deny, covers
the handful of commands no answer at the prompt should unlock: rm, sudo,
chmod, chown, curl and the like. The last matching rule wins, so the
catch-all goes first.

The browser follows the same shape. Opening a URL asks, unless the host is
on the BROWSER_ALLOW list. Reading, clicking and typing on a page that is
already open are allowed: the question was answered when the page opened.

The computer is stricter. Looking at the screen is allowed. Every click,
key press and drag asks, unless COMPUTER_AUTO=1, because the desktop has no
sandbox: a click lands wherever the model said.

An MCP tool is code the harness has never seen, running in another process.
Every call asks, unless the tool's full name matches a glob in MCP_ALLOW.

Plan mode is stricter than any rule. A bash command the rules would ask
about is denied instead: the user is not asked, because in plan mode the
answer is always no. Every tool outside the plan tool set is denied too.

Step 35 adds the session rules. An `a` at the approve prompt means always:
the tool, and for bash the first word of the command, is allowed for the
rest of the session. A `never` denies it the same way. SESSION_RULES holds
these answers and is consulted before BASH_RULES, one command part at a
time. A deny in BASH_RULES still wins: no answer at the prompt unlocks rm.
"""

import json
import os
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

from . import extensions, modes, plan

PROJECT = Path.cwd().resolve()

# a command the rules cannot read: another command inside it, or output sent to a file
HIDDEN = ("$(", "`", "<(", ">(")

# hosts the browser may open without asking, e.g. BROWSER_ALLOW=docs.python.org,pypi.org
BROWSER_ALLOW = {host.strip().lower() for host in os.environ.get("BROWSER_ALLOW", "").split(",") if host.strip()}

# MCP tools that run without asking, as globs on the full name, e.g. MCP_ALLOW=mcp__echo__*,mcp__fs__read_*
MCP_ALLOW = [pattern.strip() for pattern in os.environ.get("MCP_ALLOW", "").split(",") if pattern.strip()]


def computer_auto():
    """COMPUTER_AUTO=1 lets computer_act run without asking. Read per call, so a test can flip it."""
    return os.environ.get("COMPUTER_AUTO", "") == "1"

BASH_RULES = {
    "*": "ask",
    # read-only: let them through
    "ls*": "allow", "pwd": "allow", "cd *": "allow", "echo *": "allow",
    "sort*": "allow", "uniq*": "allow", "cut *": "allow", "basename *": "allow", "dirname *": "allow",
    "date*": "allow", "cat *": "allow", "head *": "allow", "tail *": "allow",
    "wc *": "allow", "file *": "allow", "which *": "allow", "grep *": "allow", "rg *": "allow",
    "find *": "allow", "tree*": "allow",
    "env": "ask",  # prints every secret in the environment: ask
    "git status*": "allow", "git diff*": "allow", "git log*": "allow", "git show*": "allow", "git ls-files*": "allow",
    "pytest*": "allow", "python -m pytest*": "allow",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny",
}


SESSION_RULES = {}  # (tool, what was asked) -> "allow" or "deny", from the a and never answers of this session


def first_word(command):
    """The program a command runs: its first word, or an empty string."""
    parts = command.split()
    return parts[0] if parts else ""


def session_keys(name, args):
    """The SESSION_RULES keys one call is filed under: what the prompt asked about.

    bash: one key per command part, by its first word. An edit outside the
    project: (tool, "outside"), so an always for one stray path does not
    unlock every path. browser_open: the host. Anything else: the tool.
    """
    if name in ("bash", "bash_background"):
        return [("bash", first_word(part)) for part in split_command(args.get("command", ""))]
    if name in ("write_file", "str_replace") and not inside_project(args.get("path", "")):
        return [(name, "outside")]
    if name == "browser_open":
        return [(name, (urlparse(args.get("url", "")).hostname or "").lower())]
    return [(name, "")]


def remember(name, args, verdict):
    """Store an always (allow) or never (deny) answer for the rest of the session. Returns what was stored."""
    stored = []
    for key in session_keys(name, args):
        SESSION_RULES[key] = verdict
        stored.append(" ".join(part for part in key if part))
    return f"{verdict} for this session: " + ", ".join(stored)


def split_command(command):
    """Split a compound command on |, ||, ;, &, &&, and newlines - but not inside quotes.

    The & of a redirection (`2>&1`, `>&2`) is part of its command, not a
    separator.
    """
    parts, current, quote, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if quote:
            current.append(ch)
            quote = None if ch == quote else quote
        elif ch == "\\" and i + 1 < len(command):
            current.extend(command[i : i + 2])
            i += 1
        elif ch in "\"'":
            quote = ch
            current.append(ch)
        elif ch == "&" and current and current[-1] == ">":
            current.append(ch)  # 2>&1: a redirection, not a background job
        elif ch in "&|;\n":
            parts.append("".join(current))
            current = []
            while i + 1 < len(command) and command[i + 1] in "&|":
                i += 1
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def writes(part):
    """Whether an otherwise read-only command part writes somewhere the rules cannot see.

    An unquoted > or >> sends output to a file; `tee` writes its input; a
    find with -delete, -exec or -ok changes what it finds.
    """
    quote = None
    for ch in part:
        if quote:
            quote = None if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == ">":
            return True
    words = part.split()
    if "tee" in words:
        return True
    return words[:1] == ["find"] and any(flag in words for flag in ("-delete", "-exec", "-execdir", "-ok", "-okdir"))


def rate(part):
    """One command's verdict: BASH_RULES, then a session rule. A deny in BASH_RULES wins.

    An allow that writes somewhere (writes()) becomes an ask: `ls > out` is
    not the `ls` the rule meant. Session rules do not apply in plan mode:
    nothing the user allowed in act mode is an exploration.
    """
    action = "ask"
    for pattern, rule in BASH_RULES.items():
        if fnmatch(part, pattern):
            action = rule
    if action == "allow" and writes(part):
        action = "ask"
    remembered = SESSION_RULES.get(("bash", first_word(part))) if plan.MODE != "plan" else None
    if remembered and action != "deny":
        action = remembered
    return action


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins.

    A command with a command inside it - $(...), backticks, <(...) - is an
    ask whatever its parts say: the rules cannot see the inner one.
    """
    verdicts = [rate(part) for part in split_command(command)]
    if any(marker in command for marker in HIDDEN):
        verdicts.append("ask")
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"


def inside_project(path):
    resolved = Path(path).resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def describe(name, args):
    """A short reason for a call the rules gave none: the tool and, for an edit, its path."""
    if name in ("write_file", "str_replace"):
        return f"{name} {args.get('path', '')}".strip()
    return name


def missing(name, args, *keys):
    """The deny verdict for a required argument the call did not carry, or None."""
    for key in keys:
        if args.get(key) is None:
            return "deny", f"{name}: missing argument {key!r}"
    return None


def check(name, args):
    """Return (action, reason). Action is allow, ask or deny.

    The mode is consulted first. Plan mode denies every tool outside the
    plan tool set before the rules see the call, and an agent definition
    with a `tools:` list gets only those. Then the rules rate the call,
    and the mode's table rewrites an allow or an ask; a deny is final.
    When the mode changed the verdict, the reason says which mode.
    """
    from . import handoff  # here, not at the top: handoff imports the agents, which import the tools

    mode = modes.current()
    if mode == "plan" and not plan.offered(name):
        return "deny", f"plan mode: {name} is not available until the plan is approved"
    if not handoff.offered(name):
        return "deny", f"{name} is not available to the {handoff.active_name()} agent"
    action, reason = rules(name, args)
    final = modes.apply(mode, modes.category(name, args, inside_project), action)
    if final != action:
        reason = f"{mode} mode: {reason or describe(name, args)}"
    return final, reason


def rules(name, args):
    """The verdict of the rules alone: (action, reason), as check() gave it before step 39.

    A call without a required argument is denied with a reason that names
    it, so the model fixes the call instead of the harness crashing on it.
    A session rule is read under the key the prompt filed it under, and
    never in plan mode.
    """
    if name in ("bash", "bash_background"):
        problem = missing(name, args, "command")
        if problem:
            return problem
        action = decide(args["command"])
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {args['command']}"
        how = "run in background" if name == "bash_background" else "run"
        return action, f"{how}: {args['command']}"

    if name in ("write_file", "str_replace"):
        problem = missing(name, args, "path")
        if problem:
            return problem
    if name == "browser_open":
        problem = missing(name, args, "url")
        if problem:
            return problem

    if plan.MODE != "plan":
        for key in session_keys(name, args):
            remembered = SESSION_RULES.get(key)
            if remembered:
                return remembered, f"{remembered} for this session: {' '.join(part for part in key if part)}"

    if name in ("write_file", "str_replace") and not inside_project(args["path"]):
        return "ask", f"{name} outside {PROJECT}: {args['path']}"

    if name in ("write_file", "str_replace") and ".git" in Path(args["path"]).parts:
        return "ask", f"{name} inside .git: {args['path']}"

    if name == "browser_open":
        host = (urlparse(args["url"]).hostname or "").lower()
        if host in BROWSER_ALLOW:
            return "allow", None
        return "ask", f"open in the browser: {args['url']}"

    if name == "computer_act" and not computer_auto():
        where = f" at ({args.get('x')}, {args.get('y')})" if args.get("x") is not None else ""
        detail = args.get("text") if args.get("text") is not None else args.get("keys")
        return "ask", f"computer: {args.get('action')}{where}" + (f" {detail!r}" if detail is not None else "")

    if name.startswith("mcp__"):
        if any(fnmatch(name, pattern) for pattern in MCP_ALLOW):
            return "allow", None
        return "ask", f"call MCP tool {name} with {json.dumps(args)[:200]}"

    if extensions.PERMISSIONS.get(name) == "ask":  # an extension tool that did not declare itself read-only
        return "ask", f"call {name} with {json.dumps(args)[:200]}"

    return "allow", None
