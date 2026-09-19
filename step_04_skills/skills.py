"""Stage 4 - skill discovery and reading.

Skills are markdown documents placed in a known folder. Each has YAML
front matter with a name and a description; only those two lines go into
the system prompt. The body is read on demand with the read_skill tool,
and that is the only time the model sees the full instructions.
"""

import re
import sys
from pathlib import Path

import yaml

SKILL_DIRS = [
    Path.home() / ".agents" / "skills",  # your skills
    Path.cwd() / ".agents" / "skills",   # this project's skills
]

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)  # the block between the two --- lines


def find_skills():
    """Glob SKILL.md under every skill dir; name -> {description, path}.
    A broken file is skipped with a note: one bad skill must not stop the agent."""
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
            if not match:
                continue
            try:
                meta = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as e:
                print(f"skipping {path}: bad front matter ({e})", file=sys.stderr)
                continue
            if not isinstance(meta, dict):
                continue
            name = str(meta.get("name") or path.parent.name)
            description = " ".join(str(meta.get("description", "")).split())
            skills[name] = {"description": description, "path": path}  # later dirs override earlier ones
    return skills


SKILLS = find_skills()


def skills_prompt():
    """One line per skill: the index that goes into the system prompt."""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8")


if __name__ == "__main__":
    print(skills_prompt())
