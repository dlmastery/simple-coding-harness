# Improve the improvement procedure

[Course](../README.md)

The solver proposes ML experiments. The improver revises the solver’s research skill. Recursion enters when an improvement procedure is itself revised and that revision governs later improvement work.

Track three separate objects: task solver, improver, and evaluator. Keep claims of structure, effectiveness, and acceleration separate.

| Lab | What you will build |
|---|---|
| [09.01 · Identify the solver, improver, and evaluator](step_01_three_objects/README.md) | A map of three distinct components and the changes each may make. |
| [09.02 · Run repeated improvement with an unchanged improver](step_02_fixed_improver/README.md) | Two generations of task-skill revision governed by one fixed improver. |
| [09.03 · Propose a change to the improver](step_03_revise_improver/README.md) | A child improver that changes how future task-skill revisions are chosen or tested. |
| [09.04 · Use the revised improver in the next round](step_04_inherit/README.md) | An inheritance trace from a changed improver to a later task-skill proposal and decision. |
| [09.05 · Measure whether the revised improver helps](step_05_compare_improvers/README.md) | A matched comparison of improvements produced by two improver versions. |
| [09.06 · Run bounded recursive generations](step_06_bounded_generations/README.md) | A two-generation recursive lineage with promotion, rejection, checkpoint, and stop records. |
| [09.07 · State the result without overstating it](step_07_claim/README.md) | A final claim audit separating structural recursion, effective improvement, and acceleration. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

A bounded recursive experiment is now inspectable. The research studio shows how current systems combine these mechanisms and where their evidence ends.
