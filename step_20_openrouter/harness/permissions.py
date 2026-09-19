"""Stage 15 - which tool calls need a human.

An allow list names the commands the agent may run on its own: ls, pwd,
echo and other read-only commands it uses to gather information. Every
other command stops and asks the user. If the user approves, the tool call
runs.

The allow / ask design comes from OpenCode. A third verdict, deny, covers
the handful of commands no answer at the prompt should unlock: rm, sudo,
chmod, chown, curl and the like. The last matching rule wins, so the
catch-all goes first.
"""

import re
from fnmatch import fnmatch
from pathlib import Path

PROJECT = Path.cwd().resolve()

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
    # env prints every secret in the environment: ask first
    "env": "ask", "env *": "ask",
    # risky: never, even if the user says yes
    "rm *": "deny", "sudo *": "deny", "chmod *": "deny", "chown *": "deny",
    "curl *": "deny", "wget *": "deny",
    "git push*": "deny", "git reset*": "deny", "git clean*": "deny",
}


# Shell syntax the splitter cannot see through: a nested command, or a
# redirection that turns a read-only command into a write.
OPAQUE = ("$(", "`", "<(", ">(")
REDIRECT = re.compile(r"(?<![<>&\d])>|\|\s*tee\b")
FIND_WRITES = re.compile(r"^find\b.*\s-(delete|exec|ok)\b")


def split_command(command):
    """Split a compound command on |, ||, ;, &, &&, newlines - but not inside quotes.

    `2>&1` and `>&` are redirections, not the background operator, so an `&`
    right after `>` stays with its part.
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
    """The part with every quoted string blanked out, so `echo ">"` stays clean."""
    return re.sub(r"\"[^\"]*\"|'[^']*'", '""', part)


def decide(command):
    """Rate every part of a compound command; the strictest verdict wins."""
    if any(marker in command for marker in OPAQUE):
        return "ask"  # a nested command we cannot rate
    verdicts = []
    for part in split_command(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part, pattern):
                action = rule
        # a read-only command that writes after all: `cat a > b`, `ls | tee f`, `find -delete`
        if action == "allow" and (REDIRECT.search(unquoted(part)) or FIND_WRITES.match(part)):
            action = "ask"
        verdicts.append(action)
    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"


def inside_project(path):
    resolved = Path(path).resolve()
    return resolved == PROJECT or PROJECT in resolved.parents


def inside_git_dir(path):
    return ".git" in Path(path).resolve().relative_to(PROJECT).parts if inside_project(path) else False


def check(name, args):
    """Return (action, reason). Action is allow, ask or deny."""
    if name == "bash":
        if "command" not in args:
            return "deny", f"{name}: missing argument 'command'"
        return decide(args["command"]), f"run: {args['command']}"

    if name in ("write_file", "str_replace"):
        if "path" not in args:
            return "deny", f"{name}: missing argument 'path'"
        if not inside_project(args["path"]):
            return "ask", f"{name} outside {PROJECT}: {args['path']}"
        if inside_git_dir(args["path"]):
            return "ask", f"{name} inside .git: {args['path']}"

    return "allow", None
