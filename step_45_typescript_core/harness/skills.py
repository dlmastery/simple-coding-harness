"""Step 43 - skills are an extension. apply(ctx) registers the read_skill
tool and the skill index as a section of the system prompt, through the
same registry every other extension uses. Before this step, tools.py
imported read_skill and listed its schema by hand, and llm.py called
skills_prompt() inside the prompt template. The finding of the skills is
unchanged since step 4.
"""

import re
from pathlib import Path

import yaml

FRONT_MATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)  # the block between the first two --- lines

SKILL_DIRS = [
    Path.home() / ".agents" / "skills",  # your skills
    Path.cwd() / ".agents" / "skills",   # this project's skills
]

READ_SKILL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_skill",
        "description": "Open a skill by name and return its full instructions.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Name of the skill to open"}},
            "required": ["name"],
        },
    },
}

SKILLS_INTRO = """You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it."""


def find_skills():
    """Glob SKILL.md under every skill dir; name -> {description, path}."""
    skills = {}
    for directory in SKILL_DIRS:
        for path in sorted(directory.glob("*/SKILL.md")):
            try:
                match = FRONT_MATTER.match(path.read_text(encoding="utf-8-sig"))
                meta = yaml.safe_load(match.group(1)) if match else None
            except (OSError, yaml.YAMLError) as failed:  # one bad file is a note, not a start-up failure
                _note(f"skill {path.parent.name} skipped: {failed}")
                continue
            if not isinstance(meta, dict):
                continue
            name = str(meta.get("name") or path.parent.name)  # the folder names the skill when the front matter does not
            description = " ".join(str(meta.get("description", "")).split())
            skills[name] = {"description": description, "path": path}
    return skills


def _note(text):
    from .ui import ui  # here, not at the top: ui imports todos, tools imports this module

    ui.note(text)


SKILLS = find_skills()


def skills_prompt():
    """One line per skill: the index that goes into the system prompt."""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def skills_section():
    """The skills paragraph of the system prompt: the introduction, then the index."""
    return SKILLS_INTRO + "\n\n" + skills_prompt()


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8-sig", errors="replace")


def apply(ctx):
    """The skills extension: the read_skill tool, and the skill index in the system prompt."""
    ctx.tool(read_skill, READ_SKILL_SCHEMA, permission="allow")  # reads a file the project shipped: no prompt
    ctx.prompt_section(skills_section)  # a function: rendered when the prompt is built


if __name__ == "__main__":
    print(skills_prompt())
