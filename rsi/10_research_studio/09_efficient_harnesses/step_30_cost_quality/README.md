# 10.30 · Reduce cost without hiding quality loss

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A quality-and-cost comparison of two small harness variants.

## Why this matters

A shorter trace is useful only if it still performs the required work reliably.

## Before you start

Complete [10.29: Repair a skill for an experiment-results page](../../08_skills_and_procedures/step_29_gui/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-30</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** A baseline harness, two task fixtures, and a predeclared quality tolerance.

**Budget:** Two variants, at most two fits each. Include proposal and checking overhead. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

SoL-Pi motivates harness search for efficiency subject to quality requirements. Our exercise removes redundant report work, then checks whether the retained evidence remains complete. Define acceptable quality before comparing cost. Lower token use alone does not establish recursive cost compounding.

![A cheaper harness is eligible only if it still meets the declared quality requirement.](../../../assets/diagrams/lab-10-30.png)

*Read the diagram:* A cheaper harness is eligible only if it still meets the declared quality requirement.

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.30, Reduce cost without hiding quality loss, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Which report step can be removed without losing evidence needed for acceptance?

### 1. Set the acceptance rule

Prevent cost savings from weakening the task.

```text
Write QUALITY-COST.md with required evidence, allowed quality tolerance, failure handling, and measured cost fields. Propose one removal of redundant work.
```

**Observe:** The quality floor precedes the optimization.

### 2. Compare variants

Count the work needed to obtain each result.

```text
Run baseline and candidate on matched fixtures or tasks. Compare quality, missing evidence, tool calls, wall time, and available agent usage. Include the cost of proposing and evaluating the change.
```

**Observe:** A cheaper invalid result is rejected.

## Check your result

The acceptance rule is unchanged. All relevant costs are included or marked unknown. The conclusion is limited to measured efficiency.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Run the same comparison after removing a necessary checker in a labelled fixture. Explain why the apparent saving is not a valid win.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Efficiency is conditional on a quality requirement.
- Search overhead belongs in the cost.
- One cheaper harness does not prove compounding RSI.

## Research connection

[SoL-Pi](https://arxiv.org/abs/2609.20519), 17 September 2026.

**Activity type: mechanism exercise.** You execute a small classroom mechanism. Its task, models, and budget differ from the source. Local observations do not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why predeclare tolerance?
2. Does fewer tokens always mean less total cost?
3. What should happen to missing evidence?
4. What would demonstrate recursive cost compounding?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Otherwise a quality loss can be excused after seeing a cost reduction.

2. No. More tool work, retries, or failures can offset the saving.

3. Treat it under the acceptance rule, not as a free speedup.

4. Inherited improvements to the cost-improvement process with repeated measured downstream benefits.

</details>

## What's next

Audit systems that generate and improve harness infrastructure. Continue to [10.31: Compare harness generation and harness improvement](../step_31_harness_builders/README.md).
