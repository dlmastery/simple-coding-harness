# 05.05 · Find which component makes the difference

[Course](../../README.md) · [Theme](../README.md)

## What you will build

An ablation that compares the system with and without one domain check.

## Why this matters

A successful full system does not reveal which component caused the benefit.

## Before you start

Complete [05.04: Coordinate planning, execution, and checking](../step_04_coordinate/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/05-05</code> and reports its absolute path. It checks local Python and the [tool requirements](../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** The fixed coordinator and the leaked-feature fixture used earlier.

**Budget:** No fits required. Two controlled fixture runs. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

An ablation removes one component while holding the rest as steady as possible. Here the outcome is whether an invalid proposal reaches fitting. Use a dry-run fitting stub so the ablated system cannot accidentally train a leaked model. Reliability is the measured property, not prediction quality.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 05.05, Find which component makes the difference, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Will removing the domain check change the valid case, the invalid case, or both?

### 1. Predeclare the outcome

Avoid choosing the metric after the result.

```text
Write ABLATION-PLAN.md comparing full system and system without the domain check. Use the same valid and leaked-feature fixtures. Measure whether each reaches the fit stub.
```

**Observe:** The test targets the check’s specific job.

### 2. Run both versions

Measure the component’s contribution.

```text
Execute both systems on both fixtures. Preserve the versions and outcomes. Explain any overlapping protection from another component rather than forcing the expected result.
```

**Observe:** Redundant checks may hide the effect of removing one component.

## Check your result

Only one component differs. The report accounts for redundant checks and does not claim a predictive-performance gain.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Remove both overlapping checks in a separate declared ablation. Explain why this answers a different causal question.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Ablation tests dependence on a component.
- Redundancy can make one removal appear harmless.
- The outcome must match the component’s purpose.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. Why use a fit stub?
2. Does no effect prove the component useless?
3. Why not remove several components at once first?
4. Can this establish language-model improvement?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. It records whether execution would proceed without training on an intentionally invalid fixture.

2. No. Another component may provide the same protection or the test may miss relevant cases.

3. That makes their individual contributions harder to separate.

4. No. It measures a system-level reliability mechanism with fixed model weights.

</details>

## What's next

You can describe a useful harness. Ask a builder to generate one from a task brief. Continue to [06.01: Describe the harness you need](../../06_meta_harness_engineering/step_01_write_a_brief/README.md).
