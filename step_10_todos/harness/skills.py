"""Stage 10 - skills, unchanged since stage 9.
"""

from pathlib import Path

import yaml

SKILL_DIRS = [
    Path.home() / ".agents" / "skills",  # your skills
    Path.cwd() / ".agents" / "skills",   # this project's skills
]


def find_skills():
    """Glob SKILL.md under every skill dir; name -> {description, path}."""
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            _, frontmatter, _ = text.split("---", 2)
            meta = yaml.safe_load(frontmatter) or {}
            if "name" not in meta:
                continue
            description = " ".join(str(meta.get("description", "")).split())
            skills[meta["name"]] = {"description": description, "path": path}
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
