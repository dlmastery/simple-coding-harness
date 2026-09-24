# Start with a prediction

[Course](../README.md)

**You are here:** Theme 00 of 00–11 · One experiment · 4 labs. [Your place in the guided map](../COURSE-MAP.md#theme-00).

A bike service wants an estimate of hourly demand. Before building an improving agent, learn to tell an executed prediction from a convincing description.

You need basic familiarity with tables and prediction error. You do not need RSI, agent, or infrastructure experience.

![Calendar and observed weather enter the model. Casual and registered counts add to total rentals, so their shortcut into features is blocked. Prediction and observation meet at the error check.](../assets/illustrations/target-leakage-v2.png)

*The component counts already reveal the answer: casual + registered = total rentals. Keep them out of the input features. The checker still needs the observed total to measure error. This course uses observed weather for a retrospective teaching task; it does not assume that weather was known a day ahead.*

[Open the illustration at full size](../assets/illustrations/target-leakage-v2.png).

<details>
<summary>Find theme 00 in the whole-course mindmap</summary>

![A bike-demand research project connects six learning blocks and all twelve themes: one experiment, dependable workflows, a system and builder, changes and evidence, research studio, and capstones.](../assets/illustrations/course-mindmap-v2.png)

*Follow theme numbers 00–11. The branches group concepts; they are not execution dependencies or a universal maturity ladder. The research names are selected examples. Use the theme number on each lesson to locate it here. This map describes the planned route, not completed experiments.*

[Open the illustration at full size](../assets/illustrations/course-mindmap-v2.png).

</details>

| Lab | What you will build |
|---|---|
| [00.01 · Meet the prediction task](step_01_meet_the_task/README.md) | A task brief that says what one prediction means and which inputs are available. |
| [00.02 · Prepare a workspace you can inspect](step_02_prepare_the_workspace/README.md) | A separate learner workspace, a capability report, and a verified data report. |
| [00.03 · Run one baseline](step_03_one_attempt/README.md) | A real constant-prediction baseline with a measured error and saved predictions. |
| [00.04 · Check the evidence behind the answer](step_04_check_the_evidence/README.md) | A short evidence report that ties a claim to predictions, data roles, and a reproducible calculation. |

Start with the first lab and follow its next link. Each lab keeps its notes in a separate workspace and links any earlier experiment it reuses. The agent writes code; you predict, inspect, and explain. [Skill entry point](../skills/rsi-tutor/SKILL.md).

**Ready to continue when:** Explain one prediction: its target, permitted inputs, partition, and checked error. Identify a feature that would leak the answer.

The next theme turns these checked actions into a repeatable process.
