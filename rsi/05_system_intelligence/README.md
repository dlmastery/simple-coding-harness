# Build capability around the model

[Course](../README.md)

A useful research system combines a model with tools, state, checks, and domain knowledge. In this course, “system intelligence” means the capability of that combination.

This is a course term, not an accepted RSI level. Keep the components fixed while studying how their coordination changes results.

| Lab | What changes |
|---|---|
| [05.01 · Combine fixed components into a useful system](step_01_combine_components/README.md) | A fixed research workflow that uses a task skill, an ML tool, domain checks, and a report checker. |
| [05.02 · Choose a skill for the task](step_02_route_tasks/README.md) | A router that sends bike regression and wine classification to suitable fixed procedures. |
| [05.03 · Retrieve what matters and retain task state](step_03_context_and_state/README.md) | A context packet that separates task rules, relevant knowledge, and current execution state. |
| [05.04 · Coordinate planning, execution, and checking](step_04_coordinate/README.md) | A coordinator that advances work only when the required artifacts and checks are present. |
| [05.05 · Find which component makes the difference](step_05_ablate_system/README.md) | An ablation that compares the system with and without one domain check. |

Start with the first lab and follow its next link. Each lab uses a separate workspace and keeps its evidence. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

Once you can describe a useful system, you can ask another procedure to build it from a brief.
