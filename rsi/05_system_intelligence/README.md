# Build capability around the model

[Course](../README.md)

A useful research system combines a model with tools, state, checks, and domain knowledge. In this course, “system intelligence” means the capability of that combination.

This is a course term, not an accepted RSI level. Keep the components fixed while studying how their coordination changes results.

![Numbered steps read ready, save running, and fit candidate C1. Saved awaiting-check state survives a process exit. A new process checks C1; a C2 report, missing check, or unclear target cannot complete the task.](../assets/illustrations/system-coordination-v3.png)

*Read steps 1, 2, and 3 in order: starting the fit requires running to be saved first. Matching C1 labels connect the scenes across the process boundary. The checkmarks illustrate a possible accepted handoff, not a new measured run. A missing check leaves work pending; a wrong candidate is refused. The coordinator remains fixed. Its read-only label describes the procedure, not an independently enforced permission boundary.*

[Open the illustration at full size](../assets/illustrations/system-coordination-v3.png).

| Lab | What you will build |
|---|---|
| [05.01 · Combine fixed components into a useful system](step_01_combine_components/README.md) | A fixed research workflow that uses a task skill, an ML tool, domain checks, and a report checker. |
| [05.02 · Choose a skill for the task](step_02_route_tasks/README.md) | A router that sends bike regression and wine classification to suitable fixed procedures. |
| [05.03 · Retrieve what matters and retain task state](step_03_context_and_state/README.md) | A context packet that separates task rules, relevant knowledge, and current execution state. |
| [05.04 · Coordinate planning, execution, and checking](step_04_coordinate/README.md) | A coordinator that advances work only when the required artifacts and checks are present. |
| [05.05 · Find which component makes the difference](step_05_ablate_system/README.md) | An ablation that compares the system with and without one domain check. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

Once you can describe a useful system, you can ask another procedure to build it from a brief.
