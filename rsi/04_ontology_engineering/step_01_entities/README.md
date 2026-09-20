# 04.01 · Name the objects in an experiment

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A small vocabulary for data, columns, targets, partitions, models, metrics, and evidence.

## Why this matters

“Improve the model” is ambiguous if one speaker means fitted parameters and another means the whole agent system.

## Before you start

Complete [03.06: Read the plan, data flow, and trace](../../03_graph_engineering/step_06_three_views/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/04-01</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** One baseline report, its task brief, and prediction file.

**Budget:** No fits. Classify ten objects from the existing run. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

An entity is an object you need to distinguish. A type states what kind of object it is. The bike table is a dataset; cnt is a column playing the target role; MAE is a metric; 159.948 is a measured value for a particular candidate and partition. Keeping these separate prevents category mistakes.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 04.01, Name the objects in an experiment, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Are “MAE” and “159.948 rentals per hour” the same kind of thing?

### 1. Build the vocabulary

Ground each term in an actual artifact.

```text
Use review-domain. Create VOCABULARY.md with object, type, plain-language definition, and example from the baseline. Include dataset, column, target role, partition, fitted model, recipe, metric, and measurement.
```

**Observe:** The vocabulary distinguishes a rule from its result.

### 2. Classify a confusing case

Test whether definitions help.

```text
Classify the phrase “the model improved” in three cases: lower selection error, edited research skill, and changed language-model weights. Rewrite each claim precisely.
```

**Observe:** Different mutable objects receive different names.

## Check your result

Definitions include concrete examples and do not equate a recipe with a fitted model or a metric with its measured value.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Replace every use of “score” with its precise metric, candidate, partition, and unit. Notice which missing context becomes visible.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Shared names reduce ambiguous instructions.
- A role can differ from an object’s type.
- A measured value needs context to be meaningful.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Is cnt inherently the target in every possible task?
2. Is a metric the same as a measurement?
3. What differs between a recipe and a fitted model?
4. Does a vocabulary alone enforce correctness?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. No. It is a column assigned the target role in this task.

2. No. MAE is a calculation rule; its value comes from specific predictions and actual outcomes.

3. The recipe specifies how to fit; the fitted model contains parameters learned from particular training data.

4. No. Relations and executable checks are needed to test important claims.

</details>

## What's next

Connect these objects with relations that express the experiment’s meaning. Continue to [04.02: Connect data, models, and evidence](../step_02_relations/README.md).
