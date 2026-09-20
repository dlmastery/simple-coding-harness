# Generate a harness from a brief

[Course](../README.md)

A harness organizes execution: instructions, tools, state, checks, and limits. A meta-harness generates such a system from a task description.

You have built the parts by hand through natural language. Now the agent assembles them and proves that the result runs.

| Lab | What changes |
|---|---|
| [06.01 · Describe the harness you need](step_01_write_a_brief/README.md) | A plain-language specification for a small bike-research harness. |
| [06.02 · Generate a first harness](step_02_generate/README.md) | A generated harness with a runnable entry point, checks, and readable instructions. |
| [06.03 · Inspect what the builder decided](step_03_inspect_generated/README.md) | A review that maps each important generated behavior back to the brief. |
| [06.04 · Test the generated harness’s boundaries](step_04_test_refusal/README.md) | A retained valid run and two meaningful refusals from the generated harness. |
| [06.05 · Generate a classification harness](step_05_second_task/README.md) | A wine-classification harness generated from a revised readable brief. |
| [06.06 · Recreate and compare generated harnesses](step_06_recreate/README.md) | A clean-start reproducibility report for two generated harnesses. |

Start with the first lab and follow its next link. Each lab uses a separate workspace and keeps its evidence. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

Generating a system is distinct from improving the generator. Before recursion, separate the many meanings of “self”.
