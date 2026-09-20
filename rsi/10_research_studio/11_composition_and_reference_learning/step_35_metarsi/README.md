# 10.35 · Compose changes to data, harness, and model

[Course](../../../README.md) · [Theme](../../README.md)

## What you will build

A typed operator schedule and a labelled simulation of revising that schedule.

## Why this matters

A failure does not automatically reveal whether it needs better data, a harness change, or model training.

## Before you start

Complete [10.34: Keep model training aligned with its harness](../../10_feedback_and_transfer/step_34_model_harness_fit/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent creates a separate sibling workspace named <code>rsi-work/10-35</code> and reports its absolute path. It checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Your ontology and three labelled operator stubs: data, harness, model. No actual LLM training.

**Budget:** Five small schedule checks and one inherited scheduler revision in a simulation. Plan about 20–35 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

MetaRSI composes operators over data, harness, and model state, with a policy that chooses their order and can itself be revised. The classroom simulation makes write boundaries and input versions explicit. A changed system can make old diagnostic evidence stale. Keep the external evaluator fixed.



## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.35, Compose changes to data, harness, and model, one step at a time.
Read its README and BRIEF. Prepare its separate workspace.
You write and run the implementation. Keep the reports and failures.
Ask me to predict the result before the experiment.
```

**Make a prediction:** Could the same two operators give different results when applied in the opposite order?

### 1. Define typed operators

Make each mutable surface visible.

```text
Generate a small simulator with separate data, harness, and model version fields. Give each operator a declared read/write contract and a synthetic outcome rule. Reject stale evidence and undeclared writes. Label every value synthetic.
```

**Observe:** Composition is checked through interfaces and versions.

### 2. Revise the schedule

Trace a meta-level change into later work.

```text
Compare two allowed schedules, propose one scheduler-rule revision from their outcomes, and use it in a later simulated term. Preserve the original scheduler and fixed evaluator. Audit structure separately from synthetic benefit.
```

**Observe:** The revised scheduling rule is actually inherited.

## Check your result

The simulator enforces declared surfaces and evidence versions. Synthetic outcomes are not presented as the paper’s results. The audit distinguishes schedule composition from real model training.

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Read the paper’s same-start improver comparison and per-term gains. Explain why rising cumulative gains can coexist with declining gains per term.

## If something goes wrong

If the expected artifact is missing, inspect the last command and its exit status before running again. If a check fails, preserve the failing result and diagnose that check; do not weaken it to obtain a pass.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- Operator order can matter.
- Versioned evidence can become stale after a change.
- Cumulative progress does not imply an increasing progress rate.

## Research connection

[MetaRSI / RSI2](https://arxiv.org/abs/2609.06396), Zihan Tan and colleagues; first submitted 6 September 2026, revised 9 September.

This is a classroom mechanism exercise. Its task, models, and budget differ from the original study. Your measured result belongs to this exercise; it does not reproduce the paper’s headline result.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What are the three surfaces?
2. Why keep the evaluator outside them?
3. What supports structural recursion in the simulation?
4. Does increasing cumulative gain prove acceleration?

<details>
<summary>Hint</summary>

Trace what changed, what stayed fixed, and which observation supports the conclusion. A filename or a confident explanation is not enough evidence.

</details>

<details>
<summary>Explained answers</summary>

1. Data state, harness state, and model state; the toy represents them without training an LLM.

2. Otherwise an operator could improve the apparent result by changing the measurement.

3. An altered scheduling policy governs a later improvement term.

4. No. Smaller positive increments still increase the total while the rate declines.

</details>

## What's next

Use reference trajectories carefully, without leaking their answers into active skills. Continue to [10.36: Diagnose failures with checked reference trajectories](../step_36_harnessevolve/README.md).
