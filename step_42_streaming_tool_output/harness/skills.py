"""Stage 15 - skills, unchanged since stage 9, except that a broken
SKILL.md (bad YAML, no front matter) is skipped with a note instead of
stopping the harness at import.
"""

import re
from pathlib import Path

import yaml

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)

SKILL_DIRS = [
    Path.home() / ".agents" / "skills",  # your skills
    Path.cwd() / ".agents" / "skills",   # this project's skills
]


def find_skills():
    """Glob SKILL.md under every skill dir; name -> {description, path}."""
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            meta = front_matter(path)
            if meta is None:
                continue
            name = str(meta.get("name") or path.parent.name)
            description = " ".join(str(meta.get("description", "")).split())
            skills[name] = {"description": description, "path": path}
    return skills


def front_matter(path):
    """The YAML front matter of a file as a dict, or None (with a note) when it cannot be read."""
    try:
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8-sig", errors="replace"))
        meta = yaml.safe_load(match.group(1)) if match else None
    except (OSError, yaml.YAMLError, ValueError) as failed:
        print(f"skipped {path}: {type(failed).__name__}: {failed}")
        return None
    return meta if isinstance(meta, dict) else None


SKILLS = find_skills()


def skills_prompt():
    """One line per skill: the index that goes into the system prompt."""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8-sig", errors="replace")


if __name__ == "__main__":
    print(skills_prompt())
