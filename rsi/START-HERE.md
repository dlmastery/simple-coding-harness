# Start here

[Course](README.md)

Your first goal is small: understand one bike-demand prediction and inspect one result that actually ran. You do not need to build an autonomous system today.

Want to see the route before you begin? Open the [illustrated course map](COURSE-MAP.md),
[all 101 lab illustrations](VISUAL-GUIDE.md), or the [presentation and speaker notes](PRESENTATION.md).
The [teaching roadmap](TEACHING-ROADMAP.md) helps you choose a course length.

## Open the project

Open this repository in a coding agent with local file and command access. If it is not on your computer, ask the agent to clone `https://github.com/dlmastery/simple-coding-harness` into a new local folder. During this rebuild, use branch `codex/rsi-masterclass-rebuild`. Have the agent report the branch and commit it opened.

Work from the repository root, the folder containing `rsi`. Paste:

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Start lab 00.01 with me. Explain the bike prediction task before running code.
You write and run the implementation. I will predict, inspect, and explain.
Guide me one step at a time and wait at the learning checkpoints.
Keep my generated work in a sibling rsi-work folder. Report its absolute path.
```

The agent should open [Meet the prediction task](00_start_here/step_01_meet_the_task/README.md), explain a few rows, and ask for your prediction. It should not race through the course or reveal all quiz answers.

## Know what to expect

The next lab checks Python, dependencies, command execution, and plots. The agent handles setup. If a required capability is missing, it should name the exact gap. A text-only explanation cannot complete an execution requirement.

Use these prompts whenever needed:

```text
Explain this with one concrete example, then connect it to the experiment.
```

```text
Show me the actual output file and the check that supports this claim.
```

```text
Give me a hint without revealing the quiz answer.
```

```text
Stop this lab. Save what completed, what failed, the remaining budget, and the next action.
```

To return later, ask the agent to read the lab README and your `PROGRESS.md`. To start over, ask for a new sibling workspace. Keep earlier attempts; they are part of the evidence.

Begin with [00.01 · Meet the prediction task](00_start_here/step_01_meet_the_task/README.md).
