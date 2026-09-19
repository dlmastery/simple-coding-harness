"""Stage 12 - skills, unchanged since stage 9.
"""

import re
import sys
from pathlib import Path

import yaml

SKILL_DIRS = [
    Path.home() / ".agents" / "skills",  # your skills
    Path.cwd() / ".agents" / "skills",   # this project's skills
]

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)


def find_skills():
    """Glob SKILL.md under every skill dir; name -> {description, path}.

    One broken skill file must not stop the harness from starting, so a
    file without front matter or with bad YAML is skipped with a note.
    """
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            match = FRONT_MATTER.match(path.read_text(encoding="utf-8", errors="replace"))
            if not match:
                continue
            try:
                meta = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as bad:
                print(f"skipping {path}: {bad}", file=sys.stderr)
                continue
            if not isinstance(meta, dict):
                continue
            name = str(meta.get("name") or path.parent.name)
            description = " ".join(str(meta.get("description", "")).split())
            skills[name] = {"description": description, "path": path}
    return skills


SKILLS = find_skills()


def skills_prompt():
    """One line per skill: the index that goes into the system prompt."""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    print(skills_prompt())
