"""Step 31 - project instruction files.

An instruction file is a Markdown file named AGENTS.md, or CLAUDE.md as an
alias, that tells the agent how a project is built, tested and laid out.
find_instructions() looks for one in ~/.simple-harness/, then in every
directory from the git root down to the working directory. Home comes first,
so a project file can override a personal one. instructions_prompt() joins
the files it found, with one header per file, into text that llm.py places
in the system prompt. Each file is cut at MAX_CHARS and says so.
"""

import os
import subprocess
from pathlib import Path

NAMES = ("AGENTS.md", "CLAUDE.md")  # the first one found in a directory wins
HOME = Path.home() / ".simple-harness"
MAX_CHARS = 20_000

LOADED = []  # the paths the last instructions_prompt() call read, in order


def git_root(cwd=None):
    """The top level of the git repository around cwd, or cwd when there is none."""
    cwd = Path(cwd or os.getcwd()).resolve()
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, encoding="utf-8", errors="replace", timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return cwd
    if done.returncode != 0 or not done.stdout.strip():
        return cwd
    return Path(done.stdout.strip()).resolve()


def same(a, b):
    """Whether two paths name the same directory, case-insensitively on Windows."""
    return os.path.normcase(str(a)) == os.path.normcase(str(b))


def search_dirs(cwd=None):
    """Home first, then every directory from the git root down to cwd."""
    cwd = Path(cwd or os.getcwd()).resolve()
    root = git_root(cwd)
    chain = []
    for directory in [cwd, *cwd.parents]:
        chain.append(directory)
        if same(directory, root):
            break
    else:
        chain = [cwd]  # the root is not an ancestor: only the working directory counts
    chain.reverse()
    return [HOME] + [d for d in chain if not same(d, HOME)]


def find_instructions(cwd=None):
    """Every instruction file, in the order it is read: home, root, ..., cwd."""
    found = []
    for directory in search_dirs(cwd):
        for name in NAMES:
            path = directory / name
            if path.is_file():
                found.append(path)
                break  # AGENTS.md and CLAUDE.md are one file under two names
    return found


def label(path, cwd=None):
    """The header name for a file: ~/.simple-harness/... for home, else relative to cwd."""
    cwd = Path(cwd or os.getcwd()).resolve()
    if same(path.parent, HOME):
        return "~/.simple-harness/" + path.name
    try:
        return Path(os.path.relpath(path, cwd)).as_posix()
    except ValueError:  # another drive on Windows: no relative path exists
        return path.as_posix()


def read_instructions(path):
    """The file's text, cut at MAX_CHARS with a note that says so."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")  # -sig: a BOM from a Windows editor is dropped
    if len(text) <= MAX_CHARS:
        return text
    return (
        text[:MAX_CHARS]
        + f"\n\n[truncated: this file has {len(text):,} characters; only the first {MAX_CHARS:,} are shown]"
    )


def render(paths, cwd=None):
    """The files as prompt text, each under a header naming it; empty when there are none."""
    return "\n\n".join(f"# Instructions from {label(path, cwd)}\n\n{read_instructions(path).strip()}" for path in paths)


def instructions_prompt(cwd=None):
    """Discover the files, remember them in LOADED, and render them.

    Only the system prompt builder calls this; anything that just needs the
    text again reads LOADED through render(), so /instructions describes
    the prompt the model has, not the disk as it is now.
    """
    LOADED[:] = find_instructions(cwd)
    return render(LOADED, cwd)


if __name__ == "__main__":
    print(instructions_prompt())
