# Give different cases different routes

[Course](../README.md)

A workflow is more than a numbered list. Some actions depend on others. Some can proceed independently. Some should run only after a particular failure.

You already have a bounded improvement loop. Now place it inside a graph of dependencies, branches, and recovery paths.

| Lab | What changes |
|---|---|
| [03.01 · Draw the dependencies](step_01_dependencies/README.md) | An execution graph for the process you already ran. |
| [03.02 · Route different failures differently](step_02_branch/README.md) | A branch that sends invalid data to repair and valid data to modeling. |
| [03.03 · Join independent checks](step_03_join/README.md) | A join that waits for both a data-quality check and a resource check. |
| [03.04 · Put a bounded retry inside the graph](step_04_cycle/README.md) | A graph with one explicit repair cycle and a terminal failure path. |
| [03.05 · Resume only the affected work](step_05_recover/README.md) | A recovery trace that preserves valid upstream artifacts and reruns affected descendants. |
| [03.06 · Read the plan, data flow, and trace](step_06_three_views/README.md) | Three views of one run: allowed actions, artifact movement, and actual events. |

Start with the first lab and follow its next link. Each lab uses a separate workspace and keeps its evidence. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

A graph tells the agent where work goes. The next theme asks whether the objects moving through it have the right meaning.
