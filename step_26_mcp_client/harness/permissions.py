"""Step 26 - which tool calls need a human, now including MCP tools.

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
"""

import json
import os
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
    "date*": "allow", "env": "allow", "cat *": "allow", "head *": "allow", "tail *": "allow",
    "wc *": "allow", "file *": "allow", "which *": "allow", "grep *": "allow", "rg *": "allow",
    "find *": "allow", "tree*": "allow",
    "git status*": "allow", "git diff*": "allow", "git log*": "allow", "git show*": "allow", "git ls-files*": "allow",
    "pytest*": "allow", "python -m pytest*": "allow",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny",
}


def split_command(command):
    """Split a compound command on |, ||, ;, &, && - but not inside quotes."""
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
        elif ch in "&|;":
            parts.append("".join(current))
            current = []
            while i + 1 < len(command) and command[i + 1] in "&|":
                i += 1
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        verdicts.append(action)
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"


def inside_project(path):
    resolved = Path(path).resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if name == "bash":
        return decide(args["command"]), f"run: {args['command']}"

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
