# Make one process dependable

[Course](../README.md)

You can inspect an agent’s output. Now make the actions behind it explicit and repeatable. Run a simple data science process once, then package it as a skill.

The process stays fixed. “No loops” means no learner-designed search or revision loop. The coding agent and numerical libraries can still have internal iterations.

![Five actions frame hourly bike demand, inspect data, define chronological train/selection/final partitions, fit a training-median baseline, and compare selection predictions with targets.](../assets/illustrations/data-science-process-v4.png)

*Follow the numbered actions once. Train supplies the fitted median; the matching Selection labels identify the rows used for checking. Final stays reserved. The inspection checkmarks name work to complete, not proof about your run. Observed weather makes this a retrospective task, and the public data are not access-controlled. A checked baseline is the starting evidence for later improvement.*

[Open the illustration at full size](../assets/illustrations/data-science-process-v4.png).

| Lab | What you will build |
|---|---|
| [01.01 · Write the data science process](step_01_describe_the_process/README.md) | A five-action process from task framing to a checked baseline report. |
| [01.02 · Run the process without changing it](step_02_run_the_process/README.md) | A clean-start execution trace for the fixed bike baseline process. |
| [01.03 · Turn the process into a skill](step_03_make_a_skill/README.md) | A short Markdown skill that runs the fixed baseline process. |
| [01.04 · Check outputs with a separate calculation](step_04_separate_the_check/README.md) | An output checker that derives error from prediction rows and rejects a mismatch. |
| [01.05 · Reuse the skill in a fresh session](step_05_reuse_the_skill/README.md) | A handoff that another session can execute from files alone. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

A repeatable process gives you a useful starting point. The next theme asks what to do when that process produces a weak result.
