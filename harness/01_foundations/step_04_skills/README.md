# Stage 4 - Skill discovery and reading

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 3 - Better UI](../step_03_better_ui/README.md). Next: [Stage 5 - File editing tools](../step_05_file_editing/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

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

## Why skills

A team has procedures: how to explain code here, how to write a
migration, how to cut a release. Pasting them all into the system prompt
costs context on every call and most of them are irrelevant to most
tasks. A skill is a procedure in a file: one line of it (name and
description) is always in the prompt, the rest is loaded when the model
decides it applies. Without skills the procedure lives in your head and
you re-type it into every prompt.

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
agent runs from - the directory you start `python` in, so run the agent
from the project root. More paths can be added here, such as `.claude`,
to target other tools' skill folders. When two directories hold a skill
with the same name, the later one wins: a project skill overrides a
personal one.

### 2. Discovery: glob, split the front matter, parse YAML

`skills.py`:

```python
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
```

`find_skills` globs `SKILL.md` under every skill directory. A regular
expression takes the block between the two `---` lines at the top of the
file (a `---` further down, in the body or in a description, is not a
fence). `yaml.safe_load` parses it, and the name and description come
out. It returns a dictionary of skills keyed by name. Each entry holds the
description and the path where the skill lives.

Discovery runs once, at import, so it runs at start-up. That is why a
broken file must not raise: an unclosed front matter is skipped, bad YAML
is skipped with a note on stderr, a file without `name:` is named after
its folder, and a numeric name becomes a string. One bad `SKILL.md` in
`~/.agents/skills` would otherwise stop every project's agent from
starting.

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
reads the file, and returns the text. An unknown name returns a sentence,
not an exception, so the model can correct itself.

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

bash:

```bash
pip install pyyaml
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python skills.py                 # see the index
python agent.py
```

PowerShell:

```powershell
pip install pyyaml
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python skills.py
python agent.py
```

Expected output:

```text
$ python skills.py
- explain-code: How to explain a piece of code to a beginner. Use when the user asks what some code does or how it works.

$ python agent.py
> explain what agent.py does

  ┌──────────────────────────────────────────────┐
  │ read_skill explain-code                      │
  │ ──────────────────────────────────────────── │
  │ ---                                          │
  │ name: explain-code                           │
  │ …                                            │
  └──────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────┐
  │ read_file agent.py                           │
  └──────────────────────────────────────────────┘

  agent

  agent.py is the harness loop ... (line 20) ...
```

The model calls `read_skill("explain-code")` first and then follows the
skill's four rules. Delete `.agents` and ask again to see the difference.

## Error handling

- A skill the model names that does not exist: `No skill named 'x'.` as the tool result.
- A `SKILL.md` with bad YAML: `skipping <path>: bad front matter (...)` on stderr at start-up; the rest load.
- A `SKILL.md` without a closing `---`: silently skipped (it has no front matter).
- Everything from stage 3 (bad tool calls, ctrl-c, dead model calls, `/exit`) is unchanged.

## Gotchas

- Skill files are instructions the model follows. A skill folder is as
  trusted as the code in the repository: review a `SKILL.md` that comes
  from someone else before running the agent with it.
- The project folder is `Path.cwd()/.agents/skills`, so the agent finds
  this stage's example only when started from this directory.
- The index is built once at start-up. Adding a skill means restarting
  the agent.

## Files

```text
step_04_skills/
├── .agents/skills/explain-code/SKILL.md   the example project skill
├── agent.py         the loop, unchanged from stage 3
├── llm.py           the system prompt carries the skills index
├── skills.py        find_skills(), skills_prompt() and read_skill()
├── tools.py         the registry gains read_skill
├── ui.py            the presentation layer, unchanged
├── test_step.py     offline tests: front matter indexed; broken files skipped; body read on demand
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## Test

`python -m pytest test_step.py` (from this directory) parses a skill from
a temp folder, checks that an unclosed front matter and bad YAML are
skipped while a `---` inside a description, a missing name and a numeric
name are handled, and reads the example project skill through the tool.

## Diff from stage 3

```bash
diff ../step_03_better_ui/tools.py tools.py
diff ../step_03_better_ui/llm.py llm.py
cat skills.py
```

## What the next step adds

Stage 5 adds `write_file` and `str_replace`, so the agent can change code.
