# 06.05 · Generate a classification harness

[Course](../../README.md) · [Theme](../README.md)

## What you will build

A wine-classification harness generated from a revised readable brief.

## Why this matters

A useful builder adapts scientific choices instead of copying regression labels into a new folder.

## Before you start

Complete [06.04: Test the generated harness’s boundaries](../step_04_test_refusal/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/06-05</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The fixed builder skill and wine data card. New task brief and workspace.

**Budget:** Two wine fits: majority baseline and balanced logistic model. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Preserve the high-level data science workflow. Change the target to quality at least 7, use grouped input duplicates, and measure balanced accuracy with class recalls. These changes arise from the task’s meaning. The builder’s own procedure can remain fixed.

**A concrete example.** The bike brief asks for a rental count; the wine brief asks whether a recorded quality score is at least 7. Reusing the workflow is sensible, but reusing the regression evaluator is not. The generated wine harness must also keep repeated input vectors in the same partition, so copying the same measurement into another split cannot make evaluation appear easier.

![A fixed builder can generate different task-specific systems. Different output does not mean the builder learned.](../../assets/diagrams/lab-06-05.png)

*Read the diagram:* A fixed builder can generate different task-specific systems. Different output does not mean the builder learned.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 06.05, Generate a classification harness, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Which parts of the bike harness can transfer unchanged?

### 1. Describe the new task

Keep the student interface readable.

```text
Write a wine HARNESS-BRIEF.md from the data card. Predeclare the binary threshold, the fixed wine-v1 split that keeps identical input vectors together, balanced accuracy, both class recalls, two-fit budget, and source attribution.
```

**Observe:** The brief makes the derived label explicit.

### 2. Generate and compare

Test actual adaptation.

```text
Use the unchanged builder to generate and run the classification harness. Fit the majority and balanced logistic candidates. Compare generated task, preprocessing, metric, and error analysis with the bike harness.
```

**Observe:** The classification report includes minority-class behavior.

## Check your result

The builder uses the classification contract. Identical feature rows do not cross partitions. The comparison explains shared workflow and changed scientific components.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Wine HARNESS-BRIEF.md | Declares the binary threshold, duplicate-group partition rule, balanced accuracy, both recalls, and two fits. |
| Generated classification package and runs | Retain the majority and balanced logistic candidates under the wine contract. |
| Transfer comparison | Names the unchanged builder version, shared workflow, and changed target, split, model, metric, and error analysis. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Ask for an ordinal wine task in a new brief without running it. Identify why the binary evaluator cannot be reused unchanged.

## If something goes wrong

If the output still uses a bike target or MAE, inspect the task-specific portion of generation. If duplicate input groups cross partitions, fix the split in a new experiment before trusting the scores. Do not choose the quality threshold after seeing class balance or candidate performance and keep calling it the same predefined task.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A fixed generator can adapt outputs to different briefs.
- Task transfer requires semantic changes, not filename changes.
- A derived label should be declared before evaluation.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Did the builder improve merely by generating the second harness?
2. Why group repeated feature rows?
3. Why report class recalls?
4. What does this demonstrate?

<details>
<summary>Hint</summary>

Separate reusable steps from task-specific meanings. Inspection, fitting, and checking transfer; what they inspect, fit, and measure can change.

</details>

<details>
<summary>Explained answers</summary>

1. No. Its procedure may be identical. The output adapted to a different input.

2. Otherwise identical inputs can appear in both training and evaluation and inflate the comparison. This check does not remove every near-duplicate.

3. Balanced accuracy summarizes them; inspecting each reveals asymmetric failures.

4. A small task-transfer example for the generated workflow, not universal generator capability.

</details>

## What's next

Check whether both generated systems run again from their saved packages and handoffs. Continue to [06.06: Recreate and compare generated harnesses](../step_06_recreate/README.md).
