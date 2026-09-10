# Step 6 - Skills

**New in this step:** the agent discovers `SKILL.md` files, lists them in its
system prompt, and opens one with `read_skill` when a task matches.

```
.agents/skills/
└── explain-code/
    └── SKILL.md      ← frontmatter (name, description) + instructions
```

## The idea: progressive disclosure

A skill is a recipe: "when asked to do X, here is how this project does it."
You could paste every recipe into the system prompt, but a project with
forty of them would spend most of its context window on instructions that
do not apply to the current task.

So the system prompt gets only the *index* - one line per skill, name and
description - and the body is fetched on demand through a tool:

| Where | What the model sees | Cost |
|-------|---------------------|------|
| system prompt | `- explain-code: How to explain a piece of code...` | ~20 tokens |
| after `read_skill("explain-code")` | the full instructions | only when needed |

This is the same pattern Claude Code, Codex and Cursor use for their skill
and rules directories. The mechanism is nothing more than a glob, a YAML
parse and one tool.

## Two search paths

`skills.py` looks in `./.agents/skills` (project) and `~/.agents/skills`
(personal). Project skills win on a name clash. Both directories follow the
open agent-skills convention, so skills written for other tools drop in
unchanged.

## Run it

```bash
python -m harness
you> explain what harness/agent.py does
```

The system prompt tells the model a skill exists; it should call
`read_skill` before answering, and then follow the four rules in the skill.
Try deleting the `.agents` folder and asking again to see the difference.

## Diff from step 5

```bash
diff -r ../step_05_terminal_ui/harness harness
```

New file: `harness/skills.py`. Changed: `prompts.py` (index in the prompt),
`tools.py` (one registry line).
