"""Step 43 - example project extension: a git_diff_summary tool and a /status command.

The harness imports this file from .agents/extensions and calls apply(ctx)
once. Everything registered here is listed by /extensions.
"""

import subprocess


def git(*args):
    """Run one git command in the current directory and return its output without the trailing newline."""
    try:
        completed = subprocess.run(["git", *args], capture_output=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError) as failed:  # no git on this machine, or it hung
        return f"Error: git did not run: {failed}"
    return (completed.stdout + completed.stderr).rstrip()


def git_diff_summary(staged: bool = False) -> str:
    """Summarise the uncommitted changes: one line per changed file with the lines added and removed."""
    output = git("diff", "--stat", *(["--cached"] if staged else []))
    return output or "no changes"


def status(messages, arg=""):
    """/status: the branch and the short git status."""
    from harness.ui import ui

    branch = git("branch", "--show-current") or "(detached)"
    ui.note(f"branch: {branch}\n" + (git("status", "--short") or "clean"))
    return messages


def apply(ctx):
    ctx.tool(git_diff_summary, permission="allow")  # the schema is built from the signature and the docstring; read-only, so no prompt
    ctx.command("/status", "show the git branch and the changed files", status)
