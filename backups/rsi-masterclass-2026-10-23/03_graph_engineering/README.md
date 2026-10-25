# Give different cases different routes

[Course](../README.md)

**You are here:** Theme 03 of 00–11 · Dependable workflows · 6 labs. [Your place in the guided map](../COURSE-MAP.md#theme-03).

A workflow is more than a numbered list. Some actions depend on others. Some can proceed independently. Some should run only after a particular failure.

You already have a bounded improvement loop. Now place it inside a graph of dependencies, branches, and recovery paths.

![A bike-demand research project connects six learning blocks and all twelve themes: one experiment, dependable workflows, a system and builder, changes and evidence, research studio, and capstones.](../assets/illustrations/course-mindmap-v2.png)

*Follow theme numbers 00–11. The branches group concepts; they are not execution dependencies or a universal maturity ladder. The research names are selected examples. Use the theme number on each lesson to locate it here. This map describes the planned route, not completed experiments.*

[Open the illustration at full size](../assets/illustrations/course-mindmap-v2.png).

| Lab | What you will build |
|---|---|
| [03.01 · Draw the dependencies](step_01_dependencies/README.md) | An execution graph for the process you already ran. |
| [03.02 · Route different failures differently](step_02_branch/README.md) | A branch that sends invalid data to repair and valid data to modeling. |
| [03.03 · Join independent checks](step_03_join/README.md) | A join that waits for both a data-quality check and a resource check. |
| [03.04 · Put a bounded retry inside the graph](step_04_cycle/README.md) | A graph with one explicit repair cycle and a terminal failure path. |
| [03.05 · Resume only the affected work](step_05_recover/README.md) | A recovery trace that preserves valid upstream artifacts and reruns affected descendants. |
| [03.06 · Read the plan, data flow, and trace](step_06_three_views/README.md) | Three views of one run: allowed actions, artifact movement, and actual events. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

**Ready to continue when:** Trace a failure through dependencies. Recover a failed report without refitting, and identify what a changed split would invalidate.

A graph tells the agent where work goes. The next theme asks whether the objects moving through it have the right meaning.
