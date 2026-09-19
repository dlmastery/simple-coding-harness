"""Step 23 - which tool calls need a human, now including the browser.

An allow list names the commands the agent may run on its own: ls, pwd,
echo and other read-only commands it uses to gather information. Every
other command stops and asks the user. If the user approves, the tool call
runs.

The allow / ask design comes from OpenCode. A third verdict, deny, covers
the handful of commands no answer at the prompt should unlock: rm, sudo,
chmod, chown, curl and the like. The last matching rule wins, so the
catch-all goes first.

The rules only see text. Anything that hides a command inside another one -
$(...), backticks, process substitution - or turns a read-only command into a
write - a redirection, `tee`, `find -delete` - is rated ask, whatever the
allow list says.

The browser follows the same shape. Opening a URL asks, unless the host is
on the BROWSER_ALLOW list. Reading, clicking and typing on a page that is
already open are allowed: the question was answered when the page opened.
"""

import os
import re
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

PROJECT = Path.cwd().resolve()

# hosts the browser may open without asking, e.g. BROWSER_ALLOW=docs.python.org,pypi.org
BROWSER_ALLOW = {host.strip().lower() for host in os.environ.get("BROWSER_ALLOW", "").split(",") if host.strip()}

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
    # `env` prints the API key: ask
    "env": "ask",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny",
}

HIDDEN = ("$(", "`", "<(", ">(")  # a command inside a command: the rules cannot see it
WRITES = re.compile(r"(?<![<>&\d])>{1,2}(?!&)|(^|\s|\|)tee(\s|$)")  # a redirection or tee turns a read into a write
FIND_WRITES = re.compile(r"\s-(delete|exec|execdir|ok|okdir)(\s|$)")


def split_command(command):
    """Split a compound command on |, ||, ;, &, &&, newline - but not inside quotes.

    `2>&1` and `>&` are redirections, not separators.
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
        elif ch == "&" and i > 0 and command[i - 1] == ">":
            current.append(ch)  # part of >& or 2>&1
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
    """The part with quoted strings blanked out, so a `>` inside quotes does not count."""
    return re.sub(r"'[^']*'|\"[^\"]*\"", "''", part)


def rate(part):
    """The verdict for one simple command."""
    action = "ask"
    for pattern, rule in BASH_RULES.items():
        if fnmatch(part, pattern):
            action = rule
    if action != "allow":
        return action
    bare = unquoted(part)
    if any(marker in bare for marker in HIDDEN):
        return "ask"
    if WRITES.search(bare):
        return "ask"
    if bare.startswith("find ") and FIND_WRITES.search(bare):
        return "ask"
    return "allow"


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    verdicts = [rate(part) for part in split_command(command)]
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"


def inside_project(path):
    resolved = Path(path).resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def inside_git(path):
    resolved = Path(path).resolve()
    return (PROJECT / ".git") in resolved.parents


def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if name == "bash":
        command = args.get("command", "")
        if not command:
            return "deny", f"{name}: missing argument 'command'"
        return decide(command), f"run: {command}"

    if name in ("write_file", "str_replace"):
        path = args.get("path", "")
        if not path:
            return "deny", f"{name}: missing argument 'path'"
        if not inside_project(path):
            return "ask", f"{name} outside {PROJECT}: {path}"
        if inside_git(path):
            return "ask", f"{name} inside .git: {path}"

    if name == "browser_open":
        url = args.get("url", "")
        if not url:
            return "deny", f"{name}: missing argument 'url'"
        host = (urlparse(url).hostname or "").lower()
        if host in BROWSER_ALLOW:
            return "allow", None
        return "ask", f"open in the browser: {url}"

    return "allow", None
