"""Which tool calls need a human.

Three verdicts: allow (run silently), ask (stop and show you), deny (never,
even if you would say yes). The sandbox in sandbox.py decides what is
*possible*; these rules decide what is worth *interrupting you* for.

Rules are glob patterns matched against each piece of a compound command.
Last matching rule wins, so the catch-all goes first.
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
    """Split on the separators that actually separate: |, ||, ;, &, &&.

    A naive split also cuts inside quotes, so `grep "a|b" f` would become
    two fragments that match no rule. Anything quoted or escaped is an
    argument, not a separator.
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
    """Return (action, reason) for one tool call."""
    if name == "bash":
        return decide(args.get("command", "")), f"run: {args.get('command', '')}"
    if name in ("write_file", "str_replace") and not inside_project(args.get("path", "")):
        return "ask", f"{name} outside the project: {args.get('path')}"
    return "allow", None
