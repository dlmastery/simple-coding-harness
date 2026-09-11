"""The allow / ask / deny table from step 11, unchanged.

Every SDK port in steps 16-19 reuses this file. The point of keeping it
identical is that policy is *yours* whichever harness runs the loop: the SDK
supplies the hook, you supply the rules.
"""

from fnmatch import fnmatch
from pathlib import Path

PROJECT = Path.cwd().resolve()

BASH_RULES = {
    "*": "ask",
    # read-only: let them through
    "ls*": "allow", "pwd": "allow", "cat *": "allow", "head *": "allow", "tail *": "allow",
    "wc *": "allow", "grep *": "allow", "rg *": "allow", "find *": "allow", "tree*": "allow",
    "which *": "allow", "echo *": "allow", "sort*": "allow", "uniq*": "allow", "cut *": "allow",
    "git status*": "allow", "git diff*": "allow", "git log*": "allow", "git show*": "allow",
    "git branch*": "allow", "git ls-files*": "allow",
    "pytest*": "allow", "python -m pytest*": "allow",
    # risky: never, whatever the user says at the prompt
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny", "git checkout -- *": "deny",
}


def split_command(command):
    """Split on |, ||, ;, &, && - but not inside quotes."""
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
    resolved = Path(path or ".").resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def check_bash(command):
    """(verdict, reason) for a shell command."""
    return decide(command), f"run: {command}"


def check_edit(path):
    """(verdict, reason) for a file edit: ask when it leaves the project."""
    if inside_project(path):
        return "allow", None
    return "ask", f"edit outside the project: {path}"
