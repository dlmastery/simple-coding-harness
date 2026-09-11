# Stage 4 - Skill discovery and reading (video 18:31 - 25:02)

> "Skills are just markdown documents. They can be placed in a special
> folder on your disk and all of your agents know to check these specific
> directories to find the SKILL.md file."

New file `skills.py`; `tools.py` gains `read_skill`; the system prompt in
`llm.py` gains the skills index.

```
~/.agents/skills/<name>/SKILL.md      your skills
./.agents/skills/<name>/SKILL.md      this project's skills

---                      ← YAML front matter: pasted into the system prompt
name: explain-code
description: How to explain ...
---
(the instructions)       ← shown only when the agent calls read_skill
```

## How it works, in the video's words

- `find_skills` "globs the skill.md in these skill dirs, reads the front
  matter separated by those three dashes, does a yaml.safe_load, and
  extracts its description and its name".
- `skills_prompt` "loops over all of the skills we found and joins them to
  create a long name-and-description object". Run `python skills.py` to
  see it.
- `read_skill` "given a skill name, looks up the path of that skill and
  reads it in and sends it back".

Only the index costs context on every call. The body costs nothing until a
task matches. "It's so powerful that it's almost hilarious that it just
works."

## Run it

```bash
python agent.py
> explain what agent.py does
```

The prompt tells the model `explain-code` exists; it calls `read_skill`
first, then follows the four rules in the skill.

## Diff from stage 3

```bash
diff ../step_03_better_ui/tools.py tools.py
diff ../step_03_better_ui/llm.py llm.py
cat skills.py
```
