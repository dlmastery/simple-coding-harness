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
echo and other commands it uses to gather information. Every other
command stops and asks the user. If the user approves, the tool call
runs.

The allow / ask design comes from OpenCode. A third verdict, deny, covers
the handful of commands no answer at the prompt should unlock: rm, sudo,
chmod, chown, curl and the like. The last matching rule wins, so the
catch-all goes first.

The rules only see the command text, so anything they cannot read - a
`$(...)` substitution, a backtick, a redirection into a file - is treated
as a reason to ask, never as a reason to allow.

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
what was asked - the tool, for bash the first word of each command part,
for a write outside the project that fact, for the browser the host - is
allowed for the rest of the session. A `never` denies it the same way.
SESSION_RULES holds these answers and is consulted after BASH_RULES, one
command part at a time, and never in plan mode. A deny in BASH_RULES still
wins: no answer at the prompt unlocks rm.
"""

import json
import os
import re
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

from . import modes, plan

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
    # read-only: let them through
    "ls*": "allow", "pwd": "allow", "cd *": "allow", "echo *": "allow",
    "sort*": "allow", "uniq*": "allow", "cut *": "allow", "basename *": "allow", "dirname *": "allow",
    "date*": "allow", "cat *": "allow", "head *": "allow", "tail *": "allow",
    "wc *": "allow", "file *": "allow", "which *": "allow", "grep *": "allow", "rg *": "allow",
    "find *": "allow", "tree*": "allow",
    "git status*": "allow", "git diff*": "allow", "git log*": "allow", "git show*": "allow", "git ls-files*": "allow",
    "pytest*": "allow", "python -m pytest*": "allow",
    # env prints every variable, API_KEY included, straight into the transcript
    "env": "ask",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny",
}

# The rules match a command's first word; these hide another command inside it.
UNREADABLE = re.compile(r"\$\(|`|<\(|>\(")
# An allowed command that writes: a redirection into a file, tee, or find that deletes / runs things.
WRITES = re.compile(r"(?<![0-9&<])>>?(?!&)|\btee\b|\bfind\b.*\s-(delete|exec|execdir|ok|okdir)\b")


SESSION_RULES = {}  # (tool, what was asked) -> "allow" or "deny", from the a and never answers of this session


def first_word(command):
    """The program a command runs: its first word, or an empty string."""
    parts = command.split()
    return parts[0] if parts else ""


def session_keys(name, args):
    """The SESSION_RULES keys one call is filed under: what the prompt asked about.

    One per command part for bash, keyed by its first word. A write outside
    the project is keyed as ("write_file", "outside"), so an answer there
    says nothing about writes inside it. A browser page is keyed by its
    host. Any other tool is keyed by its name alone.
    """
    if name in ("bash", "bash_background"):
        return [("bash", first_word(part)) for part in split_command(args.get("command", ""))]
    if name in ("write_file", "str_replace"):
        return [(name, "outside" if not inside_project(args.get("path", "")) else "")]
    if name == "browser_open":
        return [(name, (urlparse(args.get("url", "")).hostname or "").lower())]
    return [(name, "")]


def session_rules_apply():
    """Whether an always/never answer counts now: not in plan mode, whose answer is always no, and not in read-only mode."""
    return modes.current() not in ("plan", "read-only")


def remembered(name, args):
    """The session rule for this call as (verdict, reason), or None when the rules do not apply."""
    if not session_rules_apply():
        return None
    for key in session_keys(name, args):
        if key in SESSION_RULES:
            return SESSION_RULES[key], f"{SESSION_RULES[key]} for this session: " + " ".join(part for part in key if part)
    return None


def remember(name, args, verdict):
    """Store an always (allow) or never (deny) answer for the rest of the session. Returns what was stored."""
    stored = []
    for key in session_keys(name, args):
        SESSION_RULES[key] = verdict
        stored.append(" ".join(part for part in key if part))
    return f"{verdict} for this session: " + ", ".join(stored)


def split_command(command):
    """Split a compound command on |, ||, ;, &, &&, newlines - but not inside quotes.

    `2>&1` and `>&2` are redirections, not separators, so an & right after
    a > or a digit stays with its command.
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
        elif ch == "&" and current and current[-1] in ">0123456789":
            current.append(ch)
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


def unquoted(part):
    """The command with its quoted strings blanked, so a > inside quotes is not a redirection."""
    return re.sub(r"\"[^\"]*\"|'[^']*'", "", part)


def rate(part):
    """One command's verdict: BASH_RULES, then the session rule for its first word. A deny in BASH_RULES wins.

    An allowed command that writes through a redirection or `tee`, or a
    `find` that deletes or executes, is not read-only any more: ask. The
    session rules are never read in plan mode or read-only mode.
    """
    action = "ask"
    for pattern, rule in BASH_RULES.items():
        if fnmatch(part, pattern):
            action = rule
    if action == "allow" and WRITES.search(unquoted(part)):
        action = "ask"  # `cat a > b` is a write, whatever the verb
    rule = SESSION_RULES.get(("bash", first_word(part))) if session_rules_apply() else None
    if rule and action != "deny":
        action = rule
    return action


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    if UNREADABLE.search(command):
        return "ask"  # we cannot see what runs inside, so a human has to
    verdicts = [rate(part) for part in split_command(command)]
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"


def inside_project(path):
    resolved = Path(path).resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def in_git_dir(path):
    """.git is inside the project, but a hook written there runs on the next git command."""
    resolved = Path(path).resolve()
    return inside_project(path) and ".git" in resolved.relative_to(PROJECT).parts


def describe(name, args):
    """A short reason for a call the rules gave none: the tool and, for an edit, its path."""
    if name in ("write_file", "str_replace"):
        return f"{name} {args.get('path', '')}".strip()
    return name

def check(name, args):
    """Return (action, reason). Action is allow, ask or deny.

    The mode is consulted first. Plan mode denies every tool outside the
    plan tool set before the rules see the call. Then the rules rate the
    call, and the mode's table rewrites an allow or an ask; a deny is
    final. When the mode changed the verdict, the reason says which mode.
    """
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
    if name in ("bash", "bash_background"):
        command = args.get("command", "")
        if not command:
            return "deny", "bash: missing argument 'command'"
        action = decide(command)
        if plan.MODE == "plan" and action == "ask":
            return "deny", f"plan mode: only read-only commands run before the plan is approved: {command}"
        how = "run in background" if name == "bash_background" else "run"
        return action, f"{how}: {command}"

    answer = remembered(name, args)
    if answer:
        return answer

    if name in ("write_file", "str_replace"):
        path = args.get("path", "")
        if not path:
            return "deny", f"{name}: missing argument 'path'"
        if not inside_project(path):
            return "ask", f"{name} outside {PROJECT}: {path}"
        if in_git_dir(path):
            return "ask", f"{name} inside .git: {path}"

    if name == "browser_open":
        url = args.get("url", "")
        if not url:
            return "deny", f"{name}: missing argument 'url'"
        host = (urlparse(url).hostname or "").lower()
        if host in BROWSER_ALLOW:
            return "allow", None
        return "ask", f"open in the browser: {url}"

    if name == "computer_act" and not computer_auto():
        where = f" at ({args.get('x')}, {args.get('y')})" if args.get("x") is not None else ""
        detail = args.get("text") if args.get("text") is not None else args.get("keys")
        return "ask", f"computer: {args.get('action')}{where}" + (f" {detail!r}" if detail is not None else "")

    if name.startswith("mcp__"):
        if any(fnmatch(name, pattern) for pattern in MCP_ALLOW):
            return "allow", None
        return "ask", f"call MCP tool {name} with {json.dumps(args)[:200]}"

    return "allow", None
