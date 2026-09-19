"""Step 26 - which tool calls need a human, now including MCP tools.

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
"""

import json
import os
import re
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

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


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    if UNREADABLE.search(command):
        return "ask"  # we cannot see what runs inside, so a human has to
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        if action == "allow" and WRITES.search(unquoted(part)):
            action = "ask"  # `cat a > b` is a write, whatever the verb
        verdicts.append(action)
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


def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if name == "bash":
        command = args.get("command", "")
        if not command:
            return "deny", "bash: missing argument 'command'"
        return decide(command), f"run: {command}"

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
