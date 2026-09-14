# Stage 4 - Skill discovery and reading

Skills are markdown documents. They live in a known folder on disk, and
agents check that folder for `SKILL.md` files.

**What this stage adds:** the agent finds `SKILL.md` files, puts their
name and description into the system prompt, and reads the full
instructions only when a task matches. The result is a model that follows
a project's written procedure without further prompting.

```text
./.agents/skills/explain-code/SKILL.md
---                                          ← YAML front matter
name: explain-code                            → into the system prompt (index)
description: How to explain a piece of code…  → into the system prompt (index)
---
# Explaining code                             → only via read_skill, on demand
1. Read the whole file first ...
```

## Files

```text
step_04_skills/
├── .agents/skills/explain-code/SKILL.md   the example project skill
├── agent.py         the loop, unchanged from stage 3
├── llm.py           the system prompt carries the skills index
├── skills.py        find_skills(), skills_prompt() and read_skill()
├── tools.py         the registry gains read_skill
├── ui.py            the presentation layer, unchanged
├── test_step.py     offline tests: front matter indexed, body read on demand
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## The code, piece by piece

### 1. Where skills live

`skills.py`:

```python
SKILL_DIRS = [
    Path.home() / ".agents" / "skills",  # your skills
    Path.cwd() / ".agents" / "skills",   # this project's skills
]
```

The first directory is the user's home. The second is the project the
agent runs from. More paths can be added here, such as `.claude`, to
target other tools' skill folders.

### 2. Discovery: glob, split the front matter, parse YAML

`skills.py`:

```python
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
```

`find_skills` globs `SKILL.md` under every skill directory. It reads the
front matter between the two `---` lines, parses it with
`yaml.safe_load`, and extracts the name and the description. It returns
a dictionary of skills keyed by name. Each entry holds the description
and the path where the skill lives.

### 3. The index that goes into the prompt, and the tool that reads the body

`skills.py`:

```python
def skills_prompt():
    """One line per skill: the index that goes into the system prompt."""
    return "\n".join(f"- {name}: {s['description']}" for name, s in SKILLS.items())


def read_skill(name: str) -> str:
    """Open a skill and return its full instructions."""
    if name not in SKILLS:
        return f"No skill named '{name}'."
    return SKILLS[name]["path"].read_text(encoding="utf-8")
```

`python skills.py` prints the index so you can see what the model will
see. Given a skill name, `read_skill` looks up the path of that skill,
reads the file, and returns the text.

### 4. Wiring: the prompt and the registry

`llm.py`:

```python
You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
```

`tools.py`:

```python
TOOLS = {"bash": bash, "read_file": read_file, "read_skill": read_skill}
```

## Why only the front matter goes into the prompt

The front matter at the top of the file is pasted into the system prompt.
When the agent starts, it sees each skill's name and description, so it
knows to call the skill when a matching task arrives. The instructions
below the front matter are shown only when the model chooses to load the
skill. The index costs a line per skill on every call. The body costs
nothing until it is needed. A project can ship fifty skills without
spending fifty skills' worth of context.

## Run it

```bash
pip install pyyaml
python skills.py                 # see the index
python agent.py
> explain what agent.py does
```

The model calls `read_skill("explain-code")` first and then follows the
skill's four rules. Delete `.agents` and ask again to see the difference.

## Diff from stage 3

```bash
diff ../step_03_better_ui/tools.py tools.py
diff ../step_03_better_ui/llm.py llm.py
cat skills.py
```
