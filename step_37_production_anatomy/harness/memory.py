"""Step 25 - persistent memory.

A memory is one markdown file with YAML front matter (name, description,
type) and a body. Two directories hold them, both under the harness home,
never inside the project: one per project and one shared by every project.
The index (one line per memory) goes into the late block; the body is read
on demand with the recall tool, the way skills work.
"""

import re
from pathlib import Path

import yaml

from . import config, session

TYPES = ("user", "project", "feedback", "reference")
SCOPES = ("project", "user")

MEMORY_DIRS = [
    config.HOME / "memory" / session.PROJECT,  # this project's memories
    config.HOME / "memory" / "_user",          # memories that follow you everywhere
]


def slug(name):
    """A safe file name: lower case, letters, digits and dashes only."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return cleaned or "memory"


def parse(text):
    """Split a memory file into (meta, body). Tolerates missing or broken front matter."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, parts[2].lstrip("\n")


def find_memories():
    """Every memory on disk; name -> {description, type, scope, path}.

    The project directory is read first, so a project memory wins over a
    user memory with the same name.
    """
    memories = {}
    for directory, scope in zip(MEMORY_DIRS, SCOPES):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            meta, _ = parse(path.read_text(encoding="utf-8"))
            name = str(meta.get("name") or path.stem)
            if name in memories:
                continue
            memories[name] = {
                "description": " ".join(str(meta.get("description") or "").split()),
                "type": str(meta.get("type") or "project"),
                "scope": scope,
                "path": path,
            }
    return memories


def memory_index():
    """One line per memory: the index that goes into the late block."""
    return "\n".join(f"- {name}: {m['description']}" for name, m in find_memories().items())


def remember(name: str, description: str, content: str, type: str = "project", scope: str = "project") -> str:
    """Write a memory, replacing one of the same name in the same scope. The name is kept as its slug, the file's name."""
    name = slug(name)  # the index key and the file name agree, so recall finds what remember wrote
    if type not in TYPES:
        return f"Error: type must be one of {', '.join(TYPES)}."
    if scope not in SCOPES:
        return f"Error: scope must be one of {', '.join(SCOPES)}."
    directory = MEMORY_DIRS[SCOPES.index(scope)]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slug(name)}.md"
    existed = path.exists()
    front = yaml.safe_dump({"name": name, "description": description, "type": type}, sort_keys=False, allow_unicode=True)
    path.write_text(f"---\n{front}---\n\n{content.strip()}\n", encoding="utf-8")
    return f"{'Replaced' if existed else 'Saved'} {scope} memory '{name}' ({type}) at {path}"


def recall(name: str) -> str:
    """Return the body of a memory."""
    memories = find_memories()
    if name not in memories:
        return f"No memory named '{name}'."
    _, body = parse(memories[name]["path"].read_text(encoding="utf-8"))
    return body.strip() or "(empty memory)"


def forget(name: str) -> str:
    """Delete a memory."""
    memories = find_memories()
    if name not in memories:
        return f"No memory named '{name}'."
    memories[name]["path"].unlink()
    return f"Forgot '{name}'."


MEMORY_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": (
                "Save a durable fact for future sessions: who the user is, how "
                "this project works, a correction the user made, or a pointer "
                "to a resource. Writing the same name again replaces it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Short kebab-case name, unique per memory"},
                    "description": {"type": "string", "description": "One line: what this memory holds"},
                    "content": {"type": "string", "description": "The memory itself, in markdown"},
                    "type": {
                        "type": "string",
                        "enum": list(TYPES),
                        "description": "user: about the person. project: about this codebase. feedback: a correction. reference: a link or pointer.",
                    },
                    "scope": {
                        "type": "string",
                        "enum": list(SCOPES),
                        "description": "project: only this project sees it. user: every project sees it.",
                    },
                },
                "required": ["name", "description", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Read the full body of a memory listed in the <memory> block.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name of the memory"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forget",
            "description": "Delete a memory that turned out to be wrong or no longer matters.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name of the memory"}},
                "required": ["name"],
            },
        },
    },
]

MEMORY_TOOLS = {"remember": remember, "recall": recall, "forget": forget}


if __name__ == "__main__":
    print(memory_index())
