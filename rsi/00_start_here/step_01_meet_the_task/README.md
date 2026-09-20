# 00.01 · Meet the prediction task

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 00, One experiment → lab 1 of 4. [Find this theme in the course map](../../COURSE-MAP.md#theme-00) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A task brief that says what one prediction means and which inputs are available.

## Why this matters

An agent can optimize the wrong task very efficiently. First make the question concrete.

## Before you start

Complete [Start here](../../START-HERE.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/00-01</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The supplied Bike Sharing data card and the first eight hourly records. No earlier run is needed.

**Budget:** No model fits. Inspect eight rows and write one short brief. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

One row describes one recorded hour. The target, cnt, is the number of rentals. Calendar and observed weather fields describe the situation. A prediction is an estimate of cnt before looking at its value. We score it with mean absolute error (MAE): the average size of the prediction errors, ignoring their signs. The information setting matters: using observed weather makes this a retrospective exercise, not proof of a day-ahead forecast.

**A concrete example.** Consider an illustrative hour with 3 casual rentals and 13 registered rentals. The total is 16. Adding those two observed counts gives the answer exactly, but the counts are not available before those rentals occur. The useful question is what you could have predicted from permitted information. Now change the request from describing a recorded hour to planning tomorrow: even the weather input needs a different source.

![Calendar and observed weather enter the model. Casual and registered counts add to total rentals, so their shortcut into features is blocked. Prediction and observation meet at the error check.](../../assets/illustrations/target-leakage-v2.png)

*The component counts already reveal the answer: casual + registered = total rentals. Keep them out of the input features. The checker still needs the observed total to measure error. This course uses observed weather for a retrospective teaching task; it does not assume that weather was known a day ahead.*

[Open the illustration at full size](../../assets/illustrations/target-leakage-v2.png).

<details>
<summary>See the step diagram</summary>

![Predict the hourly total from allowed inputs. The two component counts already contain the answer.](../../assets/diagrams/lab-00-01.png)

*Read the diagram:* Predict the hourly total from allowed inputs. The two component counts already contain the answer.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 00.01, Meet the
prediction task, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Would knowing casual and registered rentals make the target easy to predict? Would those counts be available for the intended decision?

### 1. Inspect one hour

Start with a row you can understand.

```text
Read the bike data card. Show me eight
source rows as a small readable table.
Explain cnt, hr, temp, casual, and
registered using the original data
description. Do not fit a model.
```

**Observe:** The counts describe related quantities. Ask which are inputs and which are outcomes.

### 2. Write the brief

Make the prediction setting explicit.

```text
Write TASK.md in my lab workspace:
prediction unit, target, available inputs,
excluded fields, MAE, chronological
partitions, and one limitation. Explain why
observed weather does not establish an
advance forecast.
```

**Observe:** A reader can tell exactly what would count as a valid prediction.

## Check your result

TASK.md excludes casual and registered from prediction inputs. It states rentals per hour as the target unit and distinguishes observed weather from a forecast.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| TASK.md | States one row, the target and unit, when inputs are available, excluded outcome fields, the metric, and the partition rule. |
| Eight-row display | Shows source rows that support the field explanations. This is data inspection, not a model result. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Change the request to “predict tomorrow at noon.” Before training anything, list which inputs would now be unknown. Save the changed brief as a separate task.

## If something goes wrong

If the agent treats casual or registered as ordinary inputs, return to one row and add the counts. Correct the brief before fitting anything. If it calls observed weather a forecast, ask when that weather value would have been known. A missing forecast source is a task-design gap, not a reason to invent forecast accuracy.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A task includes when its inputs become available.
- An easy-to-predict target can still be the wrong decision problem.
- Changing the prediction setting can require new data and a new evaluation.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What is one prediction in this task?
2. Why exclude the two component counts?
3. Does a low error with observed weather prove a good day-ahead forecast?
4. What should change when the business question changes?

<details>
<summary>Hint</summary>

Place yourself just before the prediction is needed. Which values could you actually know then? A column can be present in a historical table and still be unavailable at that moment.

</details>

<details>
<summary>Explained answers</summary>

1. An estimated rental count for one recorded hour, under the stated input-availability rules.

2. Their sum is the target. Using them would answer the question with information contained in the outcome.

3. No. That forecast must use weather information available at its forecast origin.

4. The brief and evaluation record. Quietly changing inputs inside the same comparison would mix different tasks.

</details>

## What's next

The task is clear. Now check whether your coding agent can actually execute it. Continue to [00.02: Prepare a workspace you can inspect](../step_02_prepare_the_workspace/README.md).
