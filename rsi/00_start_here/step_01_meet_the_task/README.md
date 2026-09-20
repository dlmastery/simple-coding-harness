# 00.01 · Meet the prediction task

[Course](../../README.md) · [Theme](../README.md)

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



![Predict the hourly total from allowed inputs. The two component counts already contain the answer.](../../assets/diagrams/lab-00-01.png)

*Read the diagram:* Predict the hourly total from allowed inputs. The two component counts already contain the answer.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 00.01, Meet the prediction task, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Would knowing casual and registered rentals make the target easy to predict? Would those counts be available for the intended decision?

### 1. Inspect one hour

Start with a row you can understand.

```text
Read the bike data card. Show me eight source rows as a small readable table. Explain cnt, hr, temp, casual, and registered using the original data description. Do not fit a model.
```

**Observe:** The counts describe related quantities. Ask which are inputs and which are outcomes.

### 2. Write the brief

Make the prediction setting explicit.

```text
Write TASK.md in my lab workspace: prediction unit, target, available inputs, excluded fields, MAE, chronological partitions, and one limitation. Explain why observed weather does not establish an advance forecast.
```

**Observe:** A reader can tell exactly what would count as a valid prediction.

## Check your result

TASK.md excludes casual and registered from prediction inputs. It states rentals per hour as the target unit and distinguishes observed weather from a forecast.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Change the request to “predict tomorrow at noon.” Before training anything, list which inputs would now be unknown. Save the changed brief as a separate task.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

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

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

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
