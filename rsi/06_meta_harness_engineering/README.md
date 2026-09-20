# Generate a harness from a brief

[Course](../README.md)

**You are here:** Theme 06 of 00–11 · A system and its builder · 6 labs. [Your place in the guided map](../COURSE-MAP.md#theme-06).

A harness organizes execution: instructions, tools, state, checks, and limits. A meta-harness generates such a system from a task description.

You have built the parts by hand through natural language. Now the agent assembles them and proves that the result runs.

![A task brief enters an unchanged meta-harness builder. It produces a separate package of skills, tools, state, checks, and limits. The package then runs a model and produces predictions and a checked report.](../assets/illustrations/meta-harness-v2.png)

*In this example the builder stays fixed. It creates a package that must then run under the brief’s limits. Files alone do not show that the package works. A checked execution provides evidence about the generated harness; it does not establish that the builder improved itself.*

[Open the illustration at full size](../assets/illustrations/meta-harness-v2.png).

<details>
<summary>Find theme 06 in the whole-course mindmap</summary>

![A bike-demand research project connects six learning blocks and all twelve themes: one experiment, dependable workflows, a system and builder, changes and evidence, research studio, and capstones.](../assets/illustrations/course-mindmap-v2.png)

*Follow theme numbers 00–11. The branches group concepts; they are not execution dependencies or a universal maturity ladder. The research names are selected examples. Use the theme number on each lesson to locate it here. This map describes the planned route, not completed experiments.*

[Open the illustration at full size](../assets/illustrations/course-mindmap-v2.png).

</details>

| Lab | What you will build |
|---|---|
| [06.01 · Describe the harness you need](step_01_write_a_brief/README.md) | A plain-language specification for a small bike-research harness. |
| [06.02 · Generate a first harness](step_02_generate/README.md) | A generated harness with a runnable entry point, checks, and readable instructions. |
| [06.03 · Inspect what the builder decided](step_03_inspect_generated/README.md) | A review that maps each important generated behavior back to the brief. |
| [06.04 · Test the generated harness’s boundaries](step_04_test_refusal/README.md) | A retained valid run and two meaningful refusals from the generated harness. |
| [06.05 · Generate a classification harness](step_05_second_task/README.md) | A wine-classification harness generated from a revised readable brief. |
| [06.06 · Recreate and compare generated harnesses](step_06_recreate/README.md) | A clean-start reproducibility report for two generated harnesses. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

**Ready to continue when:** Distinguish the brief, builder, generated harness, and actual run. Show a baseline and a refusal in the generated system.

Generating a system is distinct from improving the generator. Before recursion, separate the many meanings of “self”.
