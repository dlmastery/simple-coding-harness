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
these answers and is consulted after BASH_RULES, one command part at a
time. A deny in BASH_RULES still wins: no answer at the prompt unlocks rm.
The key is what was asked: an edit outside the project is filed under
(tool, "outside"), a browser_open under its host. In plan mode and in
read-only mode the session rules are not consulted: the mode's answer is
always no, and an `always` from act mode must not unlock a command there.

The rules only see the command text, so a few shapes they cannot read are
rated ask whatever the first word: a command substitution `$(...)` or a
backtick, a process substitution, and an allowed command that redirects
its output with `>` or pipes it into tee. `find` with -delete or -exec asks
too. That is what makes read-only and plan mode really read-only: the ask
becomes a deny there.
"""

import json
import os
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

from . import handoff, modes, plan

PROJECT = Path.cwd().resolve()

# hosts the browser may open without asking, e.g. BROWSER_ALLOW=docs.python.org,pypi.org
BROWSER_ALLOW = {host.strip().lower() for host in os.environ.get("BROWSER_ALLOW", "").split(",") if host.strip()}

# MCP tools that run without asking, as globs on the full name, e.g. MCP_ALLOW=mcp__echo__*,mcp__fs__read_*
MCP_ALLOW = [pattern.strip() for pattern in os.environ.get("MCP_ALLOW", "").split(",") if pattern.strip()]


def computer_auto():
    """COMPUTER_AUTO=1 lets computer_act run without asking. Read per call, so a test can flip it."""
    return os.environ.get("COMPUTER_AUTO", "") == "1"

BASH_RULES = {
    "*": "ask",
    # read-only: let them through (env is not here: it prints the API key)
    "ls*": "allow", "pwd": "allow", "cd *": "allow", "echo *": "allow",
    "sort*": "allow", "uniq*": "allow", "cut *": "allow", "basename *": "allow", "dirname *": "allow",
    "date*": "allow", "cat *": "allow", "head *": "allow", "tail *": "allow",
    "wc *": "allow", "file *": "allow", "which *": "allow", "grep *": "allow", "rg *": "allow",
    "find *": "allow", "tree*": "allow",
    "git status*": "allow", "git diff*": "allow", "git log*": "allow", "git show*": "allow", "git ls-files*": "allow",
    "pytest*": "allow", "python -m pytest*": "allow",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny",
}


SESSION_RULES = {}  # (tool, first word) -> "allow" or "deny", from the a and never answers of this session


def first_word(command):
    """The program a command runs: its first word, or an empty string."""
    parts = command.split()
    return parts[0] if parts else ""


def session_keys(name, args):
    """The SESSION_RULES keys one call is filed under: what the prompt asked about.

    One per command part for bash; (tool, "outside") for an edit outside
    the project, so an always for one file outside does not unlock the
    tool inside; the host for browser_open; the tool name for the rest.
    """
    if name in ("bash", "bash_background"):
        return [("bash", first_word(part)) for part in split_command(args.get("command", ""))]
    if name in ("write_file", "str_replace") and not inside_project(args.get("path", "")):
        return [(name, "outside")]
    if name == "browser_open":
        return [(name, (urlparse(args.get("url", "")).hostname or "").lower())]
    return [(name, "")]


def session_rules_apply():
    """Whether an always/never answer counts now: not in plan mode, not in read-only mode."""
    return modes.current() not in ("plan", "read-only")


def remember(name, args, verdict):
    """Store an always (allow) or never (deny) answer for the rest of the session. Returns what was stored."""
    stored = []
    for key in session_keys(name, args):
        SESSION_RULES[key] = verdict
        stored.append(" ".join(part for part in key if part))
    return f"{verdict} for this session: " + ", ".join(stored)


def split_command(command):
    """Split a compound command on |, ||, ;, &, &&, newline - but not inside quotes.

    The & of a redirection (`2>&1`, `>&2`) is part of the redirection, not
    a separator.
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
            current.append(ch)  # 2>&1: a redirection, not a background &
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


def unquoted(part, chars):
    """Whether any of `chars` appears in the part outside quotes. `2>&1` does not count as a `>`."""
    quote = None
    for i, ch in enumerate(part):
        if quote:
            quote = None if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch in chars and not (ch == ">" and part[i + 1 : i + 2] == "&"):
            return True
    return False


def writes(part):
    """Whether an otherwise read-only command would write: a redirection, tee, or find that deletes or execs."""
    if unquoted(part, ">") or first_word(part) == "tee":
        return True
    return first_word(part) == "find" and any(w in ("-delete", "-exec", "-execdir", "-ok", "-okdir") for w in part.split())


def opaque(command):
    """Whether the command hides a command inside another: $(...), backticks, <(...), >(...)."""
    return any(marker in command for marker in ("$(", "`", "<(", ">("))


def rate(part):
    """One command's verdict: BASH_RULES, then a session rule. A deny in BASH_RULES wins.

    An allowed command that writes - a redirection, tee, find -delete - is
    an ask: the rules know cat, not cat > file.
    """
    action = "ask"
    for pattern, rule in BASH_RULES.items():
        if fnmatch(part, pattern):
            action = rule
    if action == "allow" and writes(part):
        action = "ask"
    remembered = SESSION_RULES.get(("bash", first_word(part))) if session_rules_apply() else None
    if remembered and action != "deny":
        action = remembered
    return action


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    if opaque(command):
        return "ask"  # a command inside a command: the parts cannot be read
    verdicts = [rate(part) for part in split_command(command)]
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"


def inside_project(path):
    resolved = Path(path).resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def inside_git(path):
    """Whether a path is under a .git directory: an edit there asks."""
    resolved = Path(path).resolve()
    return any(parent.name == ".git" for parent in [resolved, *resolved.parents])


def describe(name, args):
    """A short reason for a call the rules gave none: the tool and, for an edit, its path."""
    if name in ("write_file", "str_replace"):
        return f"{name} {args.get('path', '')}".strip()
    return name


def check(name, args):
    """Return (action, reason). Action is allow, ask or deny.

    The mode is consulted first. Plan mode denies every tool outside the
    plan tool set before the rules see the call, and so does the active
    agent's `tools:` list after a handoff (step 40). Then the rules rate the
    call, and the mode's table rewrites an allow or an ask; a deny is
    final. When the mode changed the verdict, the reason says which mode.
    """
    mode = modes.current()
    if mode == "plan" and not plan.offered(name):
        return "deny", f"plan mode: {name} is not available until the plan is approved"
    if not handoff.offered(name):
        return "deny", f"{handoff.active_name()} agent: {name} is not in its tool list"
    action, reason = rules(name, args)
    final = modes.apply(mode, modes.category(name, args, inside_project), action)
    if final != action:
        reason = f"{mode} mode: {reason or describe(name, args)}"
    return final, reason


def required(name, args):
    """The argument a rule reads and the model left out, or None."""
    needs = {"bash": "command", "bash_background": "command", "write_file": "path", "str_replace": "path", "browser_open": "url"}
    key = needs.get(name)
    return key if key is not None and not isinstance(args.get(key), str) else None


def rules(name, args):
    """The verdict of the rules alone: (action, reason), as check() gave it before step 39."""
    missing = required(name, args)
    if missing is not None:
        return "deny", f"{name}: missing argument {missing!r}"

    if name in ("bash", "bash_background"):
        action = decide(args["command"])
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {args['command']}"
        how = "run in background" if name == "bash_background" else "run"
        return action, f"{how}: {args['command']}"

    remembered = SESSION_RULES.get(session_keys(name, args)[0]) if session_rules_apply() else None
    if remembered:
        return remembered, f"{remembered} for this session: {name}"

    if name in ("write_file", "str_replace") and inside_git(args["path"]):
        return "ask", f"{name} inside .git: {args['path']}"

    if name in ("write_file", "str_replace") and not inside_project(args["path"]):
        return "ask", f"{name} outside {PROJECT}: {args['path']}"

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

    return "allow", None
