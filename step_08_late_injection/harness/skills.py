"""Skills: instructions the model can pull in when a task matches.

A skill is a folder holding a SKILL.md with YAML frontmatter:

    ---
    name: release
    description: How to cut a release of this project
    ---
    (the instructions)

Only the name and description go into the system prompt. The body is read on
demand with the read_skill tool. That is the whole trick - progressive
disclosure - and it is why a project can ship fifty skills without spending
fifty skills' worth of context on every call.
"""

from pathlib import Path

import yaml

SKILL_DIRS = [
    Path.cwd() / ".agents" / "skills",   # project skills
    Path.home() / ".agents" / "skills",  # your personal skills
]


def find_skills(dirs=None):
    """name -> {description, path}, project skills first."""
    skills = {}
    for directory in dirs or SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            _, frontmatter, _ = text.split("---", 2)
            meta = yaml.safe_load(frontmatter) or {}
            if "name" not in meta:
                continue
            description = " ".join(str(meta.get("description", "")).split())
            skills.setdefault(meta["name"], {"description": description, "path": path})
    return skills


SKILLS = find_skills()


def skills_prompt():
    """The one-line-per-skill index that goes in the system prompt."""
    if not SKILLS:
        return "(no skills installed)"
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill by name and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'. Available: {', '.join(SKILLS) or 'none'}."
    return SKILLS[name]["path"].read_text(encoding="utf-8")
