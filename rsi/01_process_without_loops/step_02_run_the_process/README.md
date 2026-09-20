# 01.02 · Run the process without changing it

[Course](../../README.md) · [Theme](../README.md)

**You are here:** Theme 01, One experiment → lab 2 of 5. [Find this theme in the course map](../../COURSE-MAP.md#theme-01) · [Whole-course mindmap](../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A clean-start execution trace for the fixed bike baseline process.

## Why this matters

A written sequence may omit setup or depend on forgotten state. A fresh run exposes those gaps.

## Before you start

Complete [01.01: Write the data science process](../step_01_describe_the_process/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/01-02</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** PROCESS.md from 01.01 and a new empty lab workspace.

**Budget:** One constant-model fit and one data inspection. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

Reproducibility begins with a fixed recipe and known inputs. Record versions and hashes, then execute the same actions. A trace says what actually happened. It can differ from the intended process if a command fails or an assumption is missing.

**A concrete example.** Two runs can produce byte-identical predictions while taking different wall-clock times. The recipe is repeatable; the operating system did not schedule both commands identically. Conversely, matching rounded MAE values can hide different predictions. Compare rows and settings before deciding what repeated.

![The process becomes evidence only when its actions run and their outputs are retained.](../../assets/diagrams/lab-01-02.png)

*Read the diagram:* The process becomes evidence only when its actions run and their outputs are retained.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 01.02, Run the process
without changing it, one step at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Should this run reproduce the earlier baseline score? Which differences would be harmless?

### 1. Execute the sequence

Test whether the written process is sufficient.

```text
Follow PROCESS.md from a clean workspace.
Use pinned data and the constant bike model.
Record each action, input artifact, output
artifact, exit status, and elapsed time in
TRACE.md. Do not improve the recipe.
```

**Observe:** The same data and recipe give the same metric within numerical tolerance.

### 2. Compare the runs

Separate reproducibility from performance improvement.

```text
Compare the new and old baseline settings,
row identities, predictions, score, and
runtime. Save REPEATABILITY.md. Explain any
difference instead of replacing it.
```

**Observe:** Wall time may differ even when predictions match.

## Check your result

The trace contains all five actions. The score recomputes from the new predictions. Any version difference is visible.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| TRACE.md | Records all five process actions, their inputs and outputs, exit status, and elapsed time. |
| New baseline artifacts | Belong to this clean workspace; they are not copied predictions presented as a new fit. |
| REPEATABILITY.md | Compares recipe, source, row identities, predictions, score, and runtime with the earlier run. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Remove an output report from a copy of the new workspace. Have the agent distinguish a missing artifact from an unexecuted model fit.

## If something goes wrong

If a report is missing, check the ledger and prediction file before retraining. If predictions differ, compare versions, feature groups, and split identities. Preserve the difference and identify its cause; replacing the new output with the old one would erase the observation this lab needs.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A fresh run tests hidden dependencies.
- A trace records events; a process specifies intended events.
- Repeatability is not evidence that the method improved.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. If the same recipe runs twice, did it learn?
2. Must wall-clock time match exactly?
3. Why keep the new predictions?
4. Does a missing report prove no training occurred?

<details>
<summary>Hint</summary>

Separate the intended recipe, the events in this run, and the result. Which of those should remain the same, and which can vary without changing the prediction?

</details>

<details>
<summary>Explained answers</summary>

1. Not necessarily. Reusing fixed instructions changes no retained method.

2. No. Scheduling and startup vary. State the measured scope and environment.

3. They allow comparison of the executed output, not only the reported metric.

4. No. Inspect the ledger and predictions; reporting may have failed after training.

</details>

## What's next

Package the process so another session can use it. Continue to [01.03: Turn the process into a skill](../step_03_make_a_skill/README.md).
