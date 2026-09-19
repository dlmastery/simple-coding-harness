"""Step 43 - example project extension: one paragraph of the system prompt.

The paragraph is computed once, when the extension is applied, and joins
the system prompt after the skills index.
"""

import os
from pathlib import Path

SUFFIXES = (".py", ".md", ".txt")
SKIP = (".git", "node_modules", ".venv", "__pycache__")
MAX_FILES = 500  # enough for a project of this size; a bigger one gets an estimate


def word_count(root=None):
    """(files, words) over the project's text files, up to MAX_FILES of them.

    os.walk with pruning, not rglob: a node_modules or .git tree is never
    entered, so start-up does not grow with what the project vendors.
    """
    files = words = 0
    for folder, dirs, names in os.walk(root or Path.cwd()):
        dirs[:] = [d for d in dirs if d not in SKIP]  # pruned in place: os.walk does not descend into them
        for name in names:
            if files >= MAX_FILES:
                return files, words
            path = Path(folder) / name
            if path.suffix in SUFFIXES:
                words += len(path.read_text(encoding="utf-8", errors="replace").split())
                files += 1
    return files, words


def apply(ctx):
    files, words = word_count()
    ctx.prompt_section(
        f"This project has {files} text files with about {words:,} words in them. "
        "Mention the file count when the user asks how big the project is."
    )
